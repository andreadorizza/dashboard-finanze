# The ledger

A Beancount ledger: plain text, double entry, free. Every movement is written once
with both sides (where the money left, where it went), and the bank's own balances
are written in as checks, so a missing or doubled row stops everything until it's
fixed. That is what makes the dashboard trustworthy. The person never needs to open
it; you do all of it.

Install once per session: `pip install beancount` (add `--break-system-packages` if pip
asks). Scripts are in `scripts/` (run with `python3`), templates in `templates/`.

## Files

| File | What's in it |
|---|---|
| `main.beancount` | options (currency, FIFO booking) and the list of files below |
| `accounts.beancount` | one `open` line per account and category |
| `opening.beancount` | balances on the day before the start date |
| `prices.beancount` | month-end prices and exchange rates (only if needed) |
| `<year>.beancount` | the movements, one file per year |
| `rules.csv` | how descriptions map to categories (grows every month) |
| `budget.csv` | category, group, monthly budget |
| `recurring_ignore.txt` | names that look recurring but aren't |
| `RUNBOOK.md` | how to update this ledger next time (from `templates/RUNBOOK.md`) |
| `piano.md` | the interview's decisions |

Start from `templates/`: copy every file except `dashboard-page.html`,
`standalone-shim.js` and `RUNBOOK.md` (that one comes at the end) into a `ledger/`
folder. Then make them theirs: replace `Nome` with each person's name (one block of
accounts per person), delete the accounts and categories they don't have, rename the
year file if they start in another year, fill in `opening.beancount` and remove the `; ` in front of its entry.
`bean-check main.beancount` must pass before the first import.

## Naming

- `Assets:<Persona>:<Istituto>` for accounts (`Assets:Giulia:Fineco`), `Liabilities:<Persona>:<Cosa>`
  for debts and cards (`Liabilities:Marco:Mutuo`). The second part is whose money it is;
  for a joint account use a household name (`Assets:Casa:Conto-comune`).
- `Assets:<Persona>:Transit`: one per person, for transfers between own accounts.
- `Income:<Persona>:<Tipo>` (`Income:Giulia:Stipendio`).
- `Expenses:<Categoria>[:<Dettaglio>]` (`Expenses:Casa:Affitto`): the first part is what
  the dashboard groups by. Categories are not per person: who paid is the account the
  money left.
- Names: letters, digits and hyphens, each part starting with a capital or digit
  (`Deposito-affitto`, not `deposito affitto`). Give an account a display name with
  `name: "Trade Republic"` under its `open` line.
- Each `open` line gets `kind:` = `cash`, `investment`, `receivable`, `debt`, `tax`,
  `pension` or `property`. Brokers are `investment`; cash held at a broker still counts
  as cash.
- Each security gets a `commodity` line with `kind: "security"`.

## Opening balances

Dated the **day before** the start date (start 1 January → 31 December), one entry
against `Equity:Opening-Balances`, from each statement's opening balance. Securities at
their purchase cost if known (`120 VWCE {95.00 EUR}`), otherwise at that day's price.
Foreign cash with `@@` its value in the base currency.

## Importing

For each statement file, into `out/` first:

```
python3 scripts/import_csv.py FILE --account Assets:Giulia:Fineco --rules rules.csv \
    --ledger main.beancount --until 2026-09-30 [--currency USD] [--close 2026-09-30=1234.56] \
    [--unknown-out Expenses:Da-classificare] [--unknown-in "Income:{owner}:Altro"] > out/fineco.bean
python3 scripts/import_broker.py FILE --account Assets:Marco:IBKR --ledger main.beancount --lang it > out/ibkr.bean
python3 scripts/match_transfers.py out/*.bean --ledger 2026.beancount --prices prices.beancount > out/merged.txt
```

Then append `out/merged.txt` to the year file. `--ledger main.beancount` reads every
included file, so rows already in the ledger are skipped (same `ref`) and importing a
file twice is safe. (`match_transfers.py` takes the year file, so it can tell you which
old half to delete.) Each script's docstring has the details.

- `--until` is the last day the statement covers. Always pass it: the dashboard uses it
  to know whether the month is complete.
