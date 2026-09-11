"""
=====================================================================
 SwahiliBot - AI Chatbot kwa Watumiaji wa Afrika
 Backend: Flask + Dual-API Routing Engine (DeepSeek + Claude)
           + Akaunti za Watumiaji + Vikomo vya Matumizi + Malipo (ZenoPay)
=====================================================================

Faili hii inashughulikia:
  1. Kuhudumia ukurasa wa mbele (index.html)
  2. Usajili/kuingia kwa watumiaji (akaunti rahisi kwa namba ya simu)
  3. Kupokea ujumbe wa mtumiaji kupitia /api/chat, kutambua lugha yake,
     kuchunguza ugumu wa ujumbe, na kuchagua DeepSeek au Claude
  4. Kudhibiti vikomo vya ujumbe kwa siku kulingana na mpango wa mtumiaji
  5. Kuanzisha na kuthibitisha malipo ya Mobile Money (M-Pesa/Tigo Pesa/
     Airtel Money) kupitia ZenoPay ili kuboresha mpango wa mtumiaji

Muundo wa majibu (API contract) umelandanishwa moja kwa moja na JS
iliyopo kwenye index.html - usibadilishe majina ya "fields" bila
kubadilisha pia index.html.
=====================================================================
"""

import os
import re
import secrets
import logging
from functools import wraps

import requests
from flask import Flask, request, jsonify, send_from_directory, session
from flask_cors import CORS
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash, check_password_hash

import database as db
import malipo

# ---------------------------------------------------------------------------
# 1. USANIDI WA AWALI (INITIAL SETUP)
# ---------------------------------------------------------------------------

load_dotenv()

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
QWEN_API_KEY = os.getenv("QWEN_API_KEY", "")

# Endapo False (chaguo-msingi kwa sasa), kila mtumiaji anatumia BURE bila
# kikomo cha malipo - vikomo vya kila siku havitekelezwi. Njia za malipo
# (PawaPay) zinabaki tayari kwenye msimbo, tayari kuwashwa wakati wowote
# kwa kubadilisha PAYMENT_ENABLED=True kwenye .env - hakuna kuandika upya
# msimbo kunakohitajika baadaye.
PAYMENT_ENABLED = os.getenv("PAYMENT_ENABLED", "False").strip().lower() == "true"

# Anwani kamili ya tovuti yako (inahitajika kwa ajili ya webhook ya ZenoPay).
# Mfano: https://swahilibot.onrender.com  (bila '/' mwishoni)
ANWANI_YA_TOVUTI = os.getenv("SITE_URL", "http://localhost:5000")

DEEPSEEK_API_URL = "https://api.deepseek.com/chat/completions"
CLAUDE_API_URL = "https://api.anthropic.com/v1/messages"
CLAUDE_API_VERSION = "2023-06-01"
OXALPHA_API_URL = os.getenv("OXALPHA_BASE_URL", "https://openrouter.ai/api/v1") + "/chat/completions"
QWEN_API_URL = os.getenv("QWEN_BASE_URL", "https://dashscope-intl.aliyuncs.com/compatible-mode/v1") + "/chat/completions"

DEEPSEEK_MODEL = "deepseek-chat"
CLAUDE_MODEL = "claude-sonnet-4-5-20250929"
OXALPHA_MODEL = os.getenv("OXALPHA_MODEL", "stealth/ox-alpha")
QWEN_MODEL = os.getenv("QWEN_MODEL", "qwen-plus")

REQUEST_TIMEOUT = 60

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger("swahilibot")

# ---------------------------------------------------------------------------
# 2. FLASK APP
# ---------------------------------------------------------------------------

app = Flask(__name__, static_folder=".", static_url_path="")

# SECRET_KEY inahitajika kuweka "session" salama (kumbukumbu ya kuingia
# kwa mtumiaji). Weka moja ya kudumu kwenye .env kabla ya kuweka live.
app.secret_key = os.getenv("SECRET_KEY", "badilisha-hii-kwenye-.env-kabla-ya-kuweka-live")

CORS(app, supports_credentials=True)

db.anzisha_database()

