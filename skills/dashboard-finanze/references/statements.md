# Getting the statements

The person is often non-technical and has never exported a statement. Make each one a
small, finished task: one account, clear steps, a check, done.

## For each account

1. **Find today's steps.** Search the web ("<banca> esportare movimenti CSV", "<banca>
   estratto conto PDF app") and read the bank's own help page when there is one. Banks
   move buttons around; never send steps from memory without checking.
2. **Ask where they use the bank**: app or website. Exports are often only on the website.
3. **Give at most six numbered steps**, with the names of the buttons as the bank writes
   them. Say which format to choose, in this order of preference:
   - CSV (or Excel / XLSX): best, almost no transcription
   - PDF statement (estratto conto): fine, you transcribe it and check the totals
   - screenshots: last resort, for an app that offers nothing else
4. **Say which period**: from the start date in `piano.md` to the end of last month
   (that end date goes to the importer as `--until`). Ask for the **closing balance on
   that day** whenever the file has no running balance: the monthly PDF statement has
   it, or a screenshot of the balance. Without it nothing checks the file.
5. **Ask them to attach it** here (or drop it in the agreed folder), then **check it at
   once**: dates covered, number of rows, columns readable, balance present. Tell them
   in one line ("Ricevuto: 412 movimenti dal 1° gennaio al 30 settembre, con i saldi").

Tell them once that they can remove IBANs or card numbers before sending if they like,
and that you remove them anyway.

## Typical cases

- **Bank accounts**: most Italian online banks export CSV or Excel from the website's
  movements list (filter by date, then export). Traditional banks often give PDF only.
- **Credit cards**: a separate statement, usually monthly PDF. Card spending appears
  on the card; the monthly debit on the bank account is a transfer between their own
  accounts (bank to card), not spending: pair it like any other own transfer.
- **Payment apps** (PayPal, Satispay): export the activity; payments funded from a bank
  account show on both sides, so pair them.
- **Brokers**: the activity or transaction report (CSV if offered, otherwise PDF), plus
  the positions on the last day. Normalise it to the broker format in
  `scripts/import_broker.py` before importing.
- **Pension funds, property, cars**: no export; ask for the value once and update it
  yearly (a balance line plus an `Equity:Revaluation` entry, shown as an adjustment).
- **Cash**: not worth tracking item by item. Count withdrawals as spending ("Contanti").
- **Multi-currency accounts** (Wise, Revolut): usually one file per currency; each is the
  same account in a different currency.

## Turning files into something the importers read

- **CSV / Excel**: open it, look at the header row and a few lines. If the columns are
  among the ones `scripts/import_csv.py` knows, import directly. Otherwise write a
  normalised CSV with `date, amount, description[, balance]` (amount signed: in +, out −),
  keeping only those columns. Excel: read it with Python (openpyxl or pandas) first.
- **PDF**: extract the text, transcribe every movement into the normalised CSV, then
  **check before importing**: each month's total in, total out and closing balance must
  equal the statement's summary. If they don't, find the row. Big PDFs can come back
  truncated: ask for a smaller period or the CSV.
- **Separate in/out columns** (Entrate/Uscite, Dare/Avere) work as they are.
- **Italian numbers** (1.234,56): handled; pass `--decimal-comma` if a file has values
  like `1.234` meaning one thousand.
- **Credit-card files** where spending is positive: pass `--card`.

## Privacy

Keep only date, amount, description and balance. Never put IBANs, account or card
numbers, tax codes or addresses into the ledger, the notes or the dashboard. The
importers remove IBANs, card numbers and long reference numbers from descriptions;
check a transcribed PDF by hand for the same.