- A file without a running balance needs `--close <last day>=<closing balance>` from the
  statement, or nothing checks it.
- Card statements: `--card` if spending is positive in the file.
- If the importer stops because it can't find the date or amount column, write a
  normalised CSV (`date,amount,description,balance`) and import that. Never let a
  file import with amounts it didn't read: check the totals of every new file.

**Transfers between own accounts** (to a savings account, to the broker, to the card,
between partners) must end up as one entry with both sides. Add a rule pointing them to
`Assets:{owner}:Transit` for each wording the banks use; `match_transfers.py` pairs the
two halves. A half whose other side isn't imported yet stays flagged `!` and pairs
next time: ask the person which account the other side is (e.g. "da quale conto paghi
la carta?") and get that statement; if it's an account they don't track, give it an
account anyway (or book the half straight to that account) so nothing stays in Transit. A transfer between two people moves net worth from one to the other; it is
not income or spending for anyone.

**One-offs**: tag the rule (or the entry) `oneoff` for money that won't repeat: a tax
refund, a bonus, the sale of a car, an inheritance. The savings rate and the projections
leave them out, so they don't flatter the numbers.

**Shared costs**: tag `shared` (rent, groceries, bills, joint holidays...). The dashboard
splits them by income over the last 12 months (`--split income`) or equally (`--split equal`).

**Freelancers**: if they want taxes set aside, after each import run
`python3 scripts/set_aside.py main.beancount --income "Income:<Nome>:Lavoro" --rate <their rate>
--expense Expenses:Tasse:Accantonate >> <year>.beancount`. Tax payments (F24) then go
to the liability with a rule, not to spending. Their accountant's rate wins.

## Categorising

`rules.csv`: `pattern,account,name,tags,direction`. The first matching row wins, so
specific rules go above general ones. `{owner}` becomes the account's person. Tags:
`shared`, `oneoff`, and `check` (book it there but keep it flagged to confirm).
The `name` column gives a clean payee ("Netflix") used by the recurring list.

After an import, list what no rule matched (entries flagged `!`), grouped by payee,
biggest first. Ask the person in batches of at most 8, your best guess pre-selected.
Turn each answer into a rule. Things that stay unknown keep the `!` and appear on the
dashboard under "Da confermare". Don't create a new category for one item: use an
existing one or ask.

## Prices (only with investments or other currencies)

One `price` line per month-end for each security and currency, in the base currency:
`2026-09-30 price VWCE 128.45 EUR`, `2026-09-30 price USD 0.8612 EUR` (EUR per 1 USD).
Get closes from a broker connector if there is one, otherwise from a reliable web source
(the exchange, the ECB for currencies). Note the source in a comment. Past months never change.

## The two checks (every time)

1. `bean-check main.beancount` prints nothing. Every statement balance agrees.
2. `python3 scripts/report.py main.beancount` ends with "unexplained is 0 in every month".

Only then export the dashboard data.

## When the check fails

- **Balance failed** on an account: a row is missing or doubled in that month, or the
  balance was for a different day (assertions are dated the day after the statement
  ends). Compare the month's totals with the statement.
- **Unexplained not 0**: a transfer booked on one side only, an opening balance dated
  inside the first month, a price missing for a currency or security, or an entry that
  moves money into an account the ledger doesn't know as the person's.
- **A transfer shows up as spending or income**: its wording isn't in the rules yet. Add
  a Transit rule and re-run the pairing.
- **Duplicates after a second import**: the bank changed a description; delete the
  duplicates and note it in the runbook's Gotchas.

## Where the files live

The next session starts from nothing, so the ledger must be somewhere it can read.
Use the first that works, and write in `RUNBOOK.md` which one. If the statements have
a folder you can write to, put the ledger there, beside them.

1. **Project files**, when this chat is in a Project and you can write to them.
2. **A folder on their computer**, when the session can reach one (Cowork, Claude Code,
   the desktop app with a folder connected).
3. **A Google Drive folder** (or another cloud drive) through a connector that can create
   and update files.
4. **Last resort**: a zip of the ledger folder, sent to them at the end of every session,
   to attach at the start of the next one. Say so clearly: without it next month
   starts over.

Statements themselves don't need to be kept: once imported, only the ledger matters.
