# SwahiliBot 🇰🇪🇹🇿🇺🇬 — AI Chatbot kwa Watumiaji wa Afrika

SwahiliBot ni tovuti kamili ya AI Chatbot yenye muundo maridadi (unaofanana na Claude AI), inayotumia lugha ya **Kiswahili pekee**, na yenye **injini mbili za AI** (DeepSeek na Claude) zinazochaguliwa kiotomatiki kulingana na ugumu wa swali lako — hii inasaidia kuokoa gharama za API bila kupunguza ubora wa majibu kwenye maswali magumu.

---

## 📁 Muundo wa Faili

```
swahili-ai-chatbot/
├── app.py              # Backend (Flask) - njia zote (routes) na uelekezaji wa API
├── database.py          # Usimamizi wa watumiaji, vikomo, na malipo (SQLite)
├── malipo.py             # Muunganiko na PawaPay (Mobile Money - Afrika)
├── index.html            # Ukurasa wa mbele (frontend) - chat + akaunti + malipo
├── requirements.txt      # Maktaba za Python zinazohitajika
├── .env.example           # Mfano wa mahali pa kuweka API keys/siri
├── Procfile               # Faili la kuanzisha seva kwenye Render/Railway
└── README.md               # Faili hii
```

Tovuti hii sasa ina mfumo kamili wa:
- **Ugunduzi wa lugha kiotomatiki** — mtumiaji akiandika Kiingereza, Kifaransa, n.k., bot inajibu kwa lugha hiyohiyo (Kiswahili ni chaguo-msingi endapo lugha haijulikani)
- **Akaunti za watumiaji** — usajili/kuingia kwa jina + namba ya simu + password
- **Vikomo vya ujumbe kwa siku** kulingana na mpango wa mtumiaji (Bure/Kawaida/Premium)
- **Malipo ya Mobile Money** (M-Pesa, Tigo Pesa/Mixx, Airtel Money, HaloPesa) kupitia **PawaPay**
- **AI halisi inayotumika (DeepSeek/Claude) haionyeshwi kwa mtumiaji** — ni uamuzi wa ndani wa backend pekee, hivyo washindani hawawezi kujua "chini ya kofia" tunatumia nini

---

## ✅ Kabla Hujaanza — Vitu Unavyohitaji

1. **Kompyuta yenye Python 3.9 au zaidi** iliyowekwa. (Angalia kwa kuandika `python3 --version` kwenye Terminal/Command Prompt).
2. **Funguo ya DeepSeek API** — pata bure kwa kujisajili kwenye: https://platform.deepseek.com
3. **Funguo ya Anthropic (Claude) API** — pata kwa kujisajili kwenye: https://console.anthropic.com
4. **Funguo ya PawaPay API** (kwa ajili ya malipo ya Mobile Money) — jisajili kwenye https://pawapay.io, kamilisha uthibitisho wa biashara (KYC), kisha uchukue "API Token" kwenye dashibodi yako. PawaPay inaunganisha M-Pesa, Tigo Pesa/Mixx, Airtel Money, na HaloPesa kupitia API moja katika nchi nyingi za Afrika, siyo Tanzania pekee.
5. Akaunti ya bure kwenye **Render.com** au **Railway.app** (kwa ajili ya ku-host tovuti bila malipo ya seva).

> 💡 Hujui programu? Usijali — maelekezo haya yamefuata hatua moja baada ya nyingine.

---

## 🖥️ Sehemu ya 1: Kuendesha Tovuti Kwenye Kompyuta Yako (Local)

### Hatua 1 — Pakua faili zote
Weka faili zote (`app.py`, `index.html`, `requirements.txt`, n.k.) kwenye folda moja, mfano: `swahili-ai-chatbot`.

### Hatua 2 — Fungua Terminal / Command Prompt
Nenda kwenye folda hiyo:

```bash
cd njia/ya/folda/swahili-ai-chatbot
```

### Hatua 3 — Tengeneza "Virtual Environment" (hiari lakini inashauriwa)

```bash
python3 -m venv venv
source venv/bin/activate        # Kwa Mac/Linux
venv\Scripts\activate           # Kwa Windows
```

### Hatua 4 — Sakinisha maktaba zinazohitajika

```bash
pip install -r requirements.txt
```

### Hatua 5 — Weka funguo zako za API
1. Nakili faili `.env.example` kisha ubadilishe jina kuwa `.env`
2. Fungua faili `.env` na uweke funguo zako halisi:

