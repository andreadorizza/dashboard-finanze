"""Invent bank and broker statements for a fictional couple (Giulia & Marco), Jan 2024 - 21 Oct 2026,
in the shapes real exports come in, to test the skill's pipeline end to end.

Writes into OUT/statements: giulia_fineco.csv (Italian, ; and decimal comma, Entrate/Uscite),
marco_n26.csv (N26-style, no balance column; closing balances in marco_n26_closes.txt),
marco_revolut_usd.csv (Revolut-style with Balance), giulia_traderepublic.csv and marco_ibkr.csv
(normalised broker format), plus OUT/ledger/prices.beancount and an opening-balances file.
"""
import calendar
import csv
import datetime as dt
import os
import random
import sys
from decimal import Decimal, ROUND_HALF_UP

OUT = sys.argv[1]
random.seed(3)
os.makedirs(f"{OUT}/statements", exist_ok=True)
os.makedirs(f"{OUT}/ledger", exist_ok=True)
Q = lambda x: Decimal(str(x)).quantize(Decimal("0.01"), ROUND_HALF_UP)  # noqa: E731
Q4 = lambda x: Decimal(str(x)).quantize(Decimal("0.0001"), ROUND_HALF_UP)  # noqa: E731

START = dt.date(2023, 12, 31)
AS_OF = dt.date(2026, 10, 21)
ends = []
for y in (2024, 2025, 2026):
    for m in range(1, 13):
        d = dt.date(y, m, calendar.monthrange(y, m)[1])
        if d > AS_OF:
            break
        ends.append(d)
ends.append(AS_OF)

# ── month-end prices (invented) ───────────────────────────────────────────
px = {"VWCE": [105.0], "SWDA": [88.0], "EIMI": [30.0]}
usd = [0.905]
shock = {(2025, 3): -0.05, (2025, 4): -0.075, (2024, 8): -0.03, (2026, 3): -0.035}
for d in ends:
    g = random.gauss(0.009, 0.03) + shock.get((d.year, d.month), 0)
    em = g + random.gauss(-0.002, 0.02)
    if d == AS_OF:
        g, em = 0.009, 0.004
    px["VWCE"].append(px["VWCE"][-1] * (1 + g))
    px["SWDA"].append(px["SWDA"][-1] * (1 + g + random.gauss(0.001, 0.004)))
    px["EIMI"].append(px["EIMI"][-1] * (1 + em))
    usd.append(usd[-1] * (1 + random.gauss(-0.002, 0.014)))
with open(f"{OUT}/ledger/prices.beancount", "w") as fh:
    fh.write("; Month-end closes (INVENTED for the demo). USD is EUR per 1 USD.\n")
    for i, d in enumerate([START] + ends):
        for c in px:
            fh.write(f"{d} price {c:<5} {Q4(px[c][i])} EUR\n")
        fh.write(f"{d} price USD   {Q4(usd[i])} EUR\n")


def mid(c, i):
    return Q4((px[c][i - 1] + px[c][i]) / 2)


def day(y, m, d):
    last = calendar.monthrange(y, m)[1]
    return dt.date(y, m, min(d, last))


# ── transactions per account ──────────────────────────────────────────────
fineco, n26, rev, tr, ib = [], [], [], [], []
bal = {"fineco": Q(5500), "n26": Q(6000), "rev": Q(1200), "tax": Q(-2100)}
n26_closes = []
TRIPS = {(2024, 4): 650, (2024, 8): 1900, (2024, 12): 400, (2025, 5): 780, (2025, 8): 2250,
         (2025, 12): 520, (2026, 4): 1100, (2026, 8): 2600}
REST = ["BAR CENTRALE", "TRATTORIA DA MARIO", "PIZZERIA NAPOLI", "SUSHI ZEN", "OSTERIA DEL PONTE", "CAFFE BRERA"]
SHOP = ["AMAZON EU", "IKEA", "ZARA", "DECATHLON", "MEDIAWORLD"]
GROC = ["ESSELUNGA", "CONAD", "LIDL", "CARREFOUR EXPRESS"]
TRAVEL = ["TRENITALIA", "BOOKING.COM", "RYANAIR", "ITALO"]
tax_accrued_since = Q(0)


def g(d, desc, amt):           # Giulia Fineco row
    fineco.append((d, desc, Q(amt)))


def n(d, desc, amt):           # Marco N26 row
    n26.append((d, desc, Q(amt)))


