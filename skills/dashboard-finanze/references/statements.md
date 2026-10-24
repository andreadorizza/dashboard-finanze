# Getting the statements

The person is often non-technical and has never exported a statement. Make each one a
small, finished task: one account, clear steps, a check, done.

## Where the statements go

Agree this once, before the first account. Write it in `piano.md`, and later in
`RUNBOOK.md`. Ask one question, with only the places this session can actually read,
recommended first:

1. **A folder on their computer**, when you can read their files (Cowork, Claude Code,
   the desktop app with a folder connected, a local agent). Suggest one folder, such as
   `Documenti/Conti/Estratti conto`, and ask them to save each download straight into it.
2. **A Google Drive folder** (or OneDrive, Dropbox...) when a connector for it can find
   and read their files. Good for couples: both save into the same shared folder. If the
   connector is there but not connected, say in one line where to connect it (on
   claude.ai: Customize > Connectors), then wait.
3. **The project's files**, when the chat is in a Project whose files you can read: they
   add the statements to the project, and every chat in it sees them.
4. **Attached here in the chat**: always works. The fallback, and fine for one file.

Check before you offer a place: list the folder or search the drive for it, and read
one file. Don't recommend a place you couldn't read.

With a folder:

- **One folder for everything.** File names don't matter, since you tell the bank from
  the content, but suggest `<banca>-<periodo>` so they can find things.
- **Each update, read every file in it.** The importers skip rows already in the ledger,
  so a file read twice adds nothing. Note in `RUNBOOK.md` which files you read and up to
  which date each account is covered.
- **A connector gives you the text, not the file.** Write it to a file before importing,
  then compare its row count and totals with what the connector showed: a long file can
  come back cut. If a connector can't read a format, ask for that file as CSV or in the
  chat.
- **Leave their files where they are.** Don't move, rename or delete anything unless
  they ask: a shared folder can hold files your account can't move (a partner's
  uploads). Once imported, the statements can go; only the ledger matters. Tell them so.
- **Keep the ledger next to the statements** when you can write there (a `registro/`
  folder beside them). See "Where the files live" in `ledger.md`.

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
5. **Ask them to save it in the agreed place** (or attach it here), then read it and
   **check it at once**: dates covered, number of rows, columns readable, balance
   present. Tell them in one line ("Trovato: 412 movimenti dal 1° gennaio al 30
   settembre, con i saldi").

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