SYSTEM_PROMPT = (
    "Wewe ni SwahiliBot, msaidizi wa akili bandia (AI) uliyeundwa mahsusi "
    "kwa ajili ya watumiaji wa Afrika. Muhimu: tambua lugha ambayo "
    "mtumiaji ametumia kwenye ujumbe wake wa mwisho, kisha JIBU KWA LUGHA "
    "HIYOHIYO - kwa mfano, akiandika kwa Kiingereza, jibu kwa Kiingereza; "
    "akiandika kwa Kiswahili, jibu kwa Kiswahili; akiandika kwa Kifaransa, "
    "jibu kwa Kifaransa. Kama huwezi kutambua lugha kwa uhakika, tumia "
    "Kiswahili kama chaguo-msingi. Kuwa mchangamfu, mwenye heshima, "
    "sahihi, na wa msaada. Unapoandika msimbo (code), maelezo "
    "yanayouzunguka yawe kwa lugha ya mazungumzo aliyotumia mtumiaji, "
    "ila majina ya vigezo (variables) na amri za programu yabaki kama "
    "kawaida ya lugha ya programu husika."
)

# ---------------------------------------------------------------------------
# 3. INJINI YA UELEKEZAJI (DUAL-API ROUTING ENGINE)
# ---------------------------------------------------------------------------

VIGEZO_VYA_UGUMU = [
    r"\bcode\b", r"\bmsimbo\b", r"\bprogramu\b", r"\bdebug\b",
    r"\balgorithm\b", r"\balgoriz?imu\b", r"\bfunction\b", r"\bclass\b",
    r"\bpython\b", r"\bjavascript\b", r"\bhtml\b", r"\bcss\b", r"\bsql\b",
    r"\bapi\b", r"\bjson\b", r"\bregex\b", r"\bbackend\b", r"\bfrontend\b",
    r"\bandika (code|msimbo)\b", r"\btengeneza (programu|tovuti|app)\b",
    r"```",
    r"\buchambuzi wa kina\b", r"\bchambua kwa undani\b",
    r"\bchanganua\b", r"\blinganisha kwa kina\b", r"\beleza kwa undani\b",
    r"\bandika insha\b", r"\bandika ripoti\b", r"\butafiti\b",
    r"\bmkakati\b", r"\bmpango kazi\b", r"\bhesabu\b", r"\bhisabati\b",
    r"\bmuundo wa biashara\b", r"\bfundisha\b.*\bhatua kwa hatua\b",
    r"\btafsiri (ndefu|kubwa|makala|kitabu)\b",
    # Vigezo vya Kiingereza pia, kwa kuwa sasa tunajibu lugha yoyote
    r"\banalyze\b", r"\bexplain in detail\b", r"\bwrite an essay\b",
    r"\bwrite code\b", r"\bstrategy\b", r"\bcompare in depth\b",
]

UGUMU_REGEX = re.compile("|".join(VIGEZO_VYA_UGUMU), re.IGNORECASE)

KIKOMO_CHA_UREFU = 400
KIKOMO_CHA_MANENO = 70


def ni_ujumbe_mgumu(ujumbe: str) -> bool:
    if not ujumbe:
        return False
    ujumbe_safi = ujumbe.strip()
    if len(ujumbe_safi) > KIKOMO_CHA_UREFU:
        return True
    if len(ujumbe_safi.split()) > KIKOMO_CHA_MANENO:
        return True
    if UGUMU_REGEX.search(ujumbe_safi):
        return True
    return False


# ---------------------------------------------------------------------------
# 4. WATEJA WA API (DEEPSEEK / CLAUDE)
# ---------------------------------------------------------------------------

def piga_simu_deepseek(historia_ya_mazungumzo):
    if not DEEPSEEK_API_KEY:
        raise RuntimeError("DEEPSEEK_API_KEY haijawekwa kwenye faili la .env")

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
    }
    ujumbe_wote = [{"role": "system", "content": SYSTEM_PROMPT}]
    ujumbe_wote.extend(historia_ya_mazungumzo)

    payload = {
        "model": DEEPSEEK_MODEL,
        "messages": ujumbe_wote,
        "temperature": 0.7,
        "max_tokens": 1500,
    }
    jibu = requests.post(DEEPSEEK_API_URL, headers=headers, json=payload, timeout=REQUEST_TIMEOUT)
    jibu.raise_for_status()
    data = jibu.json()
    return data["choices"][0]["message"]["content"]


