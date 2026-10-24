# Changelog

## 1.1.0 (2026-10-24)

- Statements can come from a folder: on the person's computer (Cowork, Claude Code, desktop app), in Google Drive or another cloud drive through a connector, or in the project's files. Attaching them in the chat still works.
- The skill asks once where the statements go, offers only places it checked it can read, and records the choice in `piano.md` and `RUNBOOK.md`.
- Each update reads every file in the folder (rows already imported are skipped), never moves or deletes the person's files, and keeps the ledger beside the statements when it can write there.

## 1.0.0 (2026-10-23)

- First public release: interview, sections, statements, ledger, dashboard and monthly runbook.
- Importers for bank and card CSVs and broker activity, transfer pairing, tax set-aside for freelancers.
- Dashboard as a Claude Dashboard artifact, or a single web page where that type isn't available.
- Demo with the invented statements of Giulia and Marco.
