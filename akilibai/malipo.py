"""
=====================================================================
 malipo.py - Muunganiko na PawaPay (Mobile Money - Tanzania na Afrika)
=====================================================================
PawaPay ni "aggregator" mmoja anayeunganisha watoa huduma wengi wa
Mobile Money (M-Pesa, Tigo Pesa/Mixx, Airtel Money, HaloPesa, MTN, n.k.)
kupitia API moja, katika nchi zaidi ya 20 za Afrika.

Nyaraka rasmi: https://docs.pawapay.io

MUHIMU KUHUSU "PROVIDER CODES":
--------------------------------
PawaPay inahitaji "provider code" mahususi (mfano "MTN_MOMO_ZMB" kwa
Zambia) kwa kila mtandao/nchi, na misimbo hii inaweza kutofautiana kidogo
kulingana na akaunti yako na nchi ulizowezeshwa. Badala ya "kubahatisha"
misimbo hii kwa Tanzania, faili hii inauliza PawaPay moja kwa moja
(endpoint ya "Active Configuration") ni watoa huduma gani wa kweli
wanapatikana kwenye akaunti yako, kisha inawalinganisha na majina
maarufu ya Kitanzania (M-Pesa, Tigo/Mixx, Airtel, Halotel) kiotomatiki.
Hii inahakikisha usanidi wako "hauvunjiki" hata kama misimbo ikibadilika.
=====================================================================
"""

import os
import re
import uuid
import time
import requests

PAWAPAY_API_TOKEN = os.getenv("PAWAPAY_API_TOKEN", "")

# "sandbox" (majaribio, hakuna pesa halisi) au "production" (pesa halisi)
PAWAPAY_MAZINGIRA = os.getenv("PAWAPAY_MAZINGIRA", "sandbox")

PAWAPAY_BASE_URL = (
    "https://api.pawapay.io"
    if PAWAPAY_MAZINGIRA == "production"
    else "https://api.sandbox.pawapay.io"
)

NCHI = "TZA"          # Tanzania (msimbo wa ISO 3166-1 alpha-3)
SARAFU = "TZS"        # Shilingi ya Tanzania
REQUEST_TIMEOUT = 30

# Ramani ya majina rahisi ya mitandao ya Kitanzania -> maneno ya kutafuta
# ndani ya "provider code"/"displayName" inayorudishwa na PawaPay. Hii
# inaepusha kutegemea msimbo mmoja maalum ambao unaweza kutofautiana.
MITANDAO_YA_TANZANIA = {
    "mpesa": {"jina": "M-Pesa (Vodacom)", "maneno_ya_kutafuta": ["MPESA", "VODACOM"]},
    "tigo": {"jina": "Tigo Pesa / Mixx", "maneno_ya_kutafuta": ["TIGO", "MIXX"]},
    "airtel": {"jina": "Airtel Money", "maneno_ya_kutafuta": ["AIRTEL"]},
    "halotel": {"jina": "HaloPesa (Halotel)", "maneno_ya_kutafuta": ["HALOTEL", "HALO"]},
}

# "Cache" rahisi ya kumbukumbu ili tusiulize PawaPay mara kwa mara
_cache_ya_watoa_huduma = {"data": None, "muda": 0}
MUDA_WA_CACHE_SEKUNDE = 3600  # saa 1


def _vichwa_vya_ombi():
    if not PAWAPAY_API_TOKEN:
        raise RuntimeError("PAWAPAY_API_TOKEN haijawekwa kwenye faili la .env")
    return {
        "Authorization": f"Bearer {PAWAPAY_API_TOKEN}",
        "Content-Type": "application/json",
    }


def tengeneza_deposit_id():
    """Inatengeneza namba ya kipekee ya muamala (UUID) - PawaPay inaihitaji."""
    return str(uuid.uuid4())