```
DEEPSEEK_API_KEY=sk-xxxxxxxxxxxxxxxxxxxx
ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxxxxxxxxx
PAWAPAY_API_TOKEN=xxxxxxxxxxxxxxxxxxxx
PAWAPAY_MAZINGIRA=sandbox
SECRET_KEY=badilisha-hii-kuwa-mfuatano-mrefu-wa-nasibu
SITE_URL=http://localhost:5000
```

> 💡 Kutengeneza `SECRET_KEY` salama, endesha: `python3 -c "import secrets; print(secrets.token_hex(32))"` kisha unakili matokeo yake.

> ⚠️ **MUHIMU**: Usiwahi kutuma faili la `.env` kwenye GitHub au mahali popote pa wazi. Funguo zako za API ni siri kama nywila (password).

### Hatua 6 — Anzisha seva

```bash
python3 app.py
```

Utaona ujumbe kama:
```
* Running on http://0.0.0.0:5000
```

### Hatua 7 — Fungua tovuti
Fungua kivinjari chako (Chrome, Firefox, n.k.) na nenda:

```
http://localhost:5000
```

🎉 Tovuti yako ya SwahiliBot sasa inafanya kazi!

---

## ☁️ Sehemu ya 2: Ku-host Tovuti Kwenye Render.com (Bure)

Render ni rahisi zaidi kwa Kompyuta yoyote wala huhitaji amri za ziada.

### Hatua 1 — Weka msimbo wako kwenye GitHub
1. Tengeneza akaunti bure kwenye https://github.com (kama huna)
2. Tengeneza "Repository" mpya, mfano: `swahili-ai-chatbot`
3. Pakia (upload) faili zote za mradi huu kwenye repository hiyo
   - **USIPAKIE faili la `.env`** — Render ina mahali pake pa kuweka siri (angalia Hatua 4)

### Hatua 2 — Tengeneza akaunti Render
Nenda https://render.com na ujisajili (unaweza kutumia akaunti yako ya GitHub moja kwa moja).

