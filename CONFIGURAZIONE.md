# Configurazione iniziale (una volta sola, circa 30 minuti)

Dopo questi passaggi non devi più fare niente: chiedi a Claude "genera 10 post" e il resto va da solo.

## 1. Instagram
1. Crea il profilo con l'handle scelto.
2. Impostazioni → Tipo di account → passa a **account professionale → Creator**.
3. Crea una Pagina Facebook (anche vuota) e collegala al profilo Instagram da Impostazioni → Centro gestione account.

## 2. GitHub (gratis)
1. Crea un account su github.com.
2. Crea un repository **pubblico** chiamato `quasiinviato-bot` (deve essere pubblico perché Instagram scarica le immagini da lì).
3. Dimmi il nome del repository: carico io i file.

## 3. Meta for Developers (gratis)
1. Vai su developers.facebook.com, accedi con il tuo Facebook e crea un'app di tipo "Business".
2. Aggiungi il prodotto **Instagram** (API con accesso Facebook).
3. Da "Graph API Explorer" genera un token con i permessi `instagram_basic`, `instagram_content_publish`, `pages_show_list`, `pages_read_engagement`, `business_management`.
4. Trasformalo in token della Pagina (non scade). Ti guido io in chat su questo passaggio.
5. Copia due valori: l'**id dell'account Instagram** e il **token della Pagina**.

## 4. Inserisci i due valori su GitHub
Nel repository: Settings → Secrets and variables → Actions:
- Secret `IG_USER_ID` = id dell'account Instagram
- Secret `IG_TOKEN` = token della Pagina
- Variable `IG_HANDLE` = il tuo handle, es. `@quasiinviato`

Fatto. Ogni 30 minuti GitHub controlla `posts.json` e pubblica i post arrivati alla loro ora.

## Limiti da sapere
- Instagram permette al massimo circa 50 post pubblicati via API ogni 24 ore: molto più del necessario.
- Il tool pubblica foto singole. Caroselli e Reel si possono aggiungere dopo.
- TikTok non è incluso: la pubblicazione automatica pubblica richiede l'approvazione dell'app da parte di TikTok.
- GitHub può ritardare i controlli programmati di qualche minuto: un post delle 21:00 può uscire alle 21:05-21:30.
