#!/bin/bash
# Build the demo end to end from the invented statements of Giulia and Marco.
# Usage: bash examples/demo/run.sh [OUT_DIR]   (needs: pip install beancount)
set -e
HERE="$(cd "$(dirname "$0")" && pwd)"
S="$HERE/../../scripts"
OUT="${1:-$PWD/demo-out}"
mkdir -p "$OUT/out" "$OUT/dash"
cp -r "$HERE/ledger" "$OUT/" && : > "$OUT/ledger/transactions.beancount"
cd "$OUT"
ST="$HERE/statements"
U="--rules ledger/rules.csv --ledger ledger/main.beancount --until 2026-10-21 --unknown-out Expenses:Da-classificare --unknown-in Income:{owner}:Altro"
python3 $S/import_csv.py $ST/giulia_fineco.csv --account Assets:Giulia:Fineco $U > out/fineco.bean
python3 $S/import_csv.py $ST/marco_n26.csv --account Assets:Marco:N26 $U $(sed 's/^/--close /' $ST/marco_n26_closes.txt) > out/n26.bean
python3 $S/import_csv.py $ST/marco_revolut_usd.csv --account Assets:Marco:Revolut --currency USD $U > out/revolut.bean
python3 $S/import_broker.py $ST/giulia_traderepublic.csv --account Assets:Giulia:TradeRepublic --ledger ledger/main.beancount --interest "Income:{owner}:Interessi" --fees Expenses:Commissioni --lang it > out/tr.bean
python3 $S/import_broker.py $ST/marco_ibkr.csv --account Assets:Marco:IBKR --ledger ledger/main.beancount --fees Expenses:Commissioni --lang it > out/ibkr.bean
python3 $S/match_transfers.py out/*.bean --ledger ledger/transactions.beancount --prices ledger/prices.beancount > out/merged.txt
cat out/merged.txt >> ledger/transactions.beancount
python3 $S/set_aside.py ledger/main.beancount --income Income:Marco:Lavoro --rate 0.24 --expense Expenses:Tasse:Accantonate --liability "Liabilities:{owner}:Tasse-da-versare" >> ledger/transactions.beancount
bean-check ledger/main.beancount
python3 $S/report.py ledger/main.beancount
python3 $S/dashboard_data.py ledger/main.beancount dash --budget ledger/budget.csv --recurring-ignore ledger/recurring_ignore.txt --fire-target 30000
python3 $S/build_page.py "$HERE/../../templates/dashboard-page.html" dash finanze-demo.html --title "Finanze di casa (demo)"
