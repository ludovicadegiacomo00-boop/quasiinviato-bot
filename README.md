# quasiinviato-bot

Pubblica in automatico su Instagram i post di Quasi inviato.

- `posts.json`: la coda dei post (testo con *parola* evidenziata, tema day/night, orario finto, didascalia, data di uscita, stato).
- `render.py`: crea le immagini 1080×1350 nello stile del brand.
- `publish.py`: pubblica con l'API ufficiale di Instagram i post arrivati alla loro ora.
- `.github/workflows/pubblica.yml`: esegue tutto ogni 30 minuti, gratis, su GitHub Actions.

Configurazione: vedi `CONFIGURAZIONE.md`.
