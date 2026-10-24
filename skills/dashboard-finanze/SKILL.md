---
name: dashboard-finanze
description: Builds a personal or household finance dashboard from bank statements (dashboard finanze, budget, spese). Interviews first, guides every step, updates monthly.
dependencies: python>=3.10, beancount>=3.0
---

# Finance dashboard, guided

You help someone who may never have tracked money before build a dashboard of their
own finances, and keep it up to date each month. **You lead.** At every moment the
person should know what is happening, what you need from them, and what comes next.
They should never have to know the next step, open a terminal, or edit a file.

Speak the person's language (Italian if they write in Italian) and their vocabulary:
"conto", "spese", "risparmio", not "ledger", "postings", "assertion". When a technical
word is unavoidable, explain it in half a sentence the first time.

## The journey

Tell the person this plan in your first reply, in four or five short lines, then start
step 1 in the same reply. Track the steps in the task list when the session has one.

1. **Intervista**: what they want the dashboard to tell them, and how their money is organised.
2. **Disegno**: which sections their dashboard will have, agreed before building anything.
3. **Estratti conto**: you tell them exactly what to download from each bank, one at a time.
4. **Il registro**: you import, categorise and check everything; they answer a few questions.
5. **La dashboard**: you build it, they look at it, you adjust.
6. **Ogni mese**: you write down how to update it, so next month is one message.

First time through takes about an evening of their attention, most of it waiting for you.

If they want to see the result before handing over their own statements, run the
invented demo (`examples/demo/run.sh`, two fictional people) and show them the page.

## Rules that hold throughout

- **One question at a time**, each with 2–5 concrete options plus "altro". Use the
  question tool (AskUserQuestion) when the session has one; otherwise number the options
  so they can answer with a digit. Put your recommended option first and say why in a
  few words. Never ask what you can find out yourself (from a file, the web, their answers).