def piga_simu_claude(historia_ya_mazungumzo):
    if not ANTHROPIC_API_KEY:
        raise RuntimeError("ANTHROPIC_API_KEY haijawekwa kwenye faili la .env")

    headers = {
        "Content-Type": "application/json",
        "x-api-key": ANTHROPIC_API_KEY,
        "anthropic-version": CLAUDE_API_VERSION,
    }
    payload = {
        "model": CLAUDE_MODEL,
        "max_tokens": 2000,
        "system": SYSTEM_PROMPT,
        "messages": historia_ya_mazungumzo,
    }
    jibu = requests.post(CLAUDE_API_URL, headers=headers, json=payload, timeout=REQUEST_TIMEOUT)
    jibu.raise_for_status()
    data = jibu.json()
    maandishi = "".join(
        block.get("text", "") for block in data.get("content", [])
        if block.get("type") == "text"
    )
    return maandishi


def _piga_simu_openai_compatible(url, api_key, model, historia_ya_mazungumzo, jina_la_provider):
    """
    Kazi ya jumla kwa providers zote zinazotumia muundo wa 'OpenAI-compatible
    chat completions' (Oxalpha kupitia TokenRa, Qwen kupitia DashScope, na
    DeepSeek pia hutumia muundo huu huu - lakini tunaacha piga_simu_deepseek
    peke yake hapo juu ili isibadilike bila sababu).
    """
    if not api_key:
        raise RuntimeError(f"Funguo ya {jina_la_provider} haijawekwa kwenye faili la .env")

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    ujumbe_wote = [{"role": "system", "content": SYSTEM_PROMPT}]
    ujumbe_wote.extend(historia_ya_mazungumzo)

    payload = {
        "model": model,
        "messages": ujumbe_wote,
        "temperature": 0.7,
        "max_tokens": 1500,
    }
    jibu = requests.post(url, headers=headers, json=payload, timeout=REQUEST_TIMEOUT)
    jibu.raise_for_status()
    data = jibu.json()
    return data["choices"][0]["message"]["content"]


def piga_simu_oxalpha(historia_ya_mazungumzo):
    """
    Oxalpha (Ox Alpha) - injini ya BURE inayotumika kwanza kabisa kwa
    ujumbe wote (rahisi na migumu), kwa sababu haina gharama. Inafikiwa
    kupitia TokenRa (tokenra.io) - endpoint ya 'OpenAI-compatible'.
    """
    return _piga_simu_openai_compatible(OXALPHA_API_URL, OPENROUTER_API_KEY, OXALPHA_MODEL, historia_ya_mazungumzo, "Oxalpha")


def piga_simu_qwen(historia_ya_mazungumzo):
    """
    Qwen (Alibaba Cloud DashScope) - injini mbadala yenye uwezo mzuri wa
    kuchambua, hasa kwa ujumbe migumu, ikitumika endapo Oxalpha imeshindwa.
    """
    return _piga_simu_openai_compatible(QWEN_API_URL, QWEN_API_KEY, QWEN_MODEL, historia_ya_mazungumzo, "Qwen")


