"""
=====================================================================
 database.py - Usimamizi wa Watumiaji, Vikomo, na Malipo (SQLite)
=====================================================================
SQLite imechaguliwa kwa sababu:
  - Haihitaji seva ya database ya ziada (rahisi ku-host Render/Railway)
  - Inatosha kabisa kwa mradi wa kuanzia hadi maelfu ya watumiaji
  - Ikihitajika baadaye, unaweza kuhamia PostgreSQL kwa mabadiliko madogo
=====================================================================
"""

import sqlite3
import os
from datetime import datetime, timedelta

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "swahilibot.db")

# ---------------------------------------------------------------------------
# MIPANGO YA MALIPO (SUBSCRIPTION PLANS)
# ---------------------------------------------------------------------------
# Badilisha bei na vikomo hapa endapo utataka kubadilisha mipango yako.
MIPANGO = {
    "bure": {
        "jina": "Bure",
        "bei": 0,
        "maelezo": "Jaribu SwahiliBot bila malipo yoyote.",
        "kikomo_kwa_siku": 15,
        "muda_wa_siku": None,  # Haiisha
    },
    "kawaida": {
        "jina": "Kawaida",
        "bei": 10000,  # TZS kwa mwezi
        "maelezo": "Kwa matumizi ya kila siku - kazi, masomo, na mazungumzo zaidi.",
        "kikomo_kwa_siku": 100,
        "muda_wa_siku": 30,
    },
    "premium": {
        "jina": "Premium",
        "bei": 15000,  # TZS kwa mwezi
        "maelezo": "Kikomo kikubwa zaidi kwa wale wanaotumia SwahiliBot sana kila siku.",
        "kikomo_kwa_siku": 300,
        "muda_wa_siku": 30,
    },
}


def pata_muunganisho():
    """Inarudisha muunganisho mpya wa SQLite (thread-safe kwa Flask)."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def anzisha_database():
    """Inatengeneza majedwali (tables) endapo hayapo bado."""
    conn = pata_muunganisho()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS watumiaji (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            jina TEXT NOT NULL,
            simu TEXT UNIQUE NOT NULL,
            nywila_hash TEXT NOT NULL,
            kiwango TEXT NOT NULL DEFAULT 'bure',
            inatumika_hadi TEXT,
            ujumbe_leo INTEGER NOT NULL DEFAULT 0,
            tarehe_ya_leo TEXT,
            tarehe_ya_usajili TEXT NOT NULL,
            api_key TEXT UNIQUE
        )
    """)
    # Kwa database zilizokuwepo kabla ya kipengele cha Developer API:
    # ongeza safu ya api_key endapo haipo bado (haiathiri database mpya).
    try:
        conn.execute("ALTER TABLE watumiaji ADD COLUMN api_key TEXT UNIQUE")
    except sqlite3.OperationalError:
        pass  # safu tayari ipo
    conn.execute("""
        CREATE TABLE IF NOT EXISTS malipo (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            mtumiaji_id INTEGER NOT NULL,
            order_id TEXT UNIQUE NOT NULL,
            kiwango TEXT NOT NULL,
            kiasi INTEGER NOT NULL,
            simu TEXT NOT NULL,
            hali TEXT NOT NULL DEFAULT 'PENDING',
            tarehe TEXT NOT NULL,
            FOREIGN KEY (mtumiaji_id) REFERENCES watumiaji(id)
        )
    """)
    conn.commit()
    conn.close()


# ---------------------------------------------------------------------------
# WATUMIAJI (USERS)
# ---------------------------------------------------------------------------

def tengeneza_mtumiaji(jina, simu, nywila_hash):
    conn = pata_muunganisho()
    sasa = datetime.utcnow().isoformat()
    cur = conn.execute(
        """INSERT INTO watumiaji (jina, simu, nywila_hash, kiwango, tarehe_ya_usajili, tarehe_ya_leo)
           VALUES (?, ?, ?, 'bure', ?, ?)""",
        (jina, simu, nywila_hash, sasa, datetime.utcnow().date().isoformat()),
    )
    conn.commit()
    mtumiaji_id = cur.lastrowid
    conn.close()
    return mtumiaji_id


def pata_mtumiaji_kwa_simu(simu):
    conn = pata_muunganisho()
    row = conn.execute("SELECT * FROM watumiaji WHERE simu = ?", (simu,)).fetchone()
    conn.close()
    return dict(row) if row else None


