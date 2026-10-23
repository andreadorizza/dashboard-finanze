# Demo: Giulia e Marco (dati inventati)

Statements of an invented couple, January 2024 to 21 October 2026, in the shapes real
exports come in: an Italian bank CSV with `;` and decimal commas (Fineco-style), an N26
export without balances (closing balances in `marco_n26_closes.txt`), a Revolut USD
export, and two broker statements already normalised. `ledger/` holds what the
interview would have produced: accounts, opening balances, invented month-end prices,
rules, budget.

`bash examples/demo/run.sh` imports everything, pairs the transfers, sets aside
Marco's taxes, checks the balances (unexplained is 0 in every month) and writes the
dashboard data plus a self-contained `finanze-demo.html`.

Use it to show someone what they'll get before asking for their own statements.
Nothing in it is real: names, companies, amounts and prices are made up.
`make_statements.py` regenerates the statements.