for i, end in enumerate(ends, start=1):
    y, m = end.year, end.month
    partial = end == AS_OF
    upto = end.day if partial else 31
    D = lambda dd: day(y, m, dd)  # noqa: E731
    ok = lambda dd: dd <= upto    # noqa: E731
    # Giulia income
    sal = 2180 if y == 2024 else 2250 if (y, m) < (2026, 3) else 2390
    if ok(27):
        extra = {7: " E QUATTORDICESIMA", 12: " E TREDICESIMA"}.get(m, "")
        g(D(27), f"STIPENDIO{extra} STUDIO LUMEN SRL", sal * (2 if extra else 1))
        if m == 7:
            g(D(27), "RIMBORSO 730 SOSTITUTO D'IMPOSTA", {2024: 480, 2025: 640, 2026: 910}[y])
    # Giulia fixed costs
    g(D(1), "BONIFICO AFFITTO MESE A PROPRIETARIO", -(1350 if y < 2026 else 1390))
    g(D(1), "BONIFICO DA MARCO B. QUOTA AFFITTO E SPESE", 550)
    n(D(1), "Giulia B. Quota affitto", -550)
    g(D(1), "ATM MILANO ABBONAMENTO MENSILE", -39)
    if ok(5):
        g(D(5), "ILIAD ITALIA", -9.99)
    if ok(10):
        g(D(10), "PALESTRA FITLAB MILANO", -45)
    if ok(15):
        g(D(15), "SPOTIFY P1234", -(11.99 if (y, m) < (2025, 2) else 12.99))
    if (y, m) >= (2026, 8) and ok(18):
        g(D(18), "YOGA ONLINE ABBONAMENTO", -9.99)
    # PAC + emergency fund to Trade Republic
    if not partial or ok(3):
        amt = 600 if y == 2024 else 800
        g(D(3), "BONIFICO A TRADE REPUBLIC BANK", -amt)
        tr.append([D(3), "deposit", "", "", Q(amt), "EUR", "Deposito"])
        price = mid("VWCE", i)
        qty = Q4(Decimal(amt) / price)
        cost = Q(qty * price)
        tr.append([D(3), "buy", "VWCE", qty, -cost, "EUR", "Piano di accumulo"])
        if cost != amt:
            pass
    if (y, m) == (2024, 3):
        g(D(28), "BONIFICO A TRADE REPUBLIC BANK FONDO EMERGENZA", -2500)
        tr.append([D(28), "deposit", "", "", Q(2500), "EUR", "Deposito"])
    # variable spending, Giulia
    k = 0.65 if partial else 1.0
    for _ in range(random.randint(3, 5)):
        dd = random.randint(2, 28)
        if ok(dd):
            g(D(dd), "PAGAMENTO CARTA " + random.choice(REST), -round(random.uniform(20, 65) * k, 2))
    if random.random() < 0.6 and ok(14):
        g(D(14), "PAGAMENTO CARTA FARMACIA SAN MARCO", -round(random.uniform(9, 45), 2))
    for _ in range(random.randint(2, 4)):
        dd = random.randint(2, 28)
        if ok(dd):
            g(D(dd), "PAGAMENTO CARTA " + random.choice(SHOP), -round(random.uniform(20, 150) * k, 2))
    if (y, m) == (2026, 9):
        g(D(22), "PAGAMENTO CARTA MEDIAWORLD LAVATRICE", -449)
    if m == 12:
        g(D(18), "PAGAMENTO CARTA LIBRERIA FELTRINELLI", -round(random.uniform(90, 140), 2))
        g(D(20), "PAGAMENTO CARTA FIORAIO ROSE", -35)
    trip = TRIPS.get((y, m), 0)
    if trip and m % 2:
        g(D(9), "PAGAMENTO CARTA " + random.choice(TRAVEL), -trip)
    if (y, m) == (2026, 10):
        g(D(3), "PAYPAL *MKTPLACE", -64.90)

    # Marco income
    base = 2700 if y < 2026 else 3100
    inv = 1400 if partial else 900 if m == 8 else 3600 if m == 12 else round(random.gauss(base, 380), -1)
    if partial:
        n(D(15), "CLIENTE ALFA SRL Fattura", inv)
    else:
        a1 = round(inv * 0.6, -1)
        n(D(10), "CLIENTE ALFA SRL Fattura", a1)
        n(D(22), "BETA STUDIO SRL Fattura", inv - a1)
    if (y, m) == (2026, 1):
        n(D(16), "BONIFICO DA ACQUIRENTE AUTO USATA", 5800)
    if (y, m) == (2026, 2):
        n(D(10), "BONIFICO A INTERACTIVE BROKERS", -5000)
        ib.append([D(11), "deposit", "", "", Q(5000), "EUR", "Deposit"])
        price = mid("SWDA", i)
        qty = Q4(Decimal(5000) / price)
        ib.append([D(11), "buy", "SWDA", qty, -Q(qty * price), "EUR", "Lump sum"])
    if (y, m) == (2026, 9):
        n(D(18), "Bonifico in entrata", 250)
    if (y, m) >= (2024, 6) and ok(5):
        rev.append((D(5), "Payment from Northwind LLC", Q(750)))
    # Marco fixed costs
    if ok(6):
        n(D(6), "FASTWEB SPA", -27.95)
        n(D(6), "HO. MOBILE", -7.99)
    if ok(8):
        n(D(8), "NETFLIX.COM", -(13.99 if (y, m) < (2026, 9) else 15.99))
        n(D(8), "APPLE.COM/BILL", -2.99)
        n(D(8), "CURSOR AI SOFTWARE", -19.50)
    if m % 2 == 0 and ok(20):
        n(D(20), "ENEL ENERGIA BOLLETTA", -round(random.uniform(120, 200) if m in (2, 12) else random.uniform(70, 120), 2))
    if m in (1, 2, 3, 11, 12) and ok(25):
        n(D(25), "A2A GAS BOLLETTA", -round(random.uniform(60, 110), 2))
    if (y, m) < (2026, 1):
        if ok(4):
            n(D(4), "TELEPASS", -3.90)
        n(D(min(12, upto)), "ENI STATION RIFORNIMENTO", -round(random.uniform(45, 70), 2))
        if m == 2:
            n(D(14), "ASSICURAZIONE AUTO RINNOVO", -(420 if y == 2024 else 445))
    # PAC to IBKR
    if not partial or ok(3):
        pac = 700 if y == 2024 else 800
        n(D(3), "BONIFICO A INTERACTIVE BROKERS", -pac)
        ib.append([D(4), "deposit", "", "", Q(pac), "EUR", "Deposit"])
        for c, share in (("SWDA", 0.8), ("EIMI", 0.2)):
            price = mid(c, i)
            qty = Q4(Decimal(pac * share) / price)
            ib.append([D(4), "buy", c, qty, -Q(qty * price), "EUR", "Monthly plan"])
        ib.append([D(4), "fee", "", "", Q(-1.25), "EUR", "Commission"])
    # groceries, restaurants, shopping, travel (Marco)
    for _ in range(random.randint(4, 6)):
        dd = random.randint(1, 28)
        if ok(dd):
            n(D(dd), "Card " + random.choice(GROC), -round(random.uniform(55, 130) * k, 2))
    for _ in range(random.randint(2, 4)):
        dd = random.randint(2, 28)
        if ok(dd):
            n(D(dd), "Card " + random.choice(REST), -round(random.uniform(20, 70) * k, 2))
    if random.random() < 0.7 and ok(17):
        n(D(17), "Card " + random.choice(SHOP), -round(random.uniform(20, 120), 2))
    if trip and not m % 2:
        n(D(9), "Card " + random.choice(TRAVEL), -trip)
    elif not trip and random.random() < 0.4 and ok(21):
        n(D(21), "Card TRENITALIA", -round(random.uniform(19, 59), 2))
    if m == 12:
        n(D(19), "Card AMAZON EU regali", -round(random.uniform(150, 220), 2))
    # quarterly USD -> EUR
    if m in (3, 6, 9, 12) and not partial:
        usd_bal = sum(x[2] for x in rev) + Q(1200)
        x = usd_bal - 300
        if x > 0:
            rev.append((D(28), "Transfer to Marco N26", -x))
            n(D(29), "BONIFICO DA MARCO REVOLUT", Q(x * Decimal(str(usd[i])) * Decimal("0.996")))
    if (y, m) == (2026, 10):
        rev.append((D(12), "ATM WITHDRAWAL LISBON", Q(-120)))
    # Trade Republic interest on cash
    tr_cash = 300 + sum(r[4] for r in tr if r[1] in ("deposit", "buy", "interest"))
    rate = 0.0375 if y == 2024 else 0.03 if y == 2025 else 0.02
    if not partial:
        tr.append([end, "interest", "", "", Q(float(tr_cash) * rate / 12), "EUR", "Interessi"])
    # tax set-aside accrues on Marco's work income (24%); F24 payments in June and November
    month_work = sum(r[2] for r in n26 if "Fattura" in r[1] and r[0].year == y and r[0].month == m)
    month_usd = sum(r[2] for r in rev if "Northwind" in r[1] and r[0].year == y and r[0].month == m)
    bal["tax"] -= Q((month_work + month_usd * Decimal(str(usd[i]))) * Decimal("0.24"))
    if m in (6, 11) and not partial:
        pay = Q(-bal["tax"] * Decimal("0.80" if m == 6 else "0.65"))
        bal["tax"] += pay
        n(D(30), "F24 AGENZIA DELLE ENTRATE", -pay)
    if not partial:
        n26_closes.append(end)

