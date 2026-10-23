"""Pair the two halves of every transfer between your own accounts into one entry.

Usage:
  python3 match_transfers.py new1.bean new2.bean ... [--ledger main-year.beancount]
      [--prices prices.beancount] > merged.bean

The importers book a recognised own transfer (a rule pointing at
Assets:{owner}:Transit) as a half: money leaves account A towards Transit, or
reaches account B from Transit. This script finds the two halves and writes ONE
entry, so moving money between your own accounts never counts as income or
spending:

  2026-03-31 * "Own transfer" "Marco Revolut USD -> Marco N26 EUR: Transfer to N26"
    Assets:Marco:Revolut   -2100.00 USD
    Assets:Marco:N26        1811.55 EUR @@ 2100.00 USD

Matching: an outgoing half and an incoming half 0-6 days apart (1 day earlier allowed
for time zones), same currency and the amount received equal to the amount sent or up
to 1% less (the difference is booked as a fee). Different currencies need --prices:
the two amounts must agree within 3% at the nearest month-end rates.
Halves left over come out with the ! flag: the other account's statement isn't in
yet. Next time pass --ledger with the file they were appended to: they join the pool,
and stderr names any old half that got paired so you can delete it from that file.
Entries whose ref is already in --ledger are dropped (safe to re-run).
"""
import argparse
import bisect
import re
import sys
from datetime import date
from decimal import Decimal

HEAD = re.compile(r'^(\d{4}-\d{2}-\d{2}) ([*!]) "([^"]*)" "([^"]*)"(.*)$')
META = re.compile(r'^\s+([a-z_]+): "(.*)"$')
POST = re.compile(r'^\s+([A-Z][\w:-]+)(?:\s+(-?[\d.]+)\s+([A-Z][A-Z0-9._-]*))?\s*$')
PRICE = re.compile(r'^(\d{4}-\d{2}-\d{2})\s+price\s+([A-Z][A-Z0-9._-]*)\s+([\d.]+)\s+([A-Z]+)', re.M)


def blocks(text):
    cur = []
    for line in text.splitlines():
        if not line.strip():
            if cur:
                yield "\n".join(cur)
                cur = []
        elif cur and not line[0].isspace():
            yield "\n".join(cur)
            cur = [line]
        else:
            cur.append(line)
    if cur:
        yield "\n".join(cur)


def parse_half(block, origin):
    lines = block.splitlines()
    m = HEAD.match(lines[0])
    if not m:
        return None
    meta, posts = {}, []
    for ln in lines[1:]:
        mm = META.match(ln)
        if mm:
            meta[mm.group(1)] = mm.group(2)
        else:
            pm = POST.match(ln)
            if pm:
                posts.append(pm.groups())
    if len(posts) != 2:
        return None
    transit = [p for p in posts if p[0].endswith(":Transit") and not p[1]]
    bank = [p for p in posts if not p[0].endswith(":Transit") and p[1]]
    if len(transit) != 1 or len(bank) != 1:
        return None
    return {"date": m.group(1), "payee": m.group(3), "narr": m.group(4), "meta": meta,
            "account": bank[0][0], "amount": Decimal(bank[0][1]), "ccy": bank[0][2],
            "block": block, "origin": origin, "used": False}


class Rates:
    def __init__(self, path):
        self.by = {}
        if path:
            for d, c, v, base in PRICE.findall(open(path, encoding="utf-8").read()):
                self.by.setdefault(c, []).append((d, Decimal(v)))
            for c in self.by:
                self.by[c].sort()
        self.base = None

    def value(self, amt, ccy, d, base):
        if ccy == base:
            return amt
        rows = self.by.get(ccy)
        if not rows:
            return None
        i = max(0, bisect.bisect_right(rows, (d, Decimal("1e30"))) - 1)
        return amt * rows[i][1]


def gap(a, b):
    return (date.fromisoformat(b) - date.fromisoformat(a)).days


def label(h):
    return " ".join(h["account"].split(":")[1:]) + " " + h["ccy"]