def zalisha_jibu_la_ai(historia_ya_mazungumzo, mgumu):
    """
    Injini kuu ya uelekezaji (routing engine), sasa na providers 4:
    Oxalpha (bure), DeepSeek (nafuu), Qwen (uwezo mzuri), na Claude
    (bora zaidi/mbadala wa mwisho kwa ujumbe migumu sana).

    Utaratibu:
      1. Oxalpha hujaribiwa KWANZA KABISA kwa ujumbe wote - ni bure.
      2. Ikishindwa, tunachagua kulingana na ugumu wa ujumbe:
         - Ujumbe rahisi -> DeepSeek, kisha Qwen kama mbadala
         - Ujumbe mgumu  -> Qwen, kisha DeepSeek kama mbadala
      3. Claude ni mbadala wa mwisho endapo zote hapo juu zimeshindwa
         (na endapo umeweka ANTHROPIC_API_KEY).

    Injini zisizo na funguo (hazijawekwa kwenye .env) huruka kimya kimya
    bila kuvuruga mzunguko - hivyo unaweza kuwasha/kuzima providers wowote
    kwa kuongeza/kuondoa funguo yake tu, bila kubadilisha msimbo.
    """
    majaribio = [("oxalpha", piga_simu_oxalpha)]
    if mgumu:
        majaribio += [("qwen", piga_simu_qwen), ("deepseek", piga_simu_deepseek)]
    else:
        majaribio += [("deepseek", piga_simu_deepseek), ("qwen", piga_simu_qwen)]
    majaribio.append(("claude", piga_simu_claude))

    hitilafu_zote = []
    for jina, fn in majaribio:
        try:
            jibu = fn(historia_ya_mazungumzo)
            return jibu, jina
        except RuntimeError as e:
            # Funguo ya provider huyu haijawekwa - ruka kimya kimya
            hitilafu_zote.append(f"{jina}: {e}")
            continue
        except requests.exceptions.RequestException as e:
            logger.warning(f"Injini '{jina}' imeshindwa: {e}")
            hitilafu_zote.append(f"{jina}: {e}")
            continue

    raise RuntimeError(
        "Injini zote za AI zimeshindwa kujibu kwa sasa. Maelezo: " + "; ".join(hitilafu_zote)
    )


# ---------------------------------------------------------------------------
# 5. VISAIDIZI VYA UTHIBITISHO (AUTH HELPERS)
# ---------------------------------------------------------------------------

def inahitaji_kuingia(fn):
    """Decorator: inazuia njia (route) isitumike bila mtumiaji kuingia."""
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if "mtumiaji_id" not in session:
            return jsonify({"error": "Tafadhali ingia kwenye akaunti yako kwanza.", "inahitaji_kuingia": True}), 401
        return fn(*args, **kwargs)
    return wrapper


def safisha_namba_ya_simu(simu: str) -> str:
    """Inasafisha namba ya simu kubaki na tarakimu pekee, mfano 0744963858."""
    tarakimu = re.sub(r"\D", "", simu or "")
    if tarakimu.startswith("255"):
        tarakimu = "0" + tarakimu[3:]
    return tarakimu


# ---------------------------------------------------------------------------
# 6. NJIA YA UKURASA WA MBELE (STATIC)
# ---------------------------------------------------------------------------

@app.route("/")
def nyumbani():
    return send_from_directory(".", "index.html")


# ---------------------------------------------------------------------------
# 7. NJIA ZA AKAUNTI (AUTH ROUTES)
# ---------------------------------------------------------------------------

@app.route("/api/jisajili", methods=["POST"])
def jisajili():
    data = request.get_json(silent=True) or {}
    jina = (data.get("jina") or "").strip()
    simu = safisha_namba_ya_simu(data.get("simu") or "")
    password = data.get("password") or ""

    if not jina or len(jina) < 2:
        return jsonify({"error": "Tafadhali weka jina lako kamili."}), 400
    if not re.match(r"^0[67]\d{8}$", simu):
        return jsonify({"error": "Namba ya simu si sahihi. Tumia mfumo: 07XXXXXXXX au 06XXXXXXXX."}), 400
    if len(password) < 4:
        return jsonify({"error": "Password iwe na herufi/tarakimu angalau 4."}), 400

    kama_ipo = db.pata_mtumiaji_kwa_simu(simu)
    if kama_ipo:
        return jsonify({"error": "Namba hii ya simu tayari imesajiliwa. Jaribu kuingia."}), 409

    password_hash = generate_password_hash(password)
    mtumiaji_id = db.tengeneza_mtumiaji(jina, simu, password_hash)
    session["mtumiaji_id"] = mtumiaji_id

    return jsonify({"sawa": True})


