# Quasi inviato (@quasiinviato) – istruzioni per Claude

Account Instagram di frasi originali "relatable". Concept: ogni frase è un messaggio scritto e mai inviato.
Logo: tre puntini "sta scrivendo…", il terzo arancio. Rispondi sempre in **italiano**.

## Brand
- Colori: crema `#F4EDE1`, nero `#14110F`, arancio `#E8571F`, grigio `#8A8178`.
- Font: Playfair Display (frasi, parola evidenziata in corsivo arancio), Inter (orario, firma).
- Formati: post 1080×1350, storie e Reel 1080×1920.
- Ogni immagine: orario in alto a sinistra (= ora reale di pubblicazione), firma in basso con puntini + @quasiinviato.
- **Template approvati da Ludovica (layout, colori, font, accenti, suono dei Reel): non cambiarli senza una sua richiesta.** Ogni modifica, presente o futura, deve restare coerente col brand e accattivante.

## Come funziona il tool
- `posts.json` è la coda. Ogni voce: `id`, `type` (`post` | `carousel` | `story` | `reel`), `text` (la parola tra `*asterischi*` diventa arancio corsivo), `slides` per i caroselli (max 10), `caption`, `publish_at` (ora di Roma, `YYYY-MM-DDTHH:MM`), opzionali `theme`, `keep_theme`, `format: "image"` per storie statiche, `label: "date"` per la frase del giorno.
- `label: "date"`: al posto dell'orario in alto a sinistra compare il giorno con la data (es. `martedì, 03.11.2026`). Vale solo per quel post.
- `render.py --due` genera le immagini/video dei post in scadenza (scacchiera crema/nero automatica per post, Reel e caroselli; le storie hanno il `theme` scritto in coda; orario = ora reale di uscita).
- `publish.py` pubblica tramite Instagram Graph API (in parallelo, max 5 per esecuzione).
- `.github/workflows/pubblica.yml` gira su GitHub Actions (avvio manuale; input `prova` per testare senza pubblicare).
- **Lancio automatico:** il cron di GitHub è inaffidabile (il 2 novembre ha saltato ore intere). Il lancio affidabile è un job su cron-job.org ogni 5 minuti che chiama `POST https://api.github.com/repos/ludovicadegiacomo00-boop/quasiinviato-bot/actions/workflows/pubblica.yml/dispatches` con body `{"ref":"main"}` e un token GitHub fine-grained (solo repo `quasiinviato-bot`, permesso Actions: read/write). Il token è salvato solo su cron-job.org e **scade dopo 1 anno (ricordare di rinnovarlo a ottobre 2027)**. Il cron di GitHub (`*/5`) resta come riserva; `concurrency` evita doppie pubblicazioni. Se i post non escono: controllare lo storico del job su cron-job.org (deve rispondere 204).
- Secrets su GitHub: `IG_USER_ID`, `IG_TOKEN` (token **di Pagina**, non scade: nel Debugger dei token deve risultare "Scadenza: Mai"); variabile `IG_HANDLE`. Guida: `CONFIGURAZIONE.md`.
- GitHub CLI installato (`C:\Program Files\GitHub CLI\gh.exe`, login già fatto): si può lanciare il workflow con `gh workflow run pubblica.yml -R ludovicadegiacomo00-boop/quasiinviato-bot`. Il token di `gh` sta nel sistema, mai nei file.

## "Genera N post"
Quando Ludovica chiede di generare post: scrivi frasi originali, in prima persona, specifiche, con didascalia accattivante (hook + domanda/CTA + 3-5 hashtag di nicchia), aggiungile a `posts.json` senza sovrapporre orari, poi commit e push su `main` (prima `git pull`: il workflow committa lo stato dei post).

### Varietà dei temi (obbligatoria)
Non fare mai due contenuti vicini sullo stesso argomento. Ruota: amore, ex, amicizia, famiglia, lavoro, scuola/università, ansia e pensieri notturni, autostima, nostalgia e primi amori, vita da adulti. Una volta a settimana (il mercoledì, carosello delle 22:30) un carosello sui **segni zodiacali**, organizzato per elementi (fuoco, terra, aria, acqua; 6 slide: copertina, 4 elementi, chiusura). Il primo post di ogni giorno è la **frase del giorno** con `label: "date"`.

### Scaletta settimanale (ora di Roma)
Dati reali (1-2 novembre 2026): i Reel portano le visualizzazioni (130-180 ciascuno) e il 71% delle interazioni; i post circa 10. Quindi più Reel, gli orari si differenziano per giorno.

| Giorno | Contenuti |
|---|---|
| Lunedì | storia 07:45, Reel 08:15, frase del giorno 13:00, Reel 18:00, carosello 22:30 |
| Martedì-Giovedì | storia 09:30, frase del giorno 10:30, Reel 13:00, post 13:30, Reel 17:30, carosello 22:30 (mercoledì = zodiaco) |
| Venerdì | storia 09:30, frase del giorno 11:00, Reel 16:00, post 18:00, carosello 23:30 |
| Sabato | storia 11:00, Reel 14:00, frase del giorno 18:00, Reel 00:30 e carosello 01:30 (notte tra sabato e domenica: primi amori, amicizie, nostalgia) |
| Domenica | storia 11:00, frase del giorno 15:00, Reel 20:00, post 21:30, carosello 22:30 (domenica sera: ansia da lunedì, nostalgia) |

I contenuti hanno tono coerente col giorno: lunedì = ricominciare, venerdì = weekend e uscite, sabato notte = nostalgia, domenica sera = malinconia. Dopo 2 settimane si rivede il ritmo con le statistiche di Instagram (Statistiche, Pubblico, orari in cui i follower sono online).

Stato: coda generata fino al 30 novembre 2026 (152 contenuti dal 3 novembre).

## Regole di sicurezza
- **Mai** scrivere token, chiavi o password in file, commit, memoria o messaggi. Il repo è pubblico.
- Gli errori dell'API vanno sempre oscurati prima di salvarli in `posts.json`.
- Se il token smette di funzionare (errore 190): ricavare un nuovo token utente nel Graph API Explorer, estenderlo, ricavare il token di Pagina con `me/accounts`, verificare "Scadenza: Mai" nel Debugger, poi aggiornare il secret `IG_TOKEN` su GitHub. Il token non va mai incollato in chat né negli screenshot.

## Cartella `materiali/` (non va su GitHub)
Business plan, foto profilo, sondaggi e anteprime video. È esclusa da git tramite `.gitignore`.
