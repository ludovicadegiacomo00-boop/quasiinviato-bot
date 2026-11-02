# quasiinviato-bot

Pubblica in automatico su Instagram i contenuti di Quasi inviato (post, caroselli, storie e Reel).

- `posts.json`: la coda (testo con *parola* evidenziata, tipo, didascalia, data di uscita, stato; `label: "date"` per la frase del giorno).
- `render.py`: crea immagini e video nello stile del brand (post e caroselli 1080×1350, storie e Reel 1080×1920).
- `publish.py`: pubblica con l'API ufficiale di Instagram i contenuti arrivati alla loro ora.
- `.github/workflows/pubblica.yml`: esegue tutto, gratis, su GitHub Actions. Parte ogni 5 minuti da un job su cron-job.org (affidabile) e dal cron di GitHub (riserva).

Configurazione: vedi `CONFIGURAZIONE.md`. Istruzioni per Claude e scaletta settimanale: `CLAUDE.md`.