@app.route("/api/ingia", methods=["POST"])
def ingia():
    data = request.get_json(silent=True) or {}
    simu = safisha_namba_ya_simu(data.get("simu") or "")
    password = data.get("password") or ""

    mtumiaji = db.pata_mtumiaji_kwa_simu(simu)
    if not mtumiaji or not check_password_hash(mtumiaji["nywila_hash"], password):
        return jsonify({"error": "Namba ya simu au password si sahihi."}), 401

    session["mtumiaji_id"] = mtumiaji["id"]
    return jsonify({"sawa": True})


@app.route("/api/toka", methods=["POST"])
def toka():
    session.pop("mtumiaji_id", None)
    return jsonify({"sawa": True})


@app.route("/api/mtumiaji")
def mtumiaji_wa_sasa():
    """
    Inarudisha taarifa za mtumiaji aliyeingia (kwa ajili ya kuonyesha
    jina, mpango, na matumizi ya leo kwenye kichwa cha ukurasa).
    """
    if "mtumiaji_id" not in session:
        return jsonify({"umeingia": False})

    mtumiaji = db.sasisha_kikomo_cha_siku(session["mtumiaji_id"])
    if not mtumiaji:
        session.pop("mtumiaji_id", None)
        return jsonify({"umeingia": False})

    mpango = db.MIPANGO[mtumiaji["kiwango"]]
    return jsonify({
        "umeingia": True,
        "jina": mtumiaji["jina"],
        "simu": mtumiaji["simu"],
        "kiwango": mtumiaji["kiwango"],
        "jina_la_kiwango": mpango["jina"],
        "matumizi_ya_leo": mtumiaji["ujumbe_leo"],
        "kikomo_cha_siku": mpango["kikomo_kwa_siku"],
        "inatumika_hadi": mtumiaji["inatumika_hadi"],
        "malipo_yamewashwa": PAYMENT_ENABLED,
        "api_key": mtumiaji.get("api_key"),
    })


# ---------------------------------------------------------------------------
# 8. NJIA YA MAZUNGUMZO (CHAT) - SASA NA VIKOMO VYA MATUMIZI
# ---------------------------------------------------------------------------

@app.route("/api/chat", methods=["POST"])
def chat():
    if "mtumiaji_id" not in session:
        return jsonify({"error": "Tafadhali ingia kwenye akaunti yako kwanza.", "inahitaji_kuingia": True}), 401

    mtumiaji = db.sasisha_kikomo_cha_siku(session["mtumiaji_id"])
    if not mtumiaji:
        session.pop("mtumiaji_id", None)
        return jsonify({"error": "Akaunti haikupatikana. Tafadhali ingia tena.", "inahitaji_kuingia": True}), 401

    mpango = db.MIPANGO[mtumiaji["kiwango"]]
    if PAYMENT_ENABLED and mtumiaji["ujumbe_leo"] >= mpango["kikomo_kwa_siku"]:
        return jsonify({
            "error": (
                f"Umefikia kikomo chako cha ujumbe {mpango['kikomo_kwa_siku']} kwa leo "
                f"(Mpango wa {mpango['jina']}). Kikomo kitarudi upya kesho, au boresha "
                f"akaunti yako sasa kupata kikomo kikubwa zaidi."
            ),
            "kikomo_kimefikiwa": True,
        }), 403

    data = request.get_json(silent=True) or {}
    historia_ya_mazungumzo = data.get("messages", [])
    if not historia_ya_mazungumzo:
        return jsonify({"error": "Hakuna ujumbe uliotumwa."}), 400

    ujumbe_wa_mwisho = ""
    for m in reversed(historia_ya_mazungumzo):
        if m.get("role") == "user":
            ujumbe_wa_mwisho = m.get("content", "")
            break

    mgumu = ni_ujumbe_mgumu(ujumbe_wa_mwisho)

    try:
        jibu_la_maandishi, injini_iliyotumika = zalisha_jibu_la_ai(historia_ya_mazungumzo, mgumu)
        logger.info(f"Ujumbe {'mgumu' if mgumu else 'rahisi'} -> injini: {injini_iliyotumika}")

    except RuntimeError as e:
        logger.error(str(e))
        return jsonify({
            "error": "Samahani, kumetokea hitilafu ya kiufundi. Tafadhali jaribu tena baada ya muda mfupi."
        }), 502

    except Exception as e:
        logger.error(f"Hitilafu isiyotarajiwa: {e}")
        return jsonify({"error": "Samahani, kumetokea hitilafu isiyotarajiwa. Jaribu tena."}), 500

    db.ongeza_ujumbe_leo(mtumiaji["id"])

    # KUMBUKA: jina la "injini" (Oxalpha/DeepSeek/Qwen/Claude) HAIRUDISHWI
    # kwa mteja kwa makusudi - ni uamuzi wa ndani wa backend pekee (angalia
    # logi hapo juu). Hii inazuia washindani/wateja kujua ni AI gani halisi
    # tunayotumia nyuma ya pazia.
    return jsonify({
        "reply": jibu_la_maandishi,
        "matumizi_ya_leo": mtumiaji["ujumbe_leo"] + 1,
        "kikomo_cha_siku": mpango["kikomo_kwa_siku"],
        "malipo_yamewashwa": PAYMENT_ENABLED,
    })


