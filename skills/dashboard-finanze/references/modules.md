# Dashboard sections

Pick from this list what the interview asked for. Core sections fit almost everyone;
optional ones only when an answer called for them. Fewer, clearer sections beat many.
Every section exists in `templates/dashboard-page.html` as a `data-module`, so building
a dashboard is mostly deleting what they don't need.

Data comes from `scripts/dashboard_data.py`: `monthly`, `people`, `categories`, `budget`,
`recurring`, `holdings`, `flags`, `fire`. No section ever shows single transactions,
except the short "Da confermare" list, which names each one in a few words only.

## Core

**In alto (header).** One sentence in plain words, then 4–5 tiles. Which tiles depends on
the goal from the interview: saved last month and the 12-month rate, this month's
spending against the budget, emergency fund in months, net worth with its 12-month
change, items to confirm. Swap a tile for one closer to their goal (debt left, goal %).

**Budget del mese** (`budget`, needs `budget.csv`). Spent so far this month per category
as a share of its budget, with a line at the share of the month gone. Over budget turns
critical; ahead of pace turns the second color. If they have no budget yet, offer to
propose one: for each category the median of the last 6 full months (or as many as
there are), rounded up to the next 10; they adjust it.

**Entrate e uscite** (`cashflow`). Income and spending, last 16 months, and the savings
rate over 12 months without one-offs. The current month is partial: say so.

**Dove vanno i soldi** (`categories`). Last full month per category against the median of
the six months before, with the categories well above usual highlighted. This is the
"why does this month feel expensive" answer.

**Spese fisse e abbonamenti** (`recurring`). What repeats every month, quarter or year,
with the total per month and per year; new ones, price rises and stopped ones marked.
Review the list with them the first time: drop false positives with
`recurring_ignore.txt`.

**Fondo emergenza** (`cushion`). All cash today, current accounts included (minus taxes
still owed), divided by average essential spending over the last 6 full months, against
a 3–6 month band. If they keep the emergency money in one account and want only that
counted, filter the `cushion` calc by account and say so in its note. Change the band if
they chose another.

**Patrimonio** (`networth`). Net worth over time, and what moved it each month:
savings, one-offs, market, exchange rates. The note shows the largest "unexplained":
it must read 0, and that is the proof the numbers tie out.

**Saldi di oggi** (`balances`) and **Da confermare** (`flags`). Always keep both: one is
how they check the dashboard against their banks, the other is how it gets better.

## Optional

**Regola 50/30/20** (`rule`). Essentials / lifestyle / saved as a share of net income over
12 months. Good for "spendo troppo?" without a budget. Needs category groups.

**Spese condivise** (`shared`, two or more people). Last month's shared costs: what each
paid, their fair share (by income or equal, as decided), money already passed between
them, and who owes whom to be even.

**Per persona** (`people` card inside `networth`). Each person's net worth. Couples who
keep separate accounts like it; drop it for one person.

**Obiettivi.** Not in the template: add a card per goal with a progress bar (current value
of the accounts set aside for it ÷ target), the date, and the monthly amount needed to
get there. Write the goals to `goals.csv` (name, target, deadline, account regex) and
compute progress in a `dash.calc` from `holdings`.

**Debiti.** Not in the template: for a mortgage or loan, the balance left (from `holdings`,
kind `debt`), the monthly payment (from `recurring`) and, if they know the rate, the
payoff date. Keep the maths in a `dash.calc` and say it is an estimate.

**Tasse da parte** (freelancers). The set-aside so far, what was paid, what's still owed
(holdings kind `tax`), and the next payment dates they give you. Their accountant's
figures always win.

**Investimenti** (`investments`). What they hold today and the market gain since purchase.
Needs month-end prices.

**FIRE / indipendenza finanziaria** (`fire`, an example of a niche module). Only when they
asked about financial independence or early retirement. Capital needed for their yearly
spending at a 3.5% and 4% withdrawal rate, progress and years to go at 3/5/7% real
returns, from invested assets and the last 12 months of regular savings. Run
`dashboard_data.py ... --fire-target <yearly spending>`. Always call it an estimate.

## Look

- Sections in the order of their goals; the header tile closest to their goal first.
- A note under every chart: what it shows and the period, in one line.
- Numbers in their format (it-IT: `1.234 €`, `31,5%`), months by name.
- If something is missing (a bank not imported yet), say so on the page in one line.