def pata_mtumiaji_kwa_id(mtumiaji_id):
    conn = pata_muunganisho()
    row = conn.execute("SELECT * FROM watumiaji WHERE id = ?", (mtumiaji_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def sasisha_kikomo_cha_siku(mtumiaji_id):
    """
    Inaangalia kama siku imebadilika tangu mara ya mwisho mtumiaji
    alipotuma ujumbe; ikiwa ndio, inarejesha kihesabio (counter) kuwa 0.
    Pia inaangalia kama muda wa mpango uliolipiwa umeisha, na kumrudisha
    mtumiaji kwenye mpango wa 'bure' endapo umeisha.
    """
    mtumiaji = pata_mtumiaji_kwa_id(mtumiaji_id)
    if not mtumiaji:
        return None

    leo = datetime.utcnow().date().isoformat()
    conn = pata_muunganisho()

    # (1) Rejesha kihesabio cha siku ikiwa siku mpya imeanza
    if mtumiaji["tarehe_ya_leo"] != leo:
        conn.execute(
            "UPDATE watumiaji SET ujumbe_leo = 0, tarehe_ya_leo = ? WHERE id = ?",
            (leo, mtumiaji_id),
        )
        mtumiaji["ujumbe_leo"] = 0
        mtumiaji["tarehe_ya_leo"] = leo

    # (2) Angalia kama mpango uliolipiwa umeisha muda wake
    if mtumiaji["kiwango"] != "bure" and mtumiaji["inatumika_hadi"]:
        inatumika_hadi = datetime.fromisoformat(mtumiaji["inatumika_hadi"])
        if datetime.utcnow() > inatumika_hadi:
            conn.execute(
                "UPDATE watumiaji SET kiwango = 'bure', inatumika_hadi = NULL WHERE id = ?",
                (mtumiaji_id,),
            )
            mtumiaji["kiwango"] = "bure"
            mtumiaji["inatumika_hadi"] = None

    conn.commit()
    conn.close()
    return mtumiaji


def ongeza_ujumbe_leo(mtumiaji_id):
    conn = pata_muunganisho()
    conn.execute(
        "UPDATE watumiaji SET ujumbe_leo = ujumbe_leo + 1 WHERE id = ?",
        (mtumiaji_id,),
    )
    conn.commit()
    conn.close()


def weka_api_key(mtumiaji_id, api_key):
    """Inaweka/kubadilisha API key ya mtumiaji (Developer API)."""
    conn = pata_muunganisho()
    conn.execute("UPDATE watumiaji SET api_key = ? WHERE id = ?", (api_key, mtumiaji_id))
    conn.commit()
    conn.close()


def pata_mtumiaji_kwa_api_key(api_key):
    conn = pata_muunganisho()
    row = conn.execute("SELECT * FROM watumiaji WHERE api_key = ?", (api_key,)).fetchone()
    conn.close()
    return dict(row) if row else None


def boresha_mpango_wa_mtumiaji(mtumiaji_id, kiwango):
    """Inatumika baada ya malipo kukamilika kwa mafanikio."""
    muda = MIPANGO[kiwango]["muda_wa_siku"] or 30
    inatumika_hadi = (datetime.utcnow() + timedelta(days=muda)).isoformat()
    conn = pata_muunganisho()
    conn.execute(
        "UPDATE watumiaji SET kiwango = ?, inatumika_hadi = ? WHERE id = ?",
        (kiwango, inatumika_hadi, mtumiaji_id),
    )
    conn.commit()
    conn.close()


# ---------------------------------------------------------------------------
# MALIPO (PAYMENTS)
# ---------------------------------------------------------------------------

def tengeneza_rekodi_ya_malipo(mtumiaji_id, order_id, kiwango, kiasi, simu):
    conn = pata_muunganisho()
    conn.execute(
        """INSERT INTO malipo (mtumiaji_id, order_id, kiwango, kiasi, simu, hali, tarehe)
           VALUES (?, ?, ?, ?, ?, 'PENDING', ?)""",
        (mtumiaji_id, order_id, kiwango, kiasi, simu, datetime.utcnow().isoformat()),
    )
    conn.commit()
    conn.close()


def pata_malipo_kwa_order_id(order_id):
    conn = pata_muunganisho()
    row = conn.execute("SELECT * FROM malipo WHERE order_id = ?", (order_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def sasisha_hali_ya_malipo(order_id, hali):
    conn = pata_muunganisho()
    conn.execute("UPDATE malipo SET hali = ? WHERE order_id = ?", (hali, order_id))
    conn.commit()
    conn.close()
