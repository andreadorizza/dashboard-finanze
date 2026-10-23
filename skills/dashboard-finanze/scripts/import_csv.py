"""Turn a bank or card CSV into ledger entries.

Usage:
  python3 import_csv.py FILE --account Assets:Giulia:Fineco [--currency EUR]
      [--rules rules.csv] [--ledger main.beancount ...] [--since YYYY-MM-DD]
      [--until YYYY-MM-DD] [--close YYYY-MM-DD=AMOUNT ...] [--decimal-comma] [--card]
      [--unknown-out Expenses:Uncategorized] [--unknown-in Income:{owner}:Other]

Columns (header names are matched ignoring case, spaces and brackets; the first present wins).
If the bank's file looks different, write a normalised CSV with these four first:
  date         date, data, data operazione, data contabile, booking date, started date, completed date
  amount       amount, importo  (signed: money in +, money out -)
               or two columns: in/out, entrate/uscite, avere/dare, credit/debit
  description  description, descrizione, causale, payee, beneficiario, reference, dettagli
  balance      balance, saldo  (optional: running balance after the row)
  id           id, transaction id  (optional: the bank's own id, used for dedup)

What it does
  - one transaction per row, dated at the booking date, in the account's currency
  - the other leg comes from rules.csv; rows no rule matches get the ! flag
  - IBANs, card numbers and long reference numbers are removed from descriptions
  - rows already in the ledger (same ref) are skipped, so re-importing is safe
  - with a balance column: checks every row follows from the previous one and writes a
    `balance` assertion after each month; otherwise pass the statement's closing
    balance with --close (asserted on the next day: Beancount checks at start of day)
  --until: the last day the statement covers (e.g. 2026-09-30), even if the last movement
    is earlier, so the dashboard knows the month is complete. Always pass it.
  --card: the file is a credit-card statement where spending is positive; flip signs.
  It stops with an error if it can't find a date or an amount column: it never guesses.
"""
import argparse
import csv
import sys
from collections import Counter
from datetime import timedelta
from decimal import Decimal

sys.path.insert(0, __file__.rsplit("/", 1)[0])
from common import (categorise, entry, find_column, known_balances, known_refs, load_rules,  # noqa: E402
                    make_ref, owner_of, parse_amount, parse_date, pick, scrub)

DATE = ["date", "data", "data operazione", "data contabile", "data valuta", "booking date",
        "completed date", "started date", "value date", "datum"]
AMOUNT = ["amount", "importo", "amount eur", "importo eur", "importo euro", "betrag", "valore"]
IN = ["in", "entrate", "avere", "credit", "accrediti"]
OUT = ["out", "uscite", "dare", "debit", "addebiti"]
DESC = ["description", "descrizione", "causale", "descrizione operazione", "payee", "beneficiario",
        "partner name", "reference", "payment reference", "dettagli", "merchant"]
BAL = ["balance", "saldo", "saldo contabile"]
ID = ["id", "transaction id", "transactionid", "id operazione"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("file")
    ap.add_argument("--account", required=True)
    ap.add_argument("--currency", default="EUR")
    ap.add_argument("--rules")
    ap.add_argument("--ledger", action="append", default=[])
    ap.add_argument("--since")
    ap.add_argument("--close", action="append", default=[])
    ap.add_argument("--until")
    ap.add_argument("--decimal-comma", action="store_true")
    ap.add_argument("--card", action="store_true")
    ap.add_argument("--unknown-out", default="Expenses:Uncategorized")
    ap.add_argument("--unknown-in", default="Income:{owner}:Other")
    a = ap.parse_args()

    owner = owner_of(a.account)
    rules = load_rules(a.rules)
    refs = known_refs(a.ledger)
    since = parse_date(a.since) if a.since else None
    dec = "," if a.decimal_comma else None
    source = a.file.rsplit("/", 1)[-1]

    out, unsure, skipped = [], 0, 0
    seen = Counter()
    running, checks = None, {}
    with open(a.file, encoding="utf-8-sig", newline="") as fh:
        sample = fh.read(4096)
        fh.seek(0)
        dialect = csv.Sniffer().sniff(sample, delimiters=",;\t") if sample else csv.excel
        reader = csv.DictReader(fh, dialect=dialect)
        rows = list(reader)
        headers = reader.fieldnames or []
    if not find_column(headers, DATE):
        raise SystemExit(f"no date column among {headers}: write a normalised CSV (date, amount, description[, balance])")
    if not find_column(headers, AMOUNT) and not (find_column(headers, IN) or find_column(headers, OUT)):
        raise SystemExit(f"no amount column among {headers}: write a normalised CSV (date, amount, description[, balance])")
    for n, row in enumerate(rows, 1):
        d = parse_date(pick(row, DATE))
        raw = pick(row, AMOUNT)
        if raw:
            amt = parse_amount(raw, dec)
        else:
            i, o = parse_amount(pick(row, IN), dec), parse_amount(pick(row, OUT), dec)
            amt = (i or 0) - abs(o or 0)
        if amt is None or (not raw and not pick(row, IN) and not pick(row, OUT)):
            raise SystemExit(f"row {n} ({d}): empty amount - check the file")
        if a.card:
            amt = -amt
        bal = pick(row, BAL)
        if running is not None:
            running += amt
        if bal:
            bal = parse_amount(bal, dec)
            if running is not None and running != bal:
                print(f"WARNING row {n} ({d}): running balance should be {running}, file says {bal}"
                      " - a row is missing, duplicated or mistyped", file=sys.stderr)
            running = bal
        if running is not None:
            checks[d] = running
        if since and d <= since:
            continue
        desc = scrub(pick(row, DESC)) or "(no description)"
        key = (d, amt, desc)
        seen[key] += 1
        ref = pick(row, ID) or make_ref(a.account, d, amt, desc, seen[key])
        if ref in refs:
            skipped += 1
            continue
        other, name, tags, sure = categorise(rules, desc, owner, amt, a.unknown_out, a.unknown_in)
        unsure += not sure
        out.append(entry(d, name or desc, desc,
                         [(a.account, amt, a.currency, ""), (other, None, None, "")],
                         {"ref": ref, "source": source}, "*" if sure else "!", tags))
    have = known_balances(a.ledger)
    bal_lines = []
    if checks:
        days = sorted(checks)
        for i, d in enumerate(days):
            if (i + 1 == len(days) or days[i + 1].month != d.month) and (not since or d > since):
                bal_lines.append((d + timedelta(days=1), checks[d]))
    if a.until and checks:
        u = parse_date(a.until)
        before = [x for x in checks if x <= u]
        if before:
            bal_lines.append((u + timedelta(days=1), checks[max(before)]))
    for c in a.close:
        d, v = c.split("=")
        bal_lines.append((parse_date(d) + timedelta(days=1), Decimal(parse_amount(v, dec)).quantize(Decimal("0.01"))))
    for d, v in dict(sorted(bal_lines)).items():   # one assertion per day
        if (d.isoformat(), a.account, a.currency) not in have:
            out.append(f"{d} balance {a.account}  {v} {a.currency}\n")
    print("\n".join(out))
    print(f"; import_csv: {len(out)} entries from {source}, {unsure} to check (!), "
          f"{skipped} already in the ledger", file=sys.stderr)


if __name__ == "__main__":
    main()
