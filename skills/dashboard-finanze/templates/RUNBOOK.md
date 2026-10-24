# Runbook: finanze di <nomi>

Read this at the start of every session about these finances, and follow it. It is how a
new session (which remembers nothing) knows what this household decided and what has
already gone wrong once. Update it at the end of every session.

## Where things are

| What | Where |
|---|---|
| Ledger | <project files `ledger/` · folder on their computer · Drive folder "…" · zip they attach> |
| Skill scripts | the `dashboard-finanze` skill, `scripts/` |
| Dashboard | <link or file name> |
| Statements | <folder on their computer "…" · Drive folder "…" · project files · attached in chat> (they can delete them once imported) |

## The household

- People: <names>. Shared costs: <which>, split <by income | equally | X/Y>.
- Base currency: <EUR>. Other currencies: <…>.
- Goal of the dashboard: <in their words>.
- Category groups: <Essenziali: … · Stile di vita: … · Tasse e costi: …>.

## Accounts and how to get each statement

| Account (ledger) | Whose | How to export | Format | Importer and options | Covered up to |
|---|---|---|---|---|---|
| Assets:<Persona>:<Istituto> | | <app/site steps, short> | CSV | import_csv.py --decimal-comma | <date> |

Update "Covered up to" after every import.

## Every update

1. Copy the ledger where you can run it; `pip install beancount`.
2. `bean-check main.beancount` passes and `report.py` says unexplained is 0, before touching anything.
3. Ask for the new statements (table above: from "covered up to" to the end of last
   month), saved where "Statements" says. With a folder, read every file in it: rows
   already in the ledger are skipped. Walk them through any export they find hard.
4. Import each file to `out/`, pair transfers, append, set aside taxes if used.
5. Categorise what the rules missed with the person (batches of at most 8); add rules.
6. Add month-end prices if they hold securities or other currencies.
7. Both checks again. Then export the data and refresh the dashboard.
8. Save the ledger back to where it lives. Update this file (coverage, decisions, gotchas).
9. Reply with a short memo: what changed and why, categories well above usual, items
   to confirm, questions. Observations and options, not advice.

## Decisions

- <date>: <decision, in a line>

## Gotchas learned

- <date>: <what went wrong, how it was fixed, how to avoid it next time>

## Never

- Put IBANs, account or card numbers, tax codes or single transactions on the dashboard.
- Book a guess as certain: use `!` and ask.
- Give financial or tax advice. Tax figures come from their accountant.
