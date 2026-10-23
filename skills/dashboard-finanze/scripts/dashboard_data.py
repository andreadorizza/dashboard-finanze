"""Export the dashboard's data files from the ledger. Only totals leave the ledger.

Usage:
  python3 dashboard_data.py main.beancount OUT_DIR [--budget budget.csv]
      [--recurring-ignore recurring_ignore.txt] [--split income|equal]
      [--fire-target 30000 --swr 0.035,0.04]

Writes to OUT_DIR:
  monthly.csv     one row per month: net worth, income, spending, savings, savings rate,
                  cash, invested, market, FX, unexplained (must be 0)
  people.csv      per month and person: net worth, income, spending, shared costs paid,
                  their fair share, and money received from (+) or sent to (-) the others
  categories.csv  per month and top-level category: amount spent, group from budget.csv
  holdings.csv    every balance on the last day: account, person, kind, units, value
  recurring.csv   payments that repeat (monthly, every two months, quarterly, yearly): cost, status
                  (active, new, increased, stopped); --recurring-ignore drops false positives
  flags.csv       entries still to confirm (flag !), described in a few words; kind
                  "transfer" = between own accounts, waiting for the other statement
  budget.csv      copied from --budget (category, group, budget) when given
  fire.csv        only with --fire-target: the optional FIRE module
"""
import argparse
import csv
import math
import re
import shutil
import statistics
import sys
from collections import defaultdict
from decimal import Decimal

from beancount.core import data

sys.path.insert(0, __file__.rsplit("/", 1)[0])
import report  # noqa: E402


def r2(x):
    return round(float(x), 2) if x is not None else ""


def write(path, header, rows):
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(header)
        w.writerows(rows)


def recurring(L, last, ignore=()):
    """Payments to the same payee at a steady rhythm and a similar amount (within 3%, or
    40% when a rule named the payee: bills vary, plans change price).
    `ignore`: regexes of names the person said are not recurring costs."""
    groups = defaultdict(list)
    for t in L.txns:
        if "Own transfer" in (t.payee or "") or "for_ref" in t.meta:   # transfers, tax set-asides
            continue
        exp = [p for p in t.postings if p.account.startswith("Expenses:")]
        bank = [p for p in t.postings if p.account.startswith(("Assets:", "Liabilities:"))]
        if len(exp) != 1 or not bank:
            continue
        p = exp[0]
        named = bool(t.payee and t.narration and t.payee != t.narration)   # payee set by a rule
        if named:
            name = t.payee.strip()          # keep the rule's name as written ("ho. Mobile")
        else:
            name = re.sub(r"[\d#*/.,:;_-]+", " ", (t.payee or t.narration or "")).strip()
            name = " ".join(name.split()[:3]) or "?"
        if any(rx.search(name) for rx in ignore):
            continue
        groups[name.lower()].append((t.date, p.units.number * L.rate(p.units.currency, t.date),
                                     p.account.split(":")[1], report.owner(bank[0].account, L.owners), name, named))
    out = []
    # (min gap, max gap, times a year, min occurrences, amount tolerance for a named payee)
    windows = {"monthly": (20, 40, 12, 3, 0.40), "bimonthly": (50, 70, 6, 3, 0.40),
               "quarterly": (75, 105, 4, 3, 0.40),
               "yearly": (350, 380, 1, 2, 0.25)}
    for key, occ in groups.items():
        occ.sort()
        occ = [o for o in occ if (last - o[0]).days <= 1100][-13:]
        if len(occ) < 2:
            continue
        gaps = [(b[0] - a[0]).days for a, b in zip(occ, occ[1:])]
        g = statistics.median(gaps)
        freq = next((f for f, w in windows.items() if w[0] <= g <= w[1]), None)
        if not freq:
            continue
        lo, hi, per_year, min_n, tol = windows[freq]
        if not occ[-1][5]:
            tol = 0.03   # a payee no rule named must charge (almost) the same amount
        if len(occ) < min_n or any(not lo <= x <= hi for x in gaps[-6:]):
            continue
        amts = [float(o[1]) for o in occ]
        recent = amts[-3:]
        med = statistics.median(recent)
        if med <= 0 or min(recent) <= 0 or (max(recent) - min(recent)) > tol * min(recent):
            continue
        interval = 365 / per_year
        year_ago = [float(o[1]) for o in occ if (occ[-1][0] - o[0]).days <= 370]
        stable = len(amts) < 2 or abs(amts[-1] - amts[-2]) <= 0.03 * min(amts[-2:])
        last_amt, before = amts[-1], year_ago[0]
        typical = last_amt if stable else statistics.median(recent)   # bills vary: use the median
        if (last - occ[-1][0]).days > interval * 1.5:
            status = "stopped"
        elif len(occ) <= min_n and (last - occ[0][0]).days < interval * (min_n + 0.5):
            status = "new"
        elif last_amt > before * 1.02 and stable:
            status = "increased"
        else:
            status = "active"
        out.append([occ[-1][4], occ[-1][2], occ[-1][3], freq, round(last_amt, 2),
                    round(typical * per_year / 12, 2), round(typical * per_year, 2),
                    occ[0][0].isoformat(), occ[-1][0].isoformat(), len(occ), status, round(before, 2)])
    out.sort(key=lambda r: (r[10] == "stopped", -r[5]))
    return out