# ---------------------------------------------------------------------------
# 8.5. DEVELOPER API - MTU WA NJE ANAWEZA KUTUMIA SWAHILIBOT KAMA HUDUMA
# ---------------------------------------------------------------------------

@app.route("/api/developer/generate-key", methods=["POST"])
@inahitaji_kuingia
def developer_generate_key():
    """Inatengeneza (au kubadilisha) API key ya mtumiaji kwa matumizi ya nje."""
    ufunguo = "sb_live_" + secrets.token_hex(20)
    db.weka_api_key(session["mtumiaji_id"], ufunguo)
    return jsonify({"api_key": ufunguo})


@app.route("/api/v1/chat", methods=["POST"])
def developer_public_chat():
    """
    Njia ya UMMA kwa watengenezaji wa nje - inathibitishwa kwa X-API-KEY
    badala ya session ya kuingia. Mfano wa matumizi:

        curl -X POST https://swahilibot.example.com/api/v1/chat \\
          -H "Content-Type: application/json" \\
          -H "X-API-KEY: sb_live_xxxxxxxx" \\
          -d '{"message": "Habari, unaweza kunisaidiaje?"}'
    """
    ufunguo = request.headers.get("X-API-KEY", "")
    mtumiaji = db.pata_mtumiaji_kwa_api_key(ufunguo) if ufunguo else None
    if not mtumiaji:
        return jsonify({"error": "X-API-KEY si sahihi au haipo. Tengeneza key kwenye dashibodi yako."}), 401

    data = request.get_json(silent=True) or {}
    ujumbe = (data.get("message") or "").strip()
    historia = data.get("history") or []

    if not ujumbe:
        return jsonify({"error": "Weka 'message' kwenye ombi lako (JSON body)."}), 400

    historia_kamili = list(historia) + [{"role": "user", "content": ujumbe}]
    mgumu = ni_ujumbe_mgumu(ujumbe)

    try:
        jibu_la_maandishi, _ = zalisha_jibu_la_ai(historia_kamili, mgumu)
    except RuntimeError as e:
        logger.error(str(e))
        return jsonify({"error": "Huduma haipatikani kwa sasa. Jaribu tena baadaye."}), 502

    return jsonify({"reply": jibu_la_maandishi})


# ---------------------------------------------------------------------------
# 9. NJIA ZA MALIPO (PAWAPAY - MOBILE MONEY)
# ---------------------------------------------------------------------------

@app.route("/api/malipo/mipango")
def malipo_mipango():
    """Inarudisha orodha ya mipango yote (kwa modal ya bei) - Bure ikiwemo."""
    return jsonify(db.MIPANGO)