def pata_watoa_huduma_wa_tanzania(force_refresh: bool = False):
    """
    Inauliza PawaPay ni watoa huduma gani (M-Pesa, Tigo, Airtel, Halotel)
    wanaopatikana KWELI kwenye akaunti yako kwa Tanzania, kisha
    inarudisha kamusi (dict) yenye ufunguo rahisi (mfano 'mpesa') ukiwa
    umeunganishwa na "provider code" halisi ya PawaPay.

    Matokeo (mfano):
        {
            "mpesa": {"jina": "M-Pesa (Vodacom)", "provider": "MPESA_TZA", "sarafu": "TZS"},
            "tigo": {"jina": "Tigo Pesa / Mixx", "provider": "TIGO_TZA", "sarafu": "TZS"},
            ...
        }
    """
    sasa = time.time()
    if not force_refresh and _cache_ya_watoa_huduma["data"] and \
            (sasa - _cache_ya_watoa_huduma["muda"] < MUDA_WA_CACHE_SEKUNDE):
        return _cache_ya_watoa_huduma["data"]

    jibu = requests.get(
        f"{PAWAPAY_BASE_URL}/v2/active-conf",
        params={"country": NCHI, "operationType": "DEPOSIT"},
        headers=_vichwa_vya_ombi(),
        timeout=REQUEST_TIMEOUT,
    )
    jibu.raise_for_status()
    data = jibu.json()

    watoa_huduma_halisi = []
    for nchi_info in data.get("countries", []):
        if nchi_info.get("country") != NCHI:
            continue
        for mtoa in nchi_info.get("providers", []):
            watoa_huduma_halisi.append({
                "provider": mtoa.get("provider", ""),
                "displayName": mtoa.get("displayName", ""),
            })

    matokeo = {}
    for ufunguo, taarifa in MITANDAO_YA_TANZANIA.items():
        kwa_kulinganisha = " ".join(taarifa["maneno_ya_kutafuta"]).upper()
        kilichopatikana = None
        for mtoa in watoa_huduma_halisi:
            maandishi_ya_mtoa = f"{mtoa['provider']} {mtoa['displayName']}".upper()
            if any(neno in maandishi_ya_mtoa for neno in taarifa["maneno_ya_kutafuta"]):
                kilichopatikana = mtoa["provider"]
                break
        if kilichopatikana:
            matokeo[ufunguo] = {
                "jina": taarifa["jina"],
                "provider": kilichopatikana,
                "sarafu": SARAFU,
            }

    _cache_ya_watoa_huduma["data"] = matokeo
    _cache_ya_watoa_huduma["muda"] = sasa
    return matokeo


def safisha_namba_kimataifa(simu_ya_ndani: str) -> str:
    """
    PawaPay inahitaji namba ya simu kwa muundo wa kimataifa BILA '+' na
    BILA '0' ya mwanzo, mfano: '0744123456' -> '255744123456'.
    """
    tarakimu = re.sub(r"\D", "", simu_ya_ndani or "")
    if tarakimu.startswith("0"):
        tarakimu = "255" + tarakimu[1:]
    elif not tarakimu.startswith("255"):
        tarakimu = "255" + tarakimu
    return tarakimu


def anzisha_malipo(simu, kiasi, provider, ujumbe_kwa_mteja, deposit_id=None, client_reference_id=None):
    """
    Inaanzisha ombi la malipo (deposit) kwa PawaPay. Mteja atapokea
    "USSD prompt" kwenye simu yake kuthibitisha malipo kwa PIN yake.

    Parameters:
        simu (str): Namba ya simu ya ndani, mfano '0744123456'
        kiasi (int|str): Kiasi cha malipo kwa TZS
        provider (str): "Provider code" halisi ya PawaPay (kutoka
                         pata_watoa_huduma_wa_tanzania)
        ujumbe_kwa_mteja (str): Maneno 4-22 tu yanayoonekana kwa mteja
        deposit_id (str): Ukiacha wazi, itatengenezwa kiotomatiki
        client_reference_id (str): Namba yako ya ndani ya rejea (hiari)

    Returns:
        dict: {"depositId": "...", "status": "ACCEPTED"|"REJECTED"|"DUPLICATE_IGNORED", ...}
    """
    deposit_id = deposit_id or tengeneza_deposit_id()
    simu_kimataifa = safisha_namba_kimataifa(simu)

    payload = {
        "depositId": deposit_id,
        "payer": {
            "type": "MMO",
            "accountDetails": {
                "phoneNumber": simu_kimataifa,
                "provider": provider,
            },
        },
        "amount": str(kiasi),
        "currency": SARAFU,
        "customerMessage": ujumbe_kwa_mteja[:22],
    }
    if client_reference_id:
        payload["clientReferenceId"] = client_reference_id[:50]

    jibu = requests.post(
        f"{PAWAPAY_BASE_URL}/v2/deposits",
        json=payload,
        headers=_vichwa_vya_ombi(),
        timeout=REQUEST_TIMEOUT,
    )
    jibu.raise_for_status()
    matokeo = jibu.json()
    matokeo.setdefault("depositId", deposit_id)
    return matokeo


def angalia_hali_ya_malipo(deposit_id):
    """
    Inauliza PawaPay hali ya sasa ya muamala fulani.

    Returns:
        dict: {"status": "FOUND", "data": {"depositId": "...",
              "status": "COMPLETED"|"FAILED"|"PENDING"|..., ...}}
    """
    jibu = requests.get(
        f"{PAWAPAY_BASE_URL}/v2/deposits/{deposit_id}",
        headers=_vichwa_vya_ombi(),
        timeout=REQUEST_TIMEOUT,
    )
    jibu.raise_for_status()
    return jibu.json()
