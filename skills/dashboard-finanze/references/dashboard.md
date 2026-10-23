# Building the dashboard

## 1. Export the data

```
python3 scripts/dashboard_data.py main.beancount dash --budget budget.csv \
    --recurring-ignore recurring_ignore.txt [--split equal] [--fire-target 30000]
```

This writes only totals: per month, per category, per person, balances today, recurring
payments and the short list of items to confirm. No single transactions leave the ledger.

## 2. Prepare the page

Start from `templates/dashboard-page.html`:

1. Delete every `data-module` section they didn't choose (and the demo note), and the
   headline tiles that read a deleted module (budget, cushion...).
2. Set `CFG` at the top of the script: locale, currency, emergency-fund band, and the
   texts. If their category groups aren't called `Essenziali`, `Stile di vita` and
   `Tasse e costi`, change those names inside the calcs (`cushion`, `rule`): each `fn`
   is self-contained and can't read `CFG`.
3. Rewrite the visible text in their language and for their situation: "avete" vs "hai",
   their names, what one-offs they actually had, the FIRE yearly target if kept. Keep
   every sentence short; each chart has one note line.
4. One person: delete the `shared` module and the per-person card.

## 3. Publish it

Check which output types the session offers (with the Artifact tool, list the types).

**A Dashboard type is listed** (claude.ai on Pro and above): create a dashboard from it,
upload each CSV from `dash/` as an asset, write one `datasets/<file name>` document per
CSV (title starting "Sample" only for invented data; `updated` set; `fixed: true` since
the files are replaced at each update), `dash/meta` with their title, and the page as
`files/index.html`. Follow the type's own instructions for the details and its checks.
Each month: upload the new CSVs and update each dataset's `url`, `name` and `updated`.

**No Dashboard type**: build one self-contained page:

```
python3 scripts/build_page.py page.html dash finanze.html --title "Finanze di casa" --lang it
```

Publish `finanze.html` as an artifact if the session can, otherwise send the file: it
opens in any browser. It loads d3 from cdnjs; for a file that must work offline, add
`--d3 <local d3.min.js>`. Rebuild and republish it after each update.

Either way the dashboard starts private: tell them once, and that whoever they share it
with sees these totals.

## 4. Hand over

Three lines on what it shows right now, in plain words and with their numbers, then one
question: "Cosa cambieresti?" Typical follow-ups and what to do:

- "Togli/aggiungi X": edit the module, rebuild, republish.
- "Questa categoria è sbagliata": fix the rule, re-categorise (edit the entries), re-export.
- "Quel movimento è...": confirm it (change `!` to `*`, right category, add a rule), re-export.
- "Voglio un budget": propose one from the median of the last 6 full months, rounded up
  to the next 10; they adjust.
