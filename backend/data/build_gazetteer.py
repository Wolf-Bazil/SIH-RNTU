"""Build the local India gazetteer that place lookup resolves against.

ORCA used to send every candidate phrase to the Open-Meteo geocoder. That
service is fuzzy and ranks by population worldwide, which is the wrong shape for
an Indian advisory: "goa" returned Genoa, Italy, and "panaji" returned a town in
Guatemala. The state of Goa and the city of Panaji were not in the results at
all. An advisory that quietly relocates to another continent is worse than one
that says it does not know the place.

This script builds a local, exact-match catalogue of Indian places from the
GeoNames India dump, which covers roughly 550,000 villages alongside every
state, district, sub-district and city, together with their native-script and
transliterated spellings. The result is a SQLite file, so lookup is an indexed
query rather than a dictionary held in memory -- the backend shares a small VPS
and cannot afford a few hundred megabytes of Python strings.

Run it as part of the image build (see Dockerfile) or by hand:

    python backend/data/build_gazetteer.py

The output is derived data and is not committed; if it is missing the backend
falls back to the upstream geocoder, degraded but working.

GeoNames data is licensed CC BY 4.0 (https://www.geonames.org/).
"""

from __future__ import annotations

import argparse
import io
import logging
import os
import sqlite3
import sys
import unicodedata
import urllib.request
import zipfile
from typing import Dict, Iterable, Iterator, List, Optional, Tuple

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger("orca.gazetteer.build")

DUMP_URL = "https://download.geonames.org/export/dump/IN.zip"
DUMP_MEMBER = "IN.txt"

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_DB = os.path.join(HERE, "india_places.sqlite3")

# How strongly a feature type should win when several places share a name.
# There are dozens of hamlets called Goa; the state must win, and a district
# headquarters must beat an unnamed hamlet. Anything absent from this map is a
# populated place of unremarkable type.
_RANK_BY_FCODE: Dict[str, int] = {
    "ADM1": 100,   # State or union territory
    "PPLC": 98,    # National capital
    "ADM2": 90,    # District
    "PPLA": 88,    # State capital
    "PPLA2": 80,   # District headquarters
    "ADM3": 74,    # Sub-district / taluk / tehsil
    "PPLA3": 72,
    "ADM4": 64,
    "PPLA4": 62,
    "PPL": 50,     # Ordinary village or town
    "PPLX": 44,    # Section of a populated place
    "PPLL": 42,    # Populated locality
    "PPLW": 12,    # Destroyed
    "PPLQ": 10,    # Abandoned
    "PPLH": 10,    # Historical
}
_DEFAULT_RANK = 40

# Feature classes worth keeping: P is populated places, A is administrative
# areas. Rivers, hills, temples and railway stations are not places an advisory
# is issued for, and every one of them is another chance to match a common word.
_KEEP_CLASSES = {"P", "A"}
_KEEP_A_CODES = {"ADM1", "ADM2", "ADM3", "ADM4"}

# Scripts an Indian user might type in. Alternate names outside these -- the
# Chinese, Japanese, Korean, Cyrillic, Hebrew and Thai spellings GeoNames also
# carries -- are dropped: they cannot be typed into this app in practice, and
# each one is another index row.
_KEEP_SCRIPT_RANGES: Tuple[Tuple[int, int], ...] = (
    (0x0020, 0x024F),  # Latin, including accented forms
    (0x0600, 0x06FF),  # Arabic, used for Urdu
    (0x0900, 0x097F),  # Devanagari
    (0x0980, 0x09FF),  # Bengali and Assamese
    (0x0A00, 0x0A7F),  # Gurmukhi
    (0x0A80, 0x0AFF),  # Gujarati
    (0x0B00, 0x0B7F),  # Odia
    (0x0B80, 0x0BFF),  # Tamil
    (0x0C00, 0x0C7F),  # Telugu
    (0x0C80, 0x0CFF),  # Kannada
    (0x0D00, 0x0D7F),  # Malayalam
)

# A one or two character "name" is a code or an initial, not something a user
# types to ask about the sea there.
_MIN_KEY_CHARS = 3