def merge(o, i):
    sent, got = -o["amount"], i["amount"]
    memo = o["narr"] or o["payee"]
    lines = [f'{o["date"]} * "Own transfer" "{label(o)} -> {label(i)}: {memo}"',
             f'  ref: "{o["meta"].get("ref", "")}"', f'  ref_in: "{i["meta"].get("ref", "")}"',
             f'  source: "{o["meta"].get("source", "")} + {i["meta"].get("source", "")}"',
             f'  {o["account"]:<40}{-sent:>14} {o["ccy"]}']
    if i["ccy"] != o["ccy"]:
        lines.append(f'  {i["account"]:<40}{got:>14} {i["ccy"]} @@ {sent} {o["ccy"]}')
    else:
        lines.append(f'  {i["account"]:<40}{got:>14} {i["ccy"]}')
        if sent != got:
            lines.append(f'  {"Expenses:Fees":<40}{sent - got:>14} {o["ccy"]}')
    return "\n".join(lines) + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="+")
    ap.add_argument("--ledger", action="append", default=[])
    ap.add_argument("--prices")
    ap.add_argument("--base", default="EUR")
    a = ap.parse_args()
    rates = Rates(a.prices)

    known, pool = set(), []
    for lp in a.ledger:
        text = open(lp, encoding="utf-8").read()
        known |= set(re.findall(r'^\s+(?:ref|ref_in): "([^"]+)"', text, re.M))
        for b in blocks(text):
            h = parse_half(b, lp)
            if h:
                pool.append(h)
    out, dropped = [], 0
    for f in a.files:
        for b in blocks(open(f, encoding="utf-8").read()):
            if b.lstrip().startswith(";"):
                continue
            r = re.search(r'^\s+ref: "([^"]+)"', b, re.M)
            if r and r.group(1) in known:
                dropped += 1
                continue
            h = parse_half(b, "new")
            if h:
                pool.append(h)
            out.append(b)

    outs = sorted((h for h in pool if h["amount"] < 0), key=lambda h: h["date"])
    ins = [h for h in pool if h["amount"] > 0]
    merged = []
    for o in outs:
        sent = -o["amount"]
        best = None
        for i in ins:
            if i["used"] or i["account"] == o["account"]:
                continue
            g = gap(o["date"], i["date"])
            if not -1 <= g <= 6:
                continue
            got = i["amount"]
            if i["ccy"] == o["ccy"]:
                ok = Decimal(0) <= sent - got <= max(Decimal("0.011"), sent * Decimal("0.01"))
                diff = abs(sent - got)
            else:
                vs, vg = rates.value(sent, o["ccy"], o["date"], a.base), rates.value(got, i["ccy"], i["date"], a.base)
                ok = vs is not None and vg is not None and abs(vs - vg) <= vs * Decimal("0.03")
                diff = abs(vs - vg) if ok else None
            if ok and (best is None or (abs(g), diff) < best[0]):
                best = ((abs(g), diff), i)
        if best:
            i = best[1]
            o["used"] = i["used"] = True
            merged.append(merge(o, i))
            for h in (o, i):
                if h["origin"] != "new":
                    print(f"paired a half already in {h['origin']}: delete the entry with "
                          f"ref {h['meta'].get('ref')} from it", file=sys.stderr)

    for b in out:
        h = next((x for x in pool if x["block"] is b), None)
        if h is None:
            print(b + "\n")
        elif not h["used"]:
            first, *rest = b.splitlines()
            m = HEAD.match(first)
            first = (f'{m.group(1)} ! "{m.group(3)}" "{m.group(4)} '
                     f'[own transfer: other side not imported yet]"{m.group(5)}')
            print("\n".join([first] + rest) + "\n")
    for t in merged:
        print(t)
    left = sum(1 for h in pool if not h["used"])
    print(f"; match_transfers: {len(merged)} transfers paired, {left} halves waiting, "
          f"{dropped} duplicates dropped", file=sys.stderr)


if __name__ == "__main__":
    main()
