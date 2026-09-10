"""Exact-match place lookup against the local India gazetteer.

The upstream geocoder answers a question ORCA never asks. It searches the world,
matches loosely and ranks by population, so "goa" resolves to Genoa in Italy and
"panaji" to a town in Guatemala -- neither of which is in India, and neither of
which the user meant. The advisory then reports live readings for the wrong
hemisphere while looking entirely confident.

This module resolves Indian places first, from the catalogue built by
``backend/data/build_gazetteer.py``: every state, district, sub-district, town
and village in the GeoNames India dump, indexed under its official spelling, its
transliterations and its native-script spellings.

Two properties matter more than coverage:

* **Exact match only.** A key either equals a name in the catalogue or it does
  not. With half a million villages in the index, fuzzy matching would find a
  hamlet for almost any word typed, which is the failure being fixed, not a
  feature.
* **Deterministic ranking.** Where a name is shared -- there are several places
  called Goa -- the state beats the district beats the village, and population
  breaks the remaining tie.

The database is opened read-only and queried through an index, so the process
holds a connection rather than the catalogue itself. When the file is absent
(nobody ran the build) every lookup returns ``None`` and the caller falls back
to the upstream geocoder.
"""

from __future__ import annotations

import logging
import os
import sqlite3
import threading
from typing import Any, Dict, Optional

from backend.data.build_gazetteer import DEFAULT_DB, normalize

logger = logging.getLogger("orca.gazetteer")

GAZETTEER_PATH = os.getenv("ORCA_GAZETTEER_PATH", DEFAULT_DB)

# One connection per thread: sqlite3 objects are not safe to share across
# threads, and FastAPI runs sync work in a thread pool.
_local = threading.local()
_missing_logged = False


def _connect() -> Optional[sqlite3.Connection]:
    global _missing_logged

    conn = getattr(_local, "conn", None)
    if conn is not None:
        return conn

    if not os.path.exists(GAZETTEER_PATH):
        if not _missing_logged:
            _missing_logged = True
            logger.warning(
                "India gazetteer not found at %s; place lookup falls back to the "
                "upstream geocoder. Build it with "
                "`python backend/data/build_gazetteer.py`.",
                GAZETTEER_PATH,
            )
        return None

    try:
        conn = sqlite3.connect(
            f"file:{GAZETTEER_PATH}?mode=ro", uri=True, check_same_thread=False
        )
    except sqlite3.Error as exc:
        logger.warning("Could not open the gazetteer at %s: %s", GAZETTEER_PATH, exc)
        return None

    _local.conn = conn
    return conn


def is_available() -> bool:
    """Whether local lookup can answer at all."""
    return _connect() is not None


_QUERY = """
    SELECT p.name, p.admin1, p.fcode, p.lat, p.lon, p.population
      FROM alias a
      JOIN place p ON p.id = a.place_id
     WHERE a.key = ?
     ORDER BY p.rank DESC, a.is_primary DESC, p.population DESC, p.id ASC
     LIMIT 1
"""


def lookup(phrase: str) -> Optional[Dict[str, Any]]:
    """Resolve a phrase to an Indian place, or return None.

    ``None`` means "this catalogue does not have that name", not "no such
    place": the caller still tries the upstream geocoder afterwards, which is
    what keeps questions about Dhaka or the Gulf of Aden answerable.
    """
    conn = _connect()
    if conn is None:
        return None

    key = normalize(phrase or "")
    if len(key) < 3:
        return None

    try:
        row = conn.execute(_QUERY, (key,)).fetchone()
    except sqlite3.Error as exc:
        logger.warning("Gazetteer query failed for %r: %s", phrase, exc)
        return None

    if not row:
        return None

    name, admin1, fcode, lat, lon, population = row
    return {
        "name": name,
        # A state has no state above it; its own name is the right label.
        "admin1": admin1 or name,
        "country": "India",
        "country_code": "IN",
        "feature_code": fcode,
        "latitude": lat,
        "longitude": lon,
        "population": population,
    }