def normalize(text: str) -> str:
    """Fold a place name to the key form both the build and lookup use.

    Latin text is stripped of diacritics and case, so "Panāji" and "panaji" meet.
    Indic text is left composed but normalised to NFC, because decomposing it
    would separate vowel marks from their consonants and stop the two spellings
    of the same word from matching. Punctuation and repeated spaces collapse.
    """
    if not text:
        return ""

    folded = unicodedata.normalize("NFKD", text)
    kept: List[str] = []
    for ch in folded:
        if unicodedata.combining(ch):
            # Latin accents are dropped; Indic vowel signs are combining marks
            # too, but they live above U+0900 and must be kept.
            if ord(ch) < 0x0300 or ord(ch) > 0x036F:
                kept.append(ch)
            continue
        kept.append(ch)

    text = unicodedata.normalize("NFC", "".join(kept)).lower()

    out: List[str] = []
    for ch in text:
        # Indic vowel signs, the virama and the nukta are categorised as marks,
        # not letters, so `isalnum` is False for them. Dropping them would fold
        # "चेन्नई" to "च न नई" -- a consonant skeleton that collides with other
        # names and matches none of them reliably.
        if ch.isalnum() or _is_indic_mark(ch):
            out.append(ch)
        elif out and out[-1] != " ":
            out.append(" ")
    return "".join(out).strip()


def _is_indic_mark(ch: str) -> bool:
    code = ord(ch)
    return (0x0900 <= code <= 0x0D7F or 0x0600 <= code <= 0x06FF) and \
        unicodedata.category(ch) in ("Mn", "Mc")


def _in_supported_script(text: str) -> bool:
    for ch in text:
        if ch.isspace() or not ch.isalpha():
            continue
        code = ord(ch)
        if not any(lo <= code <= hi for lo, hi in _KEEP_SCRIPT_RANGES):
            return False
    return True


def download_dump(url: str = DUMP_URL) -> bytes:
    logger.info("Downloading %s", url)
    with urllib.request.urlopen(url, timeout=120) as response:  # noqa: S310
        payload = response.read()
    logger.info("Downloaded %.1f MB", len(payload) / 1e6)
    return payload


def iter_rows(archive: bytes) -> Iterator[List[str]]:
    with zipfile.ZipFile(io.BytesIO(archive)) as zf:
        with zf.open(DUMP_MEMBER) as raw:
            for line in io.TextIOWrapper(raw, encoding="utf-8"):
                fields = line.rstrip("\n").split("\t")
                if len(fields) >= 19:
                    yield fields


def _admin1_names(rows: Iterable[List[str]]) -> Dict[str, str]:
    """Map GeoNames admin1 codes to state names, from the dump's own ADM1 rows.

    Doing it from the same file keeps the build to a single download and avoids
    the two sources drifting apart between releases.
    """
    names: Dict[str, str] = {}
    for fields in rows:
        if fields[6] == "A" and fields[7] == "ADM1":
            names[fields[10]] = _short_state((fields[2] or fields[1]).strip())
    return names


# GeoNames files several states under their constitutional long form. An
# advisory reads "Nagapattinam, Tamil Nadu", not "Nagapattinam, State of Tamil
# Nadu", so the prefix is trimmed at build time rather than in every caller.
_STATE_PREFIXES = (
    "State of ",
    "Union Territory of ",
    "National Capital Territory of ",
)


def _short_state(name: str) -> str:
    for prefix in _STATE_PREFIXES:
        if name.startswith(prefix):
            return name[len(prefix):]
    return name