@app.route("/api/malipo/mitandao")
def malipo_mitandao():
    """
    Inarudisha orodha ya mitandao ya simu inayopatikana kwa malipo
    (M-Pesa, Tigo/Mixx, Airtel, Halotel) - kwa ajili ya "dropdown" ya
    kuchagua mtandao kabla ya kulipa.
    """
    try:
        mitandao = malipo.pata_watoa_huduma_wa_tanzania()
    except RuntimeError as e:
        return jsonify({"error": str(e)}), 500
    except requests.exceptions.RequestException as e:
        logger.error(f"Imeshindwa kupata mitandao kutoka PawaPay: {e}")
        return jsonify({"error": "Imeshindikana kupata orodha ya mitandao. Jaribu tena."}), 502

    return jsonify(mitandao)


@app.route("/api/malipo/anzisha", methods=["POST"])
@inahitaji_kuingia
def malipo_anzisha():
    data = request.get_json(silent=True) or {}
    kiwango = data.get("kiwango")
    mtandao = data.get("mtandao")  # mfano: "mpesa", "tigo", "airtel", "halotel"
    simu_ya_malipo = safisha_namba_ya_simu(data.get("simu") or "")

    if kiwango not in ("kawaida", "premium"):
        return jsonify({"error": "Chagua mpango sahihi: 'kawaida' au 'premium'."}), 400
    if not re.match(r"^0[67]\d{8}$", simu_ya_malipo):
        return jsonify({"error": "Weka namba sahihi ya simu ya kulipia (mfano 07XXXXXXXX)."}), 400
    if not mtandao:
        return jsonify({"error": "Tafadhali chagua mtandao wako wa simu (M-Pesa, Tigo, Airtel, au Halotel)."}), 400

    try:
        mitandao = malipo.pata_watoa_huduma_wa_tanzania()
    except RuntimeError as e:
        return jsonify({"error": str(e)}), 500
    except requests.exceptions.RequestException as e:
        logger.error(f"Hitilafu ya PawaPay (mitandao): {e}")
        return jsonify({"error": "Imeshindikana kuwasiliana na mfumo wa malipo. Jaribu tena."}), 502

    taarifa_ya_mtandao = mitandao.get(mtandao)
    if not taarifa_ya_mtandao:
        return jsonify({"error": "Mtandao uliochagua hautumiki kwa sasa. Jaribu mwingine."}), 400

    mtumiaji = db.pata_mtumiaji_kwa_id(session["mtumiaji_id"])
    kiasi = db.MIPANGO[kiwango]["bei"]

    try:
        matokeo = malipo.anzisha_malipo(
            simu=simu_ya_malipo,
            kiasi=kiasi,
            provider=taarifa_ya_mtandao["provider"],
            ujumbe_kwa_mteja="SwahiliBot",
            client_reference_id=f"user{mtumiaji['id']}-{kiwango}",
        )
    except RuntimeError as e:
        return jsonify({"error": str(e)}), 500
    except requests.exceptions.RequestException as e:
        logger.error(f"Hitilafu ya PawaPay (anzisha malipo): {e}")
        return jsonify({"error": "Imeshindikana kuwasiliana na mfumo wa malipo. Jaribu tena."}), 502

    hali_ya_awali = matokeo.get("status")
    if hali_ya_awali not in ("ACCEPTED", "DUPLICATE_IGNORED"):
        sababu = (matokeo.get("failureReason") or {}).get("failureMessage", "Malipo hayakuweza kuanzishwa.")
        return jsonify({"error": sababu}), 400

    db.tengeneza_rekodi_ya_malipo(
        mtumiaji_id=mtumiaji["id"],
        order_id=matokeo["depositId"],
        kiwango=kiwango,
        kiasi=kiasi,
        simu=simu_ya_malipo,
    )

    return jsonify({
        "order_id": matokeo["depositId"],
        "ujumbe": "Ombi la malipo limetumwa. Angalia simu yako kuthibitisha malipo (utaona ujumbe wa USSD au PIN prompt).",
    })


