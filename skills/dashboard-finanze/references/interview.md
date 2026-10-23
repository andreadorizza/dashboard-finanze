# The interview

Goal: understand their money well enough to explain it back to them, and know what
their dashboard must answer. It replaces a form: you ask, listen, and decide what to
ask next. Most people answer in 10–15 questions.

## How to ask

- One question per message. 2–5 options plus "altro" (free answer). Recommended first.
- Short. "Chi c'è in questi conti?" beats a paragraph.
- Ask the next thing their last answer opened up, not the next line of this file.
- Skip what doesn't apply (no "investimenti?" to someone who said they have one card).
- Infer what you can: "Fineco" is a bank account, "Satispay" a payment app, a salary
  on the 27th is monthly. Confirm inferences in the recap, not one by one.
- If they don't know something ("non so quanto spendo"), that's fine: the data will tell.
- When they ask what you'd recommend, say it plainly with the reason in one line.
- Save each decision to `piano.md` as it is made.

## What to cover, roughly in this order

1. **Why** they want a dashboard. Offer a multi-choice and then ask which matters most:
   - capire dove vanno i soldi
   - spendere meno / restare in un budget
   - risparmiare per un obiettivo (casa, viaggio, fondo emergenza, figli)
   - dividere le spese con partner o coinquilini
   - ripagare un debito (mutuo, prestito, carta)
   - mettere da parte le tasse (partita IVA)
   - seguire investimenti / patrimonio / indipendenza finanziaria
   Their top one or two decide which dashboard sections come first.

2. **Who** the money belongs to: solo io / io e partner / famiglia / coinquilini.
   First names or nicknames for each person (they appear on the dashboard). If shared:
   which costs are shared (affitto, spesa, bollette, viaggi...) and how they split them:
   50/50, in proportion to income, or a fixed share.

3. **Where money lives** (the money map). Ask for every place, then prompt for the
   usual forgotten ones. For each: name, whose, currency, kind.
   - conti correnti, conti deposito, libretti
   - carte di credito (statement separate from the account?), prepagate
   - app di pagamento (PayPal, Satispay), buoni pasto, contanti (worth tracking? usually not)
   - broker / app di investimento, fondi pensione, cripto
   - debiti: mutuo, prestiti, finanziamenti, carte revolving
   - soldi che altri ti devono (caparre, depositi, prestiti a amici)
   - casa o auto di proprietà: only if they want net worth to include them (value it once,
     update yearly).

4. **How they get paid**: stipendio (13ª/14ª? buoni pasto?), partita IVA (irregular;
   regime? do they want taxes set aside, and at what rate their accountant estimates),
   pensione, affitti, lavoretti, aiuti dalla famiglia. Anything one-off coming up.

5. **How far back**: suggest the last 12 months (enough for real averages and the
   yearly bills, not much work). Earlier history only if they want trends; a start of
   year is fine for a quick start.

6. **Categories**: propose 10–14 based on what you've heard, grouped, and let them
   rename, merge or add. Default proposal (adapt):
   - Essenziali: Casa (affitto o mutuo, condominio), Spesa, Bollette, Trasporti, Salute
   - Stile di vita: Ristoranti e bar, Viaggi, Shopping, Abbonamenti, Svago, Regali
   - Famiglia, Animali, Istruzione: only if relevant
   - Tasse e costi: Tasse, Commissioni
   Keep it small: they can split a category later; merging is harder.

7. **Budget and goals** (only if step 1 asked for them): a monthly amount per category,
   or "proponimelo tu dai miei dati" (recommended: decide after the import, from the
   median of the last 6 full months, rounded up to the next 10).
   A goal is an amount and a date ("fondo emergenza di 6 mesi entro giugno").

8. **Investments** (only if they have any): just the total, or performance (market gain,
   allocation)? FIRE / financial independence is an optional section: offer it only if
   step 1 mentioned independence or early retirement.

9. **Rhythm**: monthly update (recommended), quarterly, or when they feel like it.
   Would they like a reminder?

10. **Anything else** they want to see. One open question at the end.

## Recap

At most ten lines: who, accounts, how they're paid, period, categories, what the
dashboard will focus on. Then: "Ho capito bene?" Correct and continue.

## `piano.md` template

```markdown
# Piano: dashboard finanze di <nomi>
Aggiornato: <data>

## Obiettivo
- <the top one or two, in their words>

## Persone
- <nome> ...; spese condivise: <quali>, divise <50/50 | in base al reddito | X/Y>

## Dove sono i soldi
| Conto | Di chi | Valuta | Tipo | Come si esporta | Note |
|---|---|---|---|---|---|

## Entrate
- <nome>: <stipendio mensile il 27 | partita IVA, accantona X% | ...>

## Periodo
- Dal <data>

## Categorie
- Essenziali: ...
- Stile di vita: ...
- Tasse e costi: ...

## Budget e obiettivi
- ...

## Sezioni della dashboard
1. ...

## Aggiornamento
- <ogni mese, promemoria il giorno X>

## Decisioni e note
- <anything decided along the way, with the date>
```