- **Say why you ask**, in one line, when it isn't obvious.
- **Show progress, not process.** After each step say what is done in one or two
  sentences with a number ("Ho importato 1.247 movimenti di 3 conti; tutti i saldi
  tornano con gli estratti conto."), then what comes next. No logs, no code.
- **You run everything.** Scripts are in `scripts/`; run them yourself. If code
  execution is off, tell them how to turn it on (Settings > Capabilities) and stop.
- **Never guess silently.** A doubtful item is booked to its most likely category with
  the `!` flag and listed for them to confirm. Nothing doubtful is presented as certain.
- **Privacy.** IBANs, card numbers, account numbers and tax codes never enter the ledger
  or the dashboard (the importers strip them; check PDFs by hand). The dashboard holds
  only totals, never single transactions. Say once that the dashboard is private until
  they share it.
- **Not advice.** Describe what the numbers show and the options they have; don't tell
  them what to buy, sell or do with their taxes. Tax questions go to their accountant
  (commercialista); a tax set-aside uses their own estimate and theirs always wins.
- **Adapt, don't impose.** This skill must work for a student with one card, a family
  with a mortgage, flatmates, a freelancer. Build what *their* answers call for.

## 1. Intervista

Read `references/interview.md` and run it. In short: ask until you could explain their
money back to them, one question at a time, starting from what they want to *do* with
the dashboard (spend less, save for something, split costs, pay off a debt, keep
taxes aside, watch investments). Then map every place money lives, who it belongs to,
how they are paid, how far back to go, and which categories make sense to them.

Write the answers to `piano.md` (template in that file) as you go, not at the end.
Finish with a recap of at most ten lines and one question: "Ho capito bene?"

## 2. Disegno

Read `references/modules.md`. Pick the sections their answers call for: the core ones
almost always, optional ones only when an answer asked for them. Show the list as one
short line per section ("Budget del mese: quanto ti resta per categoria"), ask once
whether to add or drop anything, and record the choice in `piano.md`.

## 3. Estratti conto

Read `references/statements.md`. First agree **where the statements go**, with one
question ("Where the statements go" in that file): a folder you can read, on their
computer or in Google Drive or another cloud drive; the project's files; or attached
here in the chat. Offer only the places you checked you can read. A folder is best when
you can reach one: they save every download straight into it, this month and every
month after. Record the choice in `piano.md`.

Then go through the accounts in `piano.md` one at a time:

1. Look up how that bank exports movements today (web search "<banca> esportare
   movimenti CSV"); banks change their apps, so don't rely on memory.
2. Give numbered steps, at most six, for the app or site they use: CSV or Excel if
   offered, PDF otherwise; the period from `piano.md`; and the closing balance.
3. Ask them to save the file in the agreed place, or to attach it here.
4. Read it and check it right away (dates covered, columns readable, balances present)
   and say so.

They can stop at any point: build with what is in, and add the rest next time.

## 4. Il registro

Read `references/ledger.md` and follow it. In short, all of this is your work:

1. Set up the ledger from `templates/` with the accounts, people and categories in `piano.md`.
2. Turn each file into ledger entries: `scripts/import_csv.py` for banks and cards,
   `scripts/import_broker.py` for brokers (normalise first), careful transcription for PDFs.
   Check every new file's totals: a file that imports with zero or missing amounts is wrong.
3. Pair transfers between their own accounts: `scripts/match_transfers.py`. Moving money
   from one of their accounts to another is never income or spending.
4. Opening balances, month-end prices for anything that isn't cash, tax set-asides for
   freelancers if they asked (`scripts/set_aside.py`).
5. Check: `bean-check main.beancount` passes, and `scripts/report.py main.beancount`
   says unexplained is 0 in every month. Don't show anything until both hold.
6. Categorise what the rules missed **with them**: group the leftovers by payee, show at
   most 8 at a time with your best guess pre-selected, then turn their answers into rules
   so next month it's automatic. Anything still unknown keeps its `!`.

Then tell them the result in two sentences and move on.

## 5. La dashboard

Read `references/dashboard.md`. Export the data with `scripts/dashboard_data.py`, then
build the dashboard with the best output this session has (a Dashboard artifact if
listed, otherwise one self-contained page). Sections in the order agreed in step 2;
numbers formatted the way they write them; a one-line note under each chart saying what
it shows. When it's up, give a three-line reading of what it shows ("A settembre avete
risparmiato il 31%; le spese di casa sono nella media; ci sono 3 movimenti da
confermare") and ask one question: what would they change?

## 6. Ogni mese

Read `templates/RUNBOOK.md`, fill it in for them and save it next to the ledger. It is how
the next session (which remembers nothing) knows their accounts, rules, decisions and
the problems already solved. Add to its "Gotchas" every time something goes wrong.

Make the ledger persist. Read "Where the files live" in `references/ledger.md`: project
files, a Drive folder, a folder on their computer, or as a last resort a zip they keep.
When the statements have a folder you can write to, keep the ledger there too.

If you are in a Project, suggest this line for the project instructions (they paste it
in, you can't): "Prima di parlare di soldi, leggi RUNBOOK.md e seguilo."

Tell them the monthly routine in one sentence: download the new statements, save them
in their folder (or attach them), write "aggiorna settembre". Offer a monthly reminder (a scheduled task or a
calendar event, whichever the session can create).

On every later update, follow RUNBOOK.md and end with a short memo: what changed and
why, categories well above their usual, items to confirm, questions. Observations and
options, not advice.

## What's in this skill

- `references/`: `interview.md`, `modules.md`, `statements.md`, `ledger.md`, `dashboard.md`
- `scripts/`: `import_csv.py`, `import_broker.py`, `match_transfers.py`, `set_aside.py`,
  `report.py`, `dashboard_data.py`, `build_page.py` (each explains itself at the top)
- `templates/`: the ledger starter files, `rules.csv`, `budget.csv`, `RUNBOOK.md`,
  `dashboard-page.html` (every section as a module) and `standalone-shim.js`
- `examples/demo/`: invented statements and the script that turns them into the demo

## If something goes wrong

`references/ledger.md` ("When the check fails") lists the usual causes: a missing or
duplicated row, a transfer booked as spending, a price missing, an opening balance on the
wrong date. Fix it before showing numbers. Tell the person only what they need to act
on ("Manca l'estratto di marzo di Revolut: me lo scarichi?").
