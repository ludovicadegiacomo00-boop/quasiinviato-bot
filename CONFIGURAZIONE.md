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

## 3. Meta for Developers (gratis, circa 15 minuti)

**A. Crea l'app**
1. Vai su developers.facebook.com, accedi con il tuo Facebook e clicca **Inizia** per registrarti come sviluppatrice (chiede di confermare email o telefono).
2. Clicca **Le mie app**, poi **Crea app**. Nome: `quasiinviato-bot`.
3. Come caso d'uso scegli **Altro**, poi tipo **Business**. Crea l'app.

**B. Genera il token**
1. Apri **Strumenti**, poi **Graph API Explorer** (developers.facebook.com/tools/explorer).
2. A destra, in "App Meta", scegli `quasiinviato-bot`. In "Utente o Pagina" lascia **Token utente**.
3. In "Autorizzazioni" aggiungi: `instagram_basic`, `instagram_content_publish`, `pages_show_list`, `pages_read_engagement`, `business_management`.
4. Clicca **Generate Access Token** e, nella finestra di Facebook, autorizza la Pagina "Quasi inviato" e l'account Instagram.

**C. Rendi il token permanente**
1. Clicca l'icona (i) accanto al token, poi **Apri in Access Token Tool**.
2. In fondo clicca **Estendi token di accesso** e copia il nuovo token lungo.
3. Torna nel Graph API Explorer, incolla il token lungo nel campo "Token di accesso".
4. Nella barra della richiesta scrivi `me/accounts?fields=name,access_token,instagram_business_account` e clicca **Invia**.
5. Nel risultato, sotto "Quasi inviato", trovi:
   - `access_token`: è il **token della Pagina** (non scade) → va in `IG_TOKEN`
   - `instagram_business_account` → `id`: è l'**id dell'account Instagram** → va in `IG_USER_ID` (non usare l'altro `id`, è quello della Pagina Facebook)
6. **Verifica prima di salvare**: incolla il token della Pagina nel Debugger (developers.facebook.com/tools/debug/accesstoken). Deve risultare **Scadenza: Mai**. Se c'è una data, hai saltato il passo 2 (estendi il token) e il token morirà dopo poche ore.
7. Se ti dice che non hai app, accedi a Meta for Developers con l'account Facebook con cui hai creato `quasiinviato-bot` (in incognito, se serve confermare l'identità).

Non incollare il token in chat: mettilo direttamente su GitHub (passo 4).

## 4. Inserisci i valori su GitHub
Nel repository `quasiinviato-bot`: **Settings**, poi **Secrets and variables**, poi **Actions**.
- Scheda **Secrets**, **New repository secret**: nome `IG_USER_ID`, valore l'id dell'account Instagram.
- Ancora **New repository secret**: nome `IG_TOKEN`, valore il token della Pagina.
- Scheda **Variables**, **New repository variable**: nome `IG_HANDLE`, valore `@quasiinviato`.

Fatto. Ogni 10 minuti GitHub controlla `posts.json` e pubblica i post arrivati alla loro ora.

## Limiti da sapere
- Instagram permette al massimo circa 50 post pubblicati via API ogni 24 ore: molto più del necessario.
- Il tool pubblica post, caroselli (max 10 slide), storie e Reel.
- TikTok non è incluso: la pubblicazione automatica pubblica richiede l'approvazione dell'app da parte di TikTok.
- GitHub può ritardare i controlli programmati di qualche minuto: un post delle 21:00 può uscire alle 21:05-21:30.