### Hatua 3 — Tengeneza "Web Service" mpya
1. Kwenye dashboard ya Render, bofya **New +** → **Web Service**
2. Chagua repository yako ya GitHub (`swahili-ai-chatbot`)
3. Jaza taarifa zifuatazo:
   - **Name**: `swahilibot` (au jina lolote unalotaka)
   - **Region**: chagua iliyo karibu nawe
   - **Branch**: `main`
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app`
   - **Instance Type**: `Free`

### Hatua 4 — Ongeza funguo za API (Environment Variables)
Kabla ya kubofya "Create", tembea chini hadi sehemu ya **Environment Variables** na uongeze:

| Key | Value |
|---|---|
| `DEEPSEEK_API_KEY` | funguo yako halisi ya DeepSeek |
| `ANTHROPIC_API_KEY` | funguo yako halisi ya Claude |

### Hatua 5 — Bofya "Create Web Service"
Render itaanza kujenga na kuanzisha tovuti yako. Baada ya dakika 2–5, utapata anwani (URL) kama:

```
https://swahilibot.onrender.com
```

Hiyo ndiyo tovuti yako iliyo "live" duniani kote! 🌍

---

## 🚂 Njia Mbadala: Ku-host kwenye Railway.app

1. Nenda https://railway.app na ujisajili kwa GitHub
2. Bofya **New Project** → **Deploy from GitHub repo**
3. Chagua repository yako
4. Railway itagundua `Procfile` kiotomatiki na kujenga tovuti
5. Nenda kwenye tab ya **Variables** na uongeze `DEEPSEEK_API_KEY` na `ANTHROPIC_API_KEY`
6. Bofya **Deploy** — baada ya dakika chache utapata anwani ya tovuti yako chini ya **Settings → Networking → Generate Domain**

---

## 🧠 Jinsi Injini ya Uelekezaji Inavyofanya Kazi (Oxalpha → DeepSeek → Qwen → Claude)

Kila ujumbe unaotumwa na mtumiaji huchunguzwa na `app.py` kabla ya kutumwa kwa AI. Sasa kuna **injini 4**, na **Oxalpha (bure) hujaribiwa KWANZA KABISA kwa ujumbe wote** kabla ya nyingine yoyote — hii inapunguza gharama kubwa:

| Hali ya Ujumbe | Mpangilio wa Majaribio |
|---|---|
| Ujumbe rahisi (salamu, mazungumzo ya kawaida) | Oxalpha → DeepSeek → Qwen → Claude |
| Ujumbe mgumu (code, uchambuzi wa kina, insha, ujumbe mrefu) | Oxalpha → Qwen → DeepSeek → Claude |

Injini yoyote isiyo na funguo ya API iliyowekwa kwenye `.env` inarukwa kimya kimya bila kuvuruga mzunguko — kwa hiyo unaweza kuwasha/kuzima provider yoyote kwa kuongeza au kuondoa funguo yake tu, bila kubadilisha msimbo wowote. Ukiacha zote nne wazi (bila funguo), mtumiaji atapata ujumbe wa hitilafu unaoeleweka badala ya crash.

Unaweza kubadilisha vigezo vya ugumu kwenye faili la `app.py`, sehemu yenye jina **`VIGEZO_VYA_UGUMU`** na **`KIKOMO_CHA_UREFU`**. Kupata funguo:
- **Oxalpha**: https://oxalpha.io (kupitia TokenRa - `tokenra.io/v1/chat/completions`)
- **Qwen**: https://dashscope.console.aliyun.com (Alibaba Cloud DashScope)
- **DeepSeek**: https://platform.deepseek.com
- **Claude**: https://console.anthropic.com

---

## 🆓 Kuwasha/Kuzima Malipo (`PAYMENT_ENABLED`)

Kwa sasa (`PAYMENT_ENABLED=False` kwenye `.env`), **kila mtumiaji anatumia SwahiliBot BURE bila kikomo cha ujumbe kwa siku** — vikomo vya `MIPANGO` (Bure/Kawaida/Premium) havitekelezwi kabisa, hata kama mtumiaji tayari ana ujumbe mengi zaidi ya 15 kwa siku hiyo. Hii inakuwezesha kuruhusu watu waanze kutumia bila malipo wakati unasubiri kuona muitikio wa soko.

Ukiwa tayari kuanza kutoza:

```
PAYMENT_ENABLED=True
```

Hakuna mabadiliko mengine ya msimbo yanayohitajika — vikomo vitaanza kutekelezwa mara moja, na kitufe cha "Boresha Kiwango" kitaanza kuonekana kwenye UI. Msimbo wa malipo (PawaPay) tayari upo kamili na tayari kutumika wakati wowote utakapoamua.

---

## 💳 Mfumo wa Malipo (PawaPay - Mobile Money)

Tovuti hii ina mfumo kamili wa akaunti + vikomo vya matumizi + malipo. Kila mtu (hata asiyeingia) anaweza kuona mipango yote mitatu (Bure, Kawaida, Premium) kwa kubofya **"Bei na Mipango"** kwenye sidebar. Mtumiaji akitaka kuboresha, anachagua mtandao wake (M-Pesa, Tigo Pesa/Mixx, Airtel Money, au HaloPesa) na kulipa moja kwa moja.

### Mipango ya sasa

| Mpango | Bei | Ujumbe kwa Siku |
|---|---|---|
| **Bure** | TZS 0 | 15 |
| **Kawaida** | TZS 10,000 / mwezi | 100 |
| **Premium** | TZS 15,000 / mwezi | 300 |

Unaweza kubadilisha bei na vikomo hivi kwenye faili la `database.py`, sehemu ya `MIPANGO`.

### Jinsi ya kupata Funguo ya PawaPay

1. Nenda https://pawapay.io na ujisajili kama "Merchant/Biashara"
2. Kamilisha uthibitisho wa biashara yako (KYC) - hii ni lazima kabla ya kupokea pesa halisi
3. Anza na akaunti ya **Sandbox** (majaribio, hakuna pesa halisi) kwenye https://dashboard.sandbox.pawapay.io kupata "API Token" ya majaribio
4. Iweke kwenye `.env` yako kama `PAWAPAY_API_TOKEN`, na acha `PAWAPAY_MAZINGIRA=sandbox`
5. Ukiwa tayari kupokea pesa halisi, omba akaunti ya **Live/Production** kwenye https://dashboard.pawapay.io, badilisha `PAWAPAY_API_TOKEN` kuwa ile ya live, na `PAWAPAY_MAZINGIRA=production`
6. Kwenye dashibodi yako ya PawaPay, weka "Callback URL" kuwa: `https://anwani-yako.onrender.com/api/malipo/webhook`

> 💡 **Kuhusu "Provider Codes"**: PawaPay inatumia misimbo maalum kwa kila mtandao (mfano "MPESA_TZA"). Badala ya kuandika misimbo hii moja kwa moja (ambayo inaweza kutofautiana), `malipo.py` inauliza PawaPay moja kwa moja (`/v2/active-conf`) ni mitandao gani halisi inapatikana kwenye akaunti yako, na kuilinganisha kiotomatiki na M-Pesa/Tigo/Airtel/Halotel. Hii inamaanisha mfumo "hauvunjiki" hata kama PawaPay ikibadilisha misimbo yao.

