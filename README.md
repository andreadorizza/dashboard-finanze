# dashboard-finanze

Una skill per Claude che ti costruisce la dashboard dei tuoi soldi partendo dagli estratti conto. Ti fa qualche domanda, ti dice cosa scaricare da ogni banca, mette in ordine ogni movimento e controlla che i saldi tornino al centesimo. Poi costruisce la dashboard con le sezioni che servono a te. Ogni mese la aggiorni con un messaggio.

La guida passo passo, per chi non è tecnico: [Fatti una dashboard dei tuoi conti con l'AI](https://dorizza.com/it/risorse/dashboard-conti/).

## Installala

Prima di tutto attiva l'esecuzione di codice: in Claude apri **Settings > Capabilities** e accendi **Code execution and file creation**. Le skill non partono senza.

### Claude Pro, Max, Team o Enterprise (consigliato)

Aggiungi questo repository come marketplace di plugin. Lo fai una volta sola, e da lì in poi ricevi ogni aggiornamento da solo.

1. In Claude apri **Customize > Plugins**, clicca **Add** e scegli **Add marketplace**.
2. In **Add from a repository** scrivi `andreadorizza/dashboard-finanze`.
3. Nella scheda **Discover** apri **dashboard-finanze** e clicca **Add**.

Il plugin resta nel tuo account: lo trovi nelle chat, in Cowork e in Claude Code.

### Claude gratuito

Il piano gratuito non ha i plugin, ma puoi caricare la skill a mano.

1. Scarica [dashboard-finanze.zip](https://github.com/andreadorizza/dashboard-finanze/releases/latest/download/dashboard-finanze.zip). Non serve scompattarlo.
2. In Claude apri **Customize > Skills**, clicca **+**, poi **Create skill > Upload a skill**, e carica lo zip.

Questa copia non si aggiorna da sola. Quando esce una nuova versione (le trovi in [Releases](https://github.com/andreadorizza/dashboard-finanze/releases)), elimina la skill e carica lo zip nuovo.

### Claude Code

Se hai già aggiunto il plugin su claude.ai, Claude Code lo ha già. Altrimenti, in una sessione:

```
/plugin marketplace add andreadorizza/dashboard-finanze
/plugin install dashboard-finanze@dashboard-finanze
```

Poi apri `/plugin`, vai su **Marketplaces**, scegli `dashboard-finanze` e attiva **Enable auto-update**, così ricevi gli aggiornamenti.

### Altri agenti: Codex, Cursor, Gemini CLI, GitHub Copilot, OpenCode…

La skill è una normale cartella con un `SKILL.md`, quindi funziona con ogni agente che legge le skill. La installi con [skills](https://github.com/vercel-labs/skills), un programma che la copia nella cartella giusta per il tuo agente.

Ti servono [Node.js](https://nodejs.org) 22 o più recente, per installarla, e Python 3.10 o più recente, per i conti.

1. Apri il terminale nella cartella in cui vuoi tenere i tuoi conti.
2. Lancia questo comando. Ti chiede in quale agente installarla:

   ```
   npx skills add andreadorizza/dashboard-finanze
   ```

   Per scegliere tu l'agente, senza domande, aggiungi `-a` con il suo nome e `-y`:

   | Agente | Comando |
   |---|---|
   | Codex | `npx skills add andreadorizza/dashboard-finanze -a codex -y` |
   | Cursor | `npx skills add andreadorizza/dashboard-finanze -a cursor -y` |
   | Gemini CLI | `npx skills add andreadorizza/dashboard-finanze -a gemini-cli -y` |
   | GitHub Copilot | `npx skills add andreadorizza/dashboard-finanze -a github-copilot -y` |
   | OpenCode | `npx skills add andreadorizza/dashboard-finanze -a opencode -y` |

   Gli altri nomi sono nell'[elenco degli agenti](https://github.com/vercel-labs/skills/blob/main/docs/agents.md). Con `-g` la skill vale in tutte le cartelle, non solo in questa.
3. Apri l'agente nella stessa cartella e scrivi: "Usa la skill dashboard-finanze: voglio una dashboard dei miei conti. Non sono tecnico, guidami tu."

Fuori da Claude la dashboard è una pagina web che apri nel browser.

Questa copia non si aggiorna da sola. Per avere la versione nuova, nella stessa cartella lancia `npx skills update -y`.

## Usala

Crea un progetto in Claude, per esempio "I miei conti", e lavora sempre lì: così il mese dopo Claude ritrova il registro. Poi scrivi:

```
Usa la skill dashboard-finanze: voglio una dashboard dei miei conti. Non sono tecnico, guidami tu.
```

Vuoi vedere il risultato prima di dare i tuoi estratti conto? Scrivi "fammi vedere la demo": la skill costruisce la dashboard di Giulia e Marco, una coppia inventata.

## Cosa fa

1. **Intervista**: una domanda alla volta, per capire a cosa ti serve la dashboard e dove sono i tuoi soldi.
2. **Disegno**: ti propone le sezioni e tu scegli.
3. **Estratti conto**: ti dice cosa scaricare da ogni banca, una alla volta.
4. **Registro**: importa i movimenti in [Beancount](https://beancount.github.io), riconosce i giroconti e controlla ogni saldo con quello della banca.
5. **Dashboard**: la costruisce e te la spiega in tre righe.
6. **Ogni mese**: si scrive un `RUNBOOK.md` con tutto quello che ha imparato, così il mese dopo basta "aggiorna ottobre".

## I tuoi dati

- IBAN, numeri di carta e numeri di conto non entrano né nel registro né nella dashboard.
- La dashboard mostra solo totali, mai i singoli movimenti, tranne i pochi da confermare.
- La dashboard è privata finché non la condividi.
- Non è consulenza finanziaria. Per le tasse vale quello che dice il tuo commercialista.

## Cosa c'è qui

```
.claude-plugin/          marketplace.json e plugin.json: fanno del repo un marketplace
skills/dashboard-finanze/
  SKILL.md               il percorso in sei passi
  references/            intervista, sezioni, estratti conto, registro, dashboard
  scripts/               import, giroconti, controlli, dati della dashboard
  templates/             registro di partenza, RUNBOOK.md, pagina della dashboard
  examples/demo/         gli estratti conto inventati di Giulia e Marco
tools/                   test della demo, zip, release (per chi mantiene il repo)
```

## Licenza

[MIT](LICENSE)