# positions and cash rows for brokers at each quarter end and the last day
for rows, acct_units in ((tr, {"VWCE": Decimal(120)}), (ib, {"SWDA": Decimal(130), "EIMI": Decimal(120)})):
    rows.sort(key=lambda r: r[0])
    cash = Decimal(300) if rows is tr else Decimal(150)
    units = dict(acct_units)
    out = []
    marks = {e for e in ends if e.month in (3, 6, 9, 12)} | {AS_OF}
    pending = sorted(marks)
    for r in rows:
        while pending and r[0] > pending[0]:
            e = pending.pop(0)
            for c, u in units.items():
                out.append([e, "position", c, u, "", "EUR", ""])
            out.append([e, "cash", "", "", Q(cash), "EUR", ""])
        out.append(r)
        cash += r[4]
        if r[1] == "buy":
            units[r[2]] += r[3]
    for e in pending:
        for c, u in units.items():
            out.append([e, "position", c, u, "", "EUR", ""])
        out.append([e, "cash", "", "", Q(cash), "EUR", ""])
    rows[:] = out

# ── write statements in their 'native' shapes ─────────────────────────────
fineco.sort(key=lambda r: r[0])
with open(f"{OUT}/statements/giulia_fineco.csv", "w", newline="", encoding="utf-8") as fh:
    w = csv.writer(fh, delimiter=";")
    w.writerow(["Data", "Descrizione", "Entrate", "Uscite", "Saldo"])
    b = Q(5500)
    for d, desc, a in fineco:
        b += a
        assert b > 0, ("Fineco negative", d, b)
        it = lambda v: f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")  # noqa: E731
        w.writerow([d.strftime("%d/%m/%Y"), desc, it(a) if a > 0 else "", it(-a) if a < 0 else "", it(b)])
    assert b > 0