@app.route("/api/malipo/hali")
@inahitaji_kuingia
def malipo_hali():
    """
    Frontend inaita hii mara kwa mara (polling) kuangalia kama malipo
    yamekamilika, endapo webhook haijafika bado.
    Query param: ?order_id=xxxx  (hii ni 'depositId' ya PawaPay)
    """
    order_id = request.args.get("order_id", "")
    rekodi = db.pata_malipo_kwa_order_id(order_id)
    if not rekodi or rekodi["mtumiaji_id"] != session["mtumiaji_id"]:
        return jsonify({"error": "Oda haikupatikana."}), 404

    if rekodi["hali"] == "COMPLETED":
        return jsonify({"hali": "COMPLETED"})

    try:
        matokeo = malipo.angalia_hali_ya_malipo(order_id)
    except Exception as e:
        logger.error(f"Imeshindwa kuangalia hali ya malipo: {e}")
        return jsonify({"hali": rekodi["hali"]})

    hali_mpya = (matokeo.get("data") or {}).get("status", rekodi["hali"])

    if hali_mpya == "COMPLETED" and rekodi["hali"] != "COMPLETED":
        db.sasisha_hali_ya_malipo(order_id, "COMPLETED")
        db.boresha_mpango_wa_mtumiaji(rekodi["mtumiaji_id"], rekodi["kiwango"])
    elif hali_mpya == "FAILED":
        db.sasisha_hali_ya_malipo(order_id, "FAILED")

    return jsonify({"hali": hali_mpya})


@app.route("/api/malipo/webhook", methods=["POST"])
def malipo_webhook():
    """
    PawaPay inaita njia hii moja kwa moja ("callback") mara malipo
    yanapokamilika au kushindwa. Muundo wa payload unafanana na jibu la
    'Check deposit status'.

    KUHUSU USALAMA: PawaPay inaruhusu "signed callbacks" (saini za
    kidijitali kulingana na RFC-9421) kwa usalama wa ziada - angalia
    dashibodi yako ya PawaPay kuiwezesha. Kwa sasa, njia hii inathibitisha
    kila ombi kwa kuangalia kwamba 'depositId' iliyotumwa inalingana na
    rekodi tuliyotengeneza sisi wenyewe kabla (hivyo mtu wa nje hawezi
    kuboresha akaunti bila sisi kuwa tumeshaanzisha malipo hayo kwanza).
    """
    payload = request.get_json(silent=True) or {}
    order_id = payload.get("depositId")
    hali_ya_malipo = payload.get("status")

    logger.info(f"Webhook ya PawaPay imepokewa: depositId={order_id} hali={hali_ya_malipo}")

    if not order_id:
        return jsonify({"error": "depositId haipo"}), 400

    rekodi = db.pata_malipo_kwa_order_id(order_id)
    if not rekodi:
        logger.warning(f"Webhook: oda {order_id} haipo kwenye database yetu.")
        return jsonify({"sawa": True})

    if hali_ya_malipo == "COMPLETED" and rekodi["hali"] != "COMPLETED":
        db.sasisha_hali_ya_malipo(order_id, "COMPLETED")
        db.boresha_mpango_wa_mtumiaji(rekodi["mtumiaji_id"], rekodi["kiwango"])
        logger.info(f"Mtumiaji {rekodi['mtumiaji_id']} ameboreshwa kwenda mpango '{rekodi['kiwango']}'")
    elif hali_ya_malipo == "FAILED":
        db.sasisha_hali_ya_malipo(order_id, "FAILED")

    return jsonify({"sawa": True}), 200


# ---------------------------------------------------------------------------
# 10. AFYA YA SEVA (HEALTH CHECK)
# ---------------------------------------------------------------------------

@app.route("/api/afya")
def afya():
    return jsonify({
        "hali": "sawa",
        "malipo_yamewashwa": PAYMENT_ENABLED,
        "oxalpha_key_imewekwa": bool(OPENROUTER_API_KEY),
        "deepseek_key_imewekwa": bool(DEEPSEEK_API_KEY),
        "qwen_key_imewekwa": bool(QWEN_API_KEY),
        "claude_key_imewekwa": bool(ANTHROPIC_API_KEY),
        "pawapay_key_imewekwa": bool(malipo.PAWAPAY_API_TOKEN),
        "pawapay_mazingira": malipo.PAWAPAY_MAZINGIRA,
    })


# ---------------------------------------------------------------------------
# 11. KUANZISHA SEVA (ENTRY POINT)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    bandari = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=bandari, debug=False)
