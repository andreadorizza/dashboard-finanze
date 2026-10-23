"""Book a tax set-aside on every receipt of an income account (for freelancers).

Usage:
  python3 set_aside.py main.beancount --income Income:Marco:Work --rate 0.24
      [--expense Expenses:Taxes:Set-aside] [--liability Liabilities:{owner}:Taxes-due]
      [--since YYYY-MM-DD]  >> 2026.beancount

For each transaction that credits --income, writes one entry
  Expenses:Taxes:Set-aside        rate x amount
  Liabilities:Marco:Taxes-due    -rate x amount
so the money is counted as spent when it is earned, not when the tax is paid.
When the tax is paid, a rule books the payment to the liability (no spending then).
Each set-aside carries `for_ref` (the receipt's ref): running it twice adds nothing.
The rate is the person's own estimate: their accountant's figures always win.
"""
import argparse
import re
import sys
from decimal import Decimal

from beancount import loader
from beancount.core import data, prices


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("ledger")
    ap.add_argument("--income", required=True, help="account (or regex) of the receipts")
    ap.add_argument("--rate", required=True, type=Decimal)
    ap.add_argument("--expense", default="Expenses:Taxes:Set-aside")
    ap.add_argument("--liability", default="Liabilities:{owner}:Taxes-due")
    ap.add_argument("--since")
    a = ap.parse_args()
    entries, errors, opts = loader.load_file(a.ledger)
    base = (opts.get("operating_currency") or ["EUR"])[0]
    pmap = prices.build_price_map(entries)
    rx = re.compile(a.income if any(c in a.income for c in "*^$[") else "^" + re.escape(a.income) + "$")
    done = {e.meta.get("for_ref") for e in entries if isinstance(e, data.Transaction)}
    out = []
    for e in entries:
        if not isinstance(e, data.Transaction) or (a.since and e.date.isoformat() <= a.since):
            continue
        for p in e.postings:
            if not rx.search(p.account) or p.units.number >= 0:
                continue
            ref = e.meta.get("ref") or f"{e.date}-{p.account}-{p.units.number}"
            if ref in done:
                continue
            amt = -p.units.number
            if p.units.currency != base:
                _, r = prices.get_price(pmap, (p.units.currency, base), e.date)
                if r is None:
                    sys.exit(f"no {p.units.currency} price on {e.date}: add prices first")
                amt *= r
            owner = p.account.split(":")[1]
            v = (amt * a.rate).quantize(Decimal("0.01"))
            liab = a.liability.replace("{owner}", owner)
            out.append(f'{e.date} * "Tax set-aside" "{int(a.rate * 100)}% of {e.payee or p.account}"\n'
                       f'  for_ref: "{ref}"\n'
                       f'  {a.expense:<40}{v:>14} {base}\n'
                       f'  {liab:<40}{-v:>14} {base}\n')
            done.add(ref)
    print("\n".join(out))
    print(f"; set_aside: {len(out)} set-asides", file=sys.stderr)


if __name__ == "__main__":
    main()