def build(db_path: str = DEFAULT_DB, url: str = DUMP_URL) -> int:
    archive = download_dump(url)

    # Two passes over the archive: the first collects state names so every
    # place can be labelled with the state a user would recognise, rather than
    # with the numeric admin code.
    states = _admin1_names(iter_rows(archive))
    logger.info("Found %d states and union territories", len(states))

    tmp_path = db_path + ".tmp"
    if os.path.exists(tmp_path):
        os.remove(tmp_path)

    conn = sqlite3.connect(tmp_path)
    conn.executescript(
        """
        PRAGMA journal_mode = OFF;
        PRAGMA synchronous = OFF;

        CREATE TABLE place (
            id          INTEGER PRIMARY KEY,
            name        TEXT NOT NULL,
            admin1      TEXT NOT NULL DEFAULT '',
            fcode       TEXT NOT NULL DEFAULT '',
            lat         REAL NOT NULL,
            lon         REAL NOT NULL,
            population  INTEGER NOT NULL DEFAULT 0,
            rank        INTEGER NOT NULL DEFAULT 0
        );

        CREATE TABLE alias (
            key         TEXT NOT NULL,
            place_id    INTEGER NOT NULL,
            is_primary  INTEGER NOT NULL DEFAULT 0
        );
        """
    )

    places: List[Tuple[int, str, str, str, float, float, int, int]] = []
    aliases: List[Tuple[str, int, int]] = []
    seen_alias: set = set()
    kept = 0

    for fields in iter_rows(archive):
        fclass, fcode = fields[6], fields[7]
        if fclass not in _KEEP_CLASSES:
            continue
        if fclass == "A" and fcode not in _KEEP_A_CODES:
            continue

        try:
            geoname_id = int(fields[0])
            lat, lon = float(fields[4]), float(fields[5])
            population = int(fields[14] or 0)
        except ValueError:
            continue

        # GeoNames writes the official name with scholarly diacritics
        # ("Tamil Nādu", "Gujarāt"). The plain ASCII form is the spelling an
        # advisory should print, so it is preferred for display where it exists;
        # both spellings are indexed either way.
        name = (fields[2] or fields[1]).strip() or fields[1].strip()
        if not name:
            continue

        rank = _RANK_BY_FCODE.get(fcode, _DEFAULT_RANK)
        state = states.get(fields[10], "")
        # A state is its own admin1; labelling it "Goa, Goa" reads badly. Its
        # long form is trimmed for display, while the long form stays indexed
        # below so a user who types it still finds the state.
        if fcode == "ADM1":
            state = ""
            name = _short_state(name)

        places.append((geoname_id, name, state, fcode, lat, lon, population, rank))
        kept += 1

        # Names to index: the official name, the ASCII form, and the alternate
        # spellings. Alternate spellings are what make a question typed in
        # Devanagari or Tamil resolve at all, and they carry the everyday names
        # the official record misses -- GeoNames files Panaji under "Panjim".
        # Abandoned and historical entries keep only their own two spellings:
        # they are never the answer to "is it safe there today", and their
        # transliterations are pure index weight.
        candidates = [fields[1], fields[2]]
        if rank >= _RANK_BY_FCODE["PPL"]:
            candidates.extend(a.strip() for a in fields[3].split(",") if a.strip())

        for index, candidate in enumerate(candidates):
            if not candidate or not _in_supported_script(candidate):
                continue
            key = normalize(candidate)
            if len(key) < _MIN_KEY_CHARS:
                continue
            if (key, geoname_id) in seen_alias:
                continue
            seen_alias.add((key, geoname_id))
            aliases.append((key, geoname_id, 1 if index == 0 else 0))

        if len(places) >= 50_000:
            conn.executemany("INSERT OR REPLACE INTO place VALUES (?,?,?,?,?,?,?,?)", places)
            conn.executemany("INSERT INTO alias VALUES (?,?,?)", aliases)
            places.clear()
            aliases.clear()

    conn.executemany("INSERT OR REPLACE INTO place VALUES (?,?,?,?,?,?,?,?)", places)
    conn.executemany("INSERT INTO alias VALUES (?,?,?)", aliases)

    # The index is created after the bulk load: maintaining it per row roughly
    # triples the build time.
    conn.executescript(
        """
        CREATE INDEX alias_key ON alias (key);
        ANALYZE;
        """
    )
    conn.commit()

    alias_count = conn.execute("SELECT COUNT(*) FROM alias").fetchone()[0]
    conn.close()

    os.replace(tmp_path, db_path)
    size_mb = os.path.getsize(db_path) / 1e6
    logger.info("Wrote %s: %d places, %d name keys, %.1f MB",
                db_path, kept, alias_count, size_mb)
    return kept


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default=DEFAULT_DB, help="SQLite file to write")
    parser.add_argument("--url", default=DUMP_URL, help="GeoNames dump URL")
    parser.add_argument("--skip-if-present", action="store_true",
                        help="Exit successfully when the gazetteer already exists")
    args = parser.parse_args(argv)

    if args.skip_if_present and os.path.exists(args.out):
        logger.info("%s already exists; nothing to do", args.out)
        return 0

    try:
        build(args.out, args.url)
    except Exception as exc:  # noqa: BLE001
        # A failed build must not fail the image build: without the gazetteer
        # the backend still answers through the upstream geocoder.
        logger.error("Gazetteer build failed (%s): %s", type(exc).__name__, exc)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
