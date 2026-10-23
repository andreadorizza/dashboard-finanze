"""Turn a broker statement into ledger entries.

Brokers all export differently, so first write the statement as a normalised CSV
with these columns (one row per movement), then run this:

  date, kind, symbol, quantity, amount, currency, description

  kind        deposit | withdrawal | buy | sell | dividend | interest | fee | tax | position | cash
  symbol      the ticker (VWCE, SWDA...) for buy, sell, dividend and position rows
  quantity    units bought (+) or sold (-); for `position`, units held at that date
  amount      cash movement in `currency`: buy -1000.00, sell +1050.00, fee -1.00,
              deposit +500.00; for `cash`, the cash balance at that date
  description free text (optional)

Usage:
  python3 import_broker.py FILE --account Assets:Giulia:TradeRepublic
      [--ledger main.beancount ...] [--interest Income:{owner}:Interest]
      [--dividends Income:{owner}:Dividends] [--gains Income:{owner}:Capital-Gains]
      [--fees Expenses:Fees] [--taxes Expenses:Taxes] [--lang it]

Buys are booked at their total cost (fees included when the broker adds them to the
price). Sells use the ledger's booking method (main.beancount sets FIFO) and the
gain goes to --gains. Deposits and withdrawals go to Assets:{owner}:Transit so
match_transfers.py can pair them with the bank side. `position` and `cash` rows
become balance assertions, so the ledger must agree with the broker.
New tickers need a `commodity` line and month-end prices (see references/ledger.md).
"""
import argparse
import csv
import sys
from collections import Counter
from datetime import timedelta
from decimal import Decimal

sys.path.insert(0, __file__.rsplit("/", 1)[0])
from common import (entry, known_balances, known_refs, make_ref, owner_of, parse_amount,  # noqa: E402
                    parse_date, scrub)


# payee labels shown in the ledger and in the recurring-costs list
LABELS = {
    "en": {"buy": "Buy", "sell": "Sell", "dividend": "Dividend", "interest": "Interest", "fee": "Fee", "tax": "Tax"},
    "it": {"buy": "Acquisto", "sell": "Vendita", "dividend": "Dividendo", "interest": "Interessi",
           "fee": "Commissione", "tax": "Imposta"},
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("file")
    ap.add_argument("--account", required=True)
    ap.add_argument("--ledger", action="append", default=[])
    ap.add_argument("--interest", default="Income:{owner}:Interest")
    ap.add_argument("--dividends", default="Income:{owner}:Dividends")
    ap.add_argument("--gains", default="Income:{owner}:Capital-Gains")
    ap.add_argument("--fees", default="Expenses:Fees")
    ap.add_argument("--taxes", default="Expenses:Taxes")
    ap.add_argument("--lang", default="en", choices=sorted(LABELS), help="language of the payee labels")
    a = ap.parse_args()
    T = LABELS[a.lang]
    owner = owner_of(a.account)
    acc = lambda s: s.replace("{owner}", owner)  # noqa: E731
    refs = known_refs(a.ledger)
    have = known_balances(a.ledger)
    source = a.file.rsplit("/", 1)[-1]
    seen, out, skipped = Counter(), [], 0
    with open(a.file, encoding="utf-8-sig", newline="") as fh:
        rows = list(csv.DictReader(fh))
    for n, r in enumerate(rows, 1):
        d = parse_date(r["date"])
        kind = r["kind"].strip().lower()
        sym = (r.get("symbol") or "").strip().upper()
        ccy = (r.get("currency") or "EUR").strip().upper()
        qty = parse_amount(r.get("quantity") or "")
        amt = parse_amount(r.get("amount") or "")
        desc = scrub(r.get("description") or "") or kind
        if kind in ("position", "cash"):
            c = sym if kind == "position" else ccy
            if ((d + timedelta(days=1)).isoformat(), a.account, c) not in have:
                v = qty if kind == "position" else f"{amt:.2f}"
                out.append(f"{d + timedelta(days=1)} balance {a.account}  {v} {c}\n")
            continue
        key = (d, kind, sym, qty, amt)
        seen[key] += 1
        ref = make_ref(a.account, *key, seen[key])
        if ref in refs:
            skipped += 1
            continue
        meta = {"ref": ref, "source": source}
        if kind == "buy":
            legs = [(a.account, qty, sym, f"{{{{{-amt} {ccy}}}}}"), (a.account, amt, ccy, "")]
            out.append(entry(d, f"{T['buy']} {sym}", desc, legs, meta))
        elif kind == "sell":
            price = (amt / -qty).quantize(Decimal("0.0001"))
            legs = [(a.account, qty, sym, f"{{}} @ {price} {ccy}"), (a.account, amt, ccy, ""),
                    (acc(a.gains), None, None, "")]
            out.append(entry(d, f"{T['sell']} {sym}", desc, legs, meta))
        elif kind in ("deposit", "withdrawal"):
            legs = [(a.account, amt, ccy, ""), (f"Assets:{owner}:Transit", None, None, "")]
            out.append(entry(d, "Own transfer", desc, legs, meta))
        else:
            other = {"dividend": a.dividends, "interest": a.interest, "fee": a.fees,
                     "tax": a.taxes}.get(kind)
            if not other:
                raise SystemExit(f"row {n}: unknown kind {kind!r}")
            legs = [(a.account, amt, ccy, ""), (acc(other), None, None, "")]
            where = a.account.split(":")[-1]
            out.append(entry(d, f"{T[kind]} {sym or where}", desc, legs, meta))
    print("\n".join(out))
    print(f"; import_broker: {len(out)} entries from {source}, {skipped} already in the ledger",
          file=sys.stderr)


if __name__ == "__main__":
    main()