def years_to(target, pv, c, r):
    if pv >= target:
        return 0.0
    if c <= 0:
        return float("inf")
    return math.log((target + c / r) / (pv + c / r)) / math.log(1 + r)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("ledger")
    ap.add_argument("out")
    ap.add_argument("--budget")
    ap.add_argument("--recurring-ignore", help="file with one regex per line: names that are not recurring")
    ap.add_argument("--split", default="income", choices=["income", "equal"])
    ap.add_argument("--fire-target", type=float)
    ap.add_argument("--swr", default="0.035,0.04")
    a = ap.parse_args()
    L, rows, holdings = report.main(a.ledger, a.split)
    O = a.out
    ignore = []
    if a.recurring_ignore:
        ignore = [re.compile(x.strip(), re.I) for x in open(a.recurring_ignore, encoding="utf-8")
                  if x.strip() and not x.startswith("#")]

    cum_c = cum_m = 0.0
    mrows = []
    for r in rows:
        cum_c += float(r["contributions"])
        cum_m += float(r["market"])
        mrows.append([r["month"].isoformat(), r2(r["net_worth"]), r2(r["income"]), r2(r["spending"]),
                      r2(r["savings"]), r2(r["savings_regular"]), r2(r["oneoff_net"]),
                      round(float(r["savings_rate_t12m"]), 4) if r["savings_rate_t12m"] is not None else "",
                      r2(r["income_regular"]), r2(r["cash"]), r2(r["invested"]), round(cum_c, 2),
                      r2(r["market"]), round(cum_m, 2), r2(r["fx"]), r2(r["adjustments"]), r2(r["unexplained"])])
    write(f"{O}/monthly.csv", ["month", "net_worth", "income", "spending", "savings", "savings_regular",
                                "oneoff_net", "savings_rate_t12m", "income_regular", "cash", "invested",
                                "contributions_cum", "market", "market_cum", "fx", "adjustments",
                                "unexplained"], mrows)

    write(f"{O}/people.csv", ["month", "person", "net_worth", "income", "spending", "shared_paid", "shared_share",
                               "received_from_others"],
          [[r["month"].isoformat(), o, r2(r["nw_by"][o]), r2(r["income_by"][o]), r2(r["spending_by"][o]),
            r2(r["shared_paid"][o]), r2(r["shared_share"][o]), r2(r["between"][o])] for r in rows for o in L.owners])

    group = {}
    if a.budget:
        with open(a.budget, encoding="utf-8-sig") as fh:
            for b in csv.DictReader(fh):
                group[b["category"].strip()] = (b.get("group") or "").strip()
        shutil.copy(a.budget, f"{O}/budget.csv")
    cats = sorted({c.split(":")[0] for r in rows for c in r["categories"]})
    crow = []
    for r in rows:
        tot = defaultdict(Decimal)
        for c, v in r["categories"].items():
            tot[c.split(":")[0]] += v
        for c in cats:
            crow.append([r["month"].isoformat(), c, group.get(c, ""), r2(tot.get(c, 0))])
    write(f"{O}/categories.csv", ["month", "category", "group", "amount"], crow)

    hrows = []
    for acct, inv in sorted(holdings.items()):
        if not acct.startswith(("Assets:", "Liabilities:")):
            continue
        for ccy, u in sorted(inv.items()):
            if u == 0:
                continue
            parts = acct.split(":")
            label = L.names.get(acct) or " ".join(x.replace("-", " ") for x in parts[2:]) or parts[-1]
            hrows.append([acct, report.owner(acct, L.owners), label, ccy,
                          L.kind(acct, ccy), str(u), r2(u * L.rate(ccy, L.last))])
    write(f"{O}/holdings.csv", ["account", "person", "institution", "commodity", "kind", "units", "value"], hrows)

    write(f"{O}/recurring.csv", ["name", "category", "person", "frequency", "amount", "monthly_cost",
                                  "yearly_cost", "first_date", "last_date", "count", "status",
                                  "previous_amount"], recurring(L, L.last, ignore))

    frows, n = [], 0
    for t in L.txns:
        if t.flag != "!":
            continue
        n += 1
        bank = next((p for p in t.postings if p.account.startswith(("Assets:", "Liabilities:"))
                     and not p.account.endswith(":Transit")), None)
        pending = any(p.account.endswith(":Transit") for p in t.postings)
        where = ""
        if bank:
            parts = bank.account.split(":")
            where = parts[1] + " · " + (L.names.get(bank.account) or " ".join(x.replace("-", " ") for x in parts[2:]))
        what = t.narration or t.payee or ""
        amt, ccy = (bank.units.number, bank.units.currency) if bank else ("", "")
        # "Spesa", "Casa:Affitto" for spending; "Income:Altro" for income (the person dropped)
        guess = next(("Income:" + p.account.split(":", 2)[-1] if p.account.startswith("Income:")
                      else p.account.split(":", 1)[1]
                      for p in t.postings if p.account.startswith(("Expenses:", "Income:"))), "")
        what = what.replace(" [own transfer: other side not imported yet]", "")
        frows.append([n, t.date.isoformat(), where, what, str(amt), ccy,
                      "" if pending else guess, "transfer" if pending else "category"])
    write(f"{O}/flags.csv", ["id", "date", "where", "what", "amount", "currency", "booked_as", "kind"], frows)

    if a.fire_target:
        full = [r for r in rows if r["month"] < L.last] or rows
        k = rows.index(full[-1])
        t12 = float(sum((r["savings_regular"] for r in rows[max(0, k - 11):k + 1]), Decimal(0)))
        inv = float(rows[-1]["invested"])
        out = []
        for swr in [float(s) for s in a.swr.split(",")]:
            target = a.fire_target / swr
            out.append([swr, round(target), round(inv / target, 4)] +
                       [round(years_to(target, inv, t12, ret), 1) for ret in (0.03, 0.05, 0.07)] +
                       [round(inv, 2), round(t12, 2), L.last.isoformat()])
        write(f"{O}/fire.csv", ["swr", "fire_number", "progress", "years_3", "years_5", "years_7",
                                 "invested", "savings_t12m", "as_of"], out)
    bad = [r for r in rows if abs(r["unexplained"]) > Decimal("0.05")]
    print(f"wrote {O}: {len(rows)} months, {len(hrows)} balances, {n} to check"
          + (f"; WARNING unexplained in {len(bad)} months" if bad else ""))


if __name__ == "__main__":
    main()