### Jinsi Malipo Yanavyofanya Kazi (Mtiririko)

1. Mtumiaji anachagua mpango (Kawaida au Premium), mtandao wake wa simu, na kuweka namba yake
2. Backend (`malipo.py`) inatuma ombi la "deposit" kwa PawaPay kupitia `/v2/deposits`
3. Mtumiaji anapokea "USSD prompt" kwenye simu yake — anaingiza PIN yake ya Mobile Money kuthibitisha
4. PawaPay inatuma "callback" (arifa) kwenye `/api/malipo/webhook` ya tovuti yako mara malipo yanapokamilika
5. Mfumo unamboresha mtumiaji kiotomatiki kwenda mpango aliolipia kwa siku 30
6. Ikiwa "callback" haijafika (mfano wakati wa majaribio kwenye `localhost`), frontend inauliza tena (`polling`) kupitia `/api/malipo/hali` hadi malipo yathibitike

> ⚠️ **MUHIMU**: Kwa "callback" (hatua 4) ifanye kazi, tovuti yako lazima iwe "live" kwenye intaneti (siyo `localhost`) na uwe umeweka "Callback URL" sahihi kwenye dashibodi ya PawaPay.

### Usalama wa Malipo

- PawaPay inatoa uwezo wa "signed callbacks" (saini za kidijitali) kwa usalama wa ziada — inashauriwa kuiwasha kwenye dashibodi yako kabla ya kwenda "live" kikamilifu.
- Kwa sasa, njia ya `/api/malipo/webhook` inathibitisha kila "callback" kwa kulinganisha `depositId` na rekodi tuliyoitengeneza sisi wenyewe kabla — hivyo mtu wa nje hawezi kuboresha akaunti ya mtu bila sisi kuwa tumeshaanzisha malipo hayo kwanza.
- Namba za simu na maelezo ya malipo yanahifadhiwa kwenye database yako ya SQLite (`swahilibot.db`) — hakikisha huna kuipakia kwenye GitHub ya wazi (public).

---

## 🕵️ Kuhusu "Injini" ya AI (DeepSeek/Claude) Kutoonekana kwa Mtumiaji

Kwa makusudi, tovuti hii **haionyeshi** kwa mtumiaji (kwenye UI) ni AI gani hasa (DeepSeek au Claude) iliyojibu ujumbe wake fulani. Uamuzi wa kuchagua kati ya hizo mbili unabaki ndani ya `app.py` pekee (unaweza kuuona kwenye logi za seva yako, siyo kwenye majibu ya API kwa mteja). Hii inasaidia kulinda taarifa za kiushindani kuhusu jinsi mfumo wako unavyofanya kazi "chini ya kofia."

---

---

## 🛠️ Kubadilisha Mwonekano (Branding)

- **Rangi**: Badilisha ndani ya `index.html`, sehemu ya `tailwind.config` (`colors.accent`, `colors.bg`, n.k.)
- **Jina la Bot**: Tafuta na ubadilishe "SwahiliBot" popote kwenye `index.html` na `app.py` (SYSTEM_PROMPT)
- **Modeli za AI**: Badilisha `DEEPSEEK_MODEL` na `CLAUDE_MODEL` kwenye `app.py` kama unataka kutumia toleo tofauti

---

## ❓ Utatuzi wa Matatizo (Troubleshooting)

**Tatizo: "DEEPSEEK_API_KEY haijawekwa"**
→ Hakikisha faili la `.env` lipo kwenye folda sahihi na lina jina sahihi (siyo `.env.example`).

**Tatizo: Tovuti inapakia lakini haitoi majibu**
→ Fungua "Developer Tools" kwenye kivinjari (F12) → tab ya "Console" uangalie hitilafu. Mara nyingi ni funguo ya API isiyo sahihi au imekwisha muda (expired).

**Tatizo: Render inasema "Application failed to respond"**
→ Hakikisha "Start Command" ni `gunicorn app:app` na `requirements.txt` ina `gunicorn`.

---

## 📜 Leseni

Mradi huu ni wako — badilisha, boresha, na utumie kama unavyotaka kwa miradi yako binafsi au ya kibiashara.

---

Imetengenezwa kwa ❤️ kwa jamii ya watumiaji wa Kiswahili barani Afrika.
