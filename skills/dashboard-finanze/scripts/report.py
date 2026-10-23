"""Monthly figures from the ledger, and the check that makes them trustworthy.

Usage:  python3 report.py main.beancount [--split income|equal]

For every month: net worth (total and per person), income, spending (total, per
category, per person), savings, one-offs, money in cash and in investments, and
the change in net worth broken down as

    change = savings + market + FX + adjustments + unexplained

`unexplained` must be 0 every month. If it isn't, something is booked wrong
(a missing price, a transfer booked twice, an opening balance on the wrong date).

Conventions it relies on (see references/ledger.md):
  Assets:<Person>:<Institution>, Liabilities:<Person>:<What>   -> whose money it is
  Expenses:<Category>[:<Sub>]                                   -> what it was for
  Income:<Person>:<Type>                                        -> who earned it
  #oneoff    transaction left out of the savings rate (bonus, refund, sale of a car)
  #shared    expense shared between people (split by income or equally)
  open ... kind: "cash" | "investment" | "receivable" | "debt" | "tax" | "pension" | "property"
             (Assets:<Person>:Transit is "transit": money between two own accounts, other side missing)
  Securities are the commodities bought at a cost ({...}); prices come from price lines.
  Income accounts ending in :Capital-Gains on a sale of a security count as market.
"""
import argparse
import sys
from calendar import monthrange
from collections import defaultdict
from datetime import date, timedelta
from decimal import Decimal

from beancount import loader
from beancount.core import data, prices

D0 = Decimal(0)
GAINS_SUFFIX = (":Capital-Gains", ":Plusvalenze")


def month_ends(start, end):
    y, m = start.year, start.month
    while (y, m) <= (end.year, end.month):
        yield min(date(y, m, monthrange(y, m)[1]), end)
        y, m = (y + 1, 1) if m == 12 else (y, m + 1)


class Ledger:
    def __init__(self, path):
        entries, errors, opts = loader.load_file(path)
        if errors:
            for e in errors[:20]:
                print("LEDGER ERROR:", getattr(e, "message", e), file=sys.stderr)
            sys.exit("fix the ledger first (bean-check main.beancount)")
        self.entries = entries
        self.base = (opts.get("operating_currency") or ["EUR"])[0]
        self.pmap = prices.build_price_map(entries)
        self.kinds = {e.account: (e.meta.get("kind") or "").lower()
                      for e in entries if isinstance(e, data.Open)}
        self.names = {e.account: e.meta["name"] for e in entries
                      if isinstance(e, data.Open) and e.meta.get("name")}
        self.securities = {c.currency for c in entries if isinstance(c, data.Commodity)
                           and (c.meta.get("kind") or "").lower() == "security"}
        for e in entries:
            if isinstance(e, data.Transaction):
                for p in e.postings:
                    if p.cost is not None:
                        self.securities.add(p.units.currency)
        self.txns = sorted((e for e in entries if isinstance(e, data.Transaction)), key=lambda t: t.date)
        # balance assertions are dated the day after the statement ends
        self.last = max([e.date for e in entries if isinstance(e, data.Transaction)] +
                        [e.date - timedelta(days=1) for e in entries if isinstance(e, data.Balance)])
        self.owners = sorted({a.split(":")[1] for a in self.kinds
                              if a.split(":")[0] in ("Assets", "Liabilities") and len(a.split(":")) > 2})

    def rate(self, ccy, d):
        if ccy == self.base:
            return Decimal(1)
        _, p = prices.get_price(self.pmap, (ccy, self.base), d)
        if p is None:
            raise SystemExit(f"no price for {ccy} in {self.base} on or before {d}: add a price line")
        return p

    def kind(self, account, ccy):
        if account.endswith(":Transit"):
            return "transit"       # a transfer whose other side isn't imported yet
        if ccy in self.securities:
            return "investment"
        k = self.kinds.get(account, "")
        if k == "investment":
            return "cash"          # cash held at a broker is still cash
        if k:
            return k
        return "debt" if account.startswith("Liabilities:") else "cash"


