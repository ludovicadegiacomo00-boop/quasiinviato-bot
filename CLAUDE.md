# Quasi inviato (@quasiinviato) – istruzioni per Claude

Account Instagram di frasi originali "relatable". Concept: ogni frase è un messaggio scritto e mai inviato.
Logo: tre puntini "sta scrivendo…", il terzo arancio. Rispondi sempre in **italiano**.

## Brand
- Colori: crema `#F4EDE1`, nero `#14110F`, arancio `#E8571F`, grigio `#8A8178`.
- Font: Playfair Display (frasi, parola evidenziata in corsivo arancio), Inter (orario, firma).
- Formati: post 1080×1350, storie e Reel 1080×1920.
- Ogni immagine: orario in alto a sinistra (= ora reale di pubblicazione), firma in basso con puntini + @quasiinviato.

## Come funziona il tool
- `posts.json` è la coda. Ogni voce: `id`, `type` (`post` | `carousel` | `story` | `reel`), `text` (la parola tra `*asterischi*` diventa arancio corsivo), `slides` per i caroselli, `caption`, `publish_at` (ora di Roma, `YYYY-MM-DDTHH:MM`), opzionali `theme`, `keep_theme`, `format: "image"` per storie statiche.
- `render.py --due` genera le immagini/video dei post in scadenza (scacchiera crema/nero automatica, orario = ora reale di uscita).
- `publish.py` pubblica tramite Instagram Graph API (in parallelo, max 5 per esecuzione).
- `.github/workflows/pubblica.yml` gira su GitHub Actions (cron ogni 10 min + avvio manuale; input `prova` per testare senza pubblicare).
- Secrets su GitHub: `IG_USER_ID`, `IG_TOKEN` (token Pagina permanente); variabile `IG_HANDLE`. Guida: `CONFIGURAZIONE.md`.

## "Genera N post"
Quando Ludovica chiede di generare post: scrivi frasi originali, in prima persona, specifiche, con didascalia accattivante (hook + domanda/CTA + 3-5 hashtag di nicchia), aggiungile a `posts.json` senza sovrapporre orari, poi commit e push su `main`.
Slot tipici: storia 10:00, post 13:00 e 18:00, Reel 19:30 e 23:00, carosello 21:00.

## Regole di sicurezza
- **Mai** scrivere token, chiavi o password in file, commit, memoria o messaggi. Il repo è pubblico.
- Gli errori dell'API vanno sempre oscurati prima di salvarli in `posts.json`.

## Cartella `materiali/` (non va su GitHub)
Business plan, foto profilo, sondaggi e anteprime video. È esclusa da git tramite `.gitignore`.