n26.sort(key=lambda r: r[0])
with open(f"{OUT}/statements/marco_n26.csv", "w", newline="", encoding="utf-8") as fh:
    w = csv.writer(fh)
    w.writerow(["Booking Date", "Value Date", "Partner Name", "Partner Iban", "Type", "Payment Reference",
                "Account Name", "Amount (EUR)", "Original Amount", "Original Currency", "Exchange Rate"])
    for d, desc, a in n26:
        name, _, refx = desc.partition(" Fattura")
        w.writerow([d.isoformat(), d.isoformat(), name.replace("Card ", ""), "IT60X0542811101000000123456" if "BONIFICO" in desc or "Fattura" in desc else "",
                    "Credit Transfer" if a > 0 else "Presentment", "Fattura" if refx is not None and "Fattura" in desc else "",
                    "Conto principale", f"{a}", "", "", ""])
closes, b, j = [], Q(6000), 0
for e in n26_closes:
    while j < len(n26) and n26[j][0] <= e:
        b += n26[j][2]
        j += 1
    assert b > 0, (e, b)
    closes.append(f"{e}={b}")
while j < len(n26):
    b += n26[j][2]
    j += 1
closes.append(f"{AS_OF}={b}")
open(f"{OUT}/statements/marco_n26_closes.txt", "w").write("\n".join(closes) + "\n")
rev.sort(key=lambda r: r[0])
with open(f"{OUT}/statements/marco_revolut_usd.csv", "w", newline="", encoding="utf-8") as fh:
    w = csv.writer(fh)
    w.writerow(["Type", "Product", "Started Date", "Completed Date", "Description", "Amount", "Fee", "Currency", "State", "Balance"])
    b = Q(1200)
    for d, desc, a in rev:
        b += a
        w.writerow(["TRANSFER" if "Transfer" in desc or "Payment" in desc else "ATM", "Current",
                    f"{d} 09:00:00", f"{d} 09:05:00", desc, f"{a}", "0.00", "USD", "COMPLETED", f"{b}"])
for name, rows in (("giulia_traderepublic", tr), ("marco_ibkr", ib)):
    with open(f"{OUT}/statements/{name}.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["date", "kind", "symbol", "quantity", "amount", "currency", "description"])
        for r in rows:
            w.writerow([r[0].isoformat()] + r[1:])
print("statements written;", len(fineco), "Fineco rows,", len(n26), "N26 rows,", len(rev), "Revolut rows")