def owner(account, owners):
    parts = account.split(":")
    return parts[1] if len(parts) > 2 and parts[1] in owners else "Household"


def main(path, split="income"):
    L = Ledger(path)
    nw_acct = lambda a: a.startswith(("Assets:", "Liabilities:"))  # noqa: E731
    is_opening = lambda t: any(p.account.startswith("Equity:Opening") for p in t.postings)  # noqa: E731
    regular = [t for t in L.txns if not is_opening(t)]
    if not regular:
        sys.exit("no transactions yet")
    start = regular[0].date
    prev_end = date(start.year, start.month, 1) - timedelta(days=1)
    holdings = defaultdict(lambda: defaultdict(Decimal))

    def classes(d):
        base = fx = sec = D0
        for acct, inv in holdings.items():
            if not nw_acct(acct):
                continue
            for ccy, u in inv.items():
                v = u * L.rate(ccy, d)
                if ccy in L.securities:
                    sec += v
                elif ccy == L.base:
                    base += v
                else:
                    fx += v
        return base, fx, sec

    def value(pred, d):
        return sum((u * L.rate(c, d) for a, inv in holdings.items() if pred(a)
                    for c, u in inv.items() if u), D0)

    def value_kind(kind, d):
        return sum((u * L.rate(c, d) for a, inv in holdings.items() if nw_acct(a)
                    for c, u in inv.items() if u and L.kind(a, c) == kind), D0)

    i = 0
    while i < len(L.txns) and L.txns[i].date <= prev_end:
        for p in L.txns[i].postings:
            holdings[p.account][p.units.currency] += p.units.number
        i += 1
    prev_cls = classes(prev_end)
    rows = []
    for end in month_ends(start, L.last):
        inc = defaultdict(Decimal)
        inc_oneoff = defaultdict(Decimal)
        exp_cat = defaultdict(Decimal)
        exp_payer = defaultdict(Decimal)
        shared_paid = defaultdict(Decimal)
        shared_total = D0
        exp_oneoff = D0
        flows_fx = flows_sec = adjustments = realised = contributions = D0
        between = defaultdict(Decimal)   # money moved between people: + received, - sent
        while i < len(L.txns) and L.txns[i].date <= end:
            t = L.txns[i]
            i += 1
            tags = set(t.tags or ())
            payer = next((owner(p.account, L.owners) for p in t.postings
                          if nw_acct(p.account) and p.units.number < 0), None) or \
                next((owner(p.account, L.owners) for p in t.postings if nw_acct(p.account)), "Household")
            has_sec = any(p.units.currency in L.securities for p in t.postings)
            nw_owners = {owner(p.account, L.owners) for p in t.postings if nw_acct(p.account)}
            person_move = len(nw_owners) > 1 and all(nw_acct(p.account) or p.account.startswith("Expenses:Fees")
                                                      for p in t.postings)
            resid = D0
            for p in t.postings:
                u, ccy = p.units.number, p.units.currency
                holdings[p.account][ccy] += u
                if p.cost is not None and p.cost.number is not None:
                    v = u * p.cost.number * L.rate(p.cost.currency, t.date)
                else:
                    v = u * L.rate(ccy, t.date)
                resid += v
                if nw_acct(p.account):
                    if person_move:
                        between[owner(p.account, L.owners)] += v
                    if ccy in L.securities:
                        flows_sec += v
                        if v > 0:
                            contributions += v
                    elif ccy != L.base:
                        flows_fx += v
                elif p.account.startswith("Income:"):
                    if has_sec and p.account.endswith(GAINS_SUFFIX):
                        realised += -v
                        continue
                    who = owner("Assets:" + ":".join(p.account.split(":")[1:]), L.owners)
                    inc[who] += -v
                    if "oneoff" in tags:
                        inc_oneoff[who] += -v
                elif p.account.startswith("Expenses:"):
                    cat = p.account.split(":", 1)[1]
                    exp_cat[cat] += v
                    exp_payer[payer] += v
                    if "oneoff" in tags:
                        exp_oneoff += v
                    if "shared" in tags:
                        shared_paid[payer] += v
                        shared_total += v
                elif p.account.startswith("Equity:"):
                    adjustments += -v
            flows_fx -= resid   # a conversion at the bank's rate vs our month-end rate is FX
        base, fx, sec = classes(end)
        nw = base + fx + sec
        income = sum(inc.values(), D0)
        spending = sum(exp_cat.values(), D0)
        savings = income - spending
        oneoff_net = sum(inc_oneoff.values(), D0) - exp_oneoff
        market = (sec - prev_cls[2]) - flows_sec + realised
        fx_eff = (fx - prev_cls[1]) - flows_fx
        unexplained = (nw - sum(prev_cls)) - savings - market - fx_eff - adjustments
        # shared costs: each person's fair share, by regular income over the last 12 months or equally
        hist = rows[-11:]
        share = {}
        if L.owners:
            if split == "income":
                ti = {o: sum((r["income_regular_by"][o] for r in hist), D0) +
                      inc[o] - inc_oneoff[o] for o in L.owners}
                tot = sum(ti.values(), D0)
                share = {o: (ti[o] / tot if tot > 0 else Decimal(1) / len(L.owners)) for o in L.owners}
            else:
                share = {o: Decimal(1) / len(L.owners) for o in L.owners}
        rows.append({
            "month": end, "net_worth": nw,
            "nw_by": {o: value(lambda a, o=o: nw_acct(a) and owner(a, L.owners) == o, end) for o in L.owners},
            "income": income, "spending": spending, "savings": savings,
            "income_oneoff": sum(inc_oneoff.values(), D0), "spending_oneoff": exp_oneoff,
            "oneoff_net": oneoff_net, "savings_regular": savings - oneoff_net,
            "income_regular": income - sum(inc_oneoff.values(), D0),
            "income_by": {o: inc[o] for o in L.owners},
            "income_regular_by": {o: inc[o] - inc_oneoff[o] for o in L.owners},
            "spending_by": {o: exp_payer[o] for o in L.owners},
            "shared_paid": {o: shared_paid[o] for o in L.owners},
            "shared_share": {o: shared_total * share.get(o, D0) for o in L.owners},
            "between": {o: between[o] for o in L.owners},
            "categories": dict(exp_cat),
            "cash": value_kind("cash", end), "invested": sec,
            "contributions": contributions, "market": market, "fx": fx_eff,
            "adjustments": adjustments, "unexplained": unexplained,
        })
        prev_cls = (base, fx, sec)
    for k, r in enumerate(rows):
        win = rows[max(0, k - 11):k + 1]
        ti = sum((x["income_regular"] for x in win), D0)
        r["savings_rate_t12m"] = (sum((x["savings_regular"] for x in win), D0) / ti) if len(win) == 12 and ti else None
    return L, rows, holdings


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("ledger")
    ap.add_argument("--split", default="income", choices=["income", "equal"])
    a = ap.parse_args()
    L, rows, _ = main(a.ledger, a.split)
    f = lambda x: f"{x:>11,.0f}"  # noqa: E731
    print(f"{'month':<11}{'net worth':>11}{'income':>11}{'spending':>11}{'savings':>11}"
          f"{'one-off':>11}{'market':>11}{'FX':>11}{'adjust':>11}{'UNEXPL.':>11}")
    for r in rows[-8:]:
        print(f"{r['month'].isoformat():<11}{f(r['net_worth'])}{f(r['income'])}{f(r['spending'])}"
              f"{f(r['savings_regular'])}{f(r['oneoff_net'])}{f(r['market'])}{f(r['fx'])}"
              f"{f(r['adjustments'])}{r['unexplained']:>11.2f}")
    bad = [r for r in rows if abs(r["unexplained"]) > Decimal("0.05")]
    print(f"\n{len(rows)} months, base currency {L.base}, people: {', '.join(L.owners) or '-'}")
    print("unexplained is 0 in every month" if not bad else
          f"UNEXPLAINED in {len(bad)} months, first {bad[0]['month']}: fix before trusting the numbers")
