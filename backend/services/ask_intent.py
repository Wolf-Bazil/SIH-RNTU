"""Question understanding and guardrails for the Ask ORCA endpoint.

The endpoint used to treat every question as a place name: the whole string was
handed to the geocoder, and whatever came back drove a fixed four-section
advisory. "highest cyclone chances?" geocoded to nothing, so the reply printed
the question itself under "Area:" and then listed sea readings the user had not
asked for.

This module separates the two questions that were conflated:

* *What is being asked?*  :func:`classify` sorts the question into an intent, so
  a definition, a greeting and a safety request are not all answered with a
  station readout.
* *Which water does it concern?*  :func:`extract_place` looks for a place name
  inside the sentence instead of assuming the sentence is one.

It also holds the guardrails, which are deliberately deterministic: they run
identically whether or not the language model is reachable, so a degraded ORCA
still refuses what a healthy ORCA refuses.
"""

from __future__ import annotations

import asyncio
import logging
import re
import time
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

import httpx

logger = logging.getLogger("orca.ask.intent")

GEOCODE_URL = "https://geocoding-api.open-meteo.com/v1/search"

# A question longer than this is either a paste or an attempt to bury an
# instruction in filler. The advisory needs a sentence or two, not an essay.
MAX_QUESTION_CHARS = 600

# Only the last few turns are worth carrying: the advisory is about conditions
# now, and a long transcript is mostly a way to push the system prompt out of
# the model's attention.
MAX_HISTORY_TURNS = 6
MAX_HISTORY_CHARS = 1500


class Intent(str, Enum):
    """What the user is asking for, which decides the shape of the answer."""

    ADVISORY = "advisory"          # Conditions or safety, for a place or the map station.
    EXPLAINER = "explainer"        # Marine or disaster knowledge, no specific place needed.
    CAPABILITY = "capability"      # "What can you do", "who are you".
    SMALLTALK = "smalltalk"        # Greetings and thanks.
    OUT_OF_SCOPE = "out_of_scope"  # Nothing to do with ocean, weather or disaster safety.
    UNSAFE = "unsafe"              # Prompt injection, or advice ORCA must not give.


# ---------------------------------------------------------------------------
# Guardrails
# ---------------------------------------------------------------------------

# Attempts to reach past the user turn and rewrite ORCA's instructions. Matched
# on the raw question because that is where they arrive; the reply names the
# refusal rather than silently continuing, so the behaviour is auditable.
_INJECTION_PATTERNS = [
    r"ignore\s+(?:all\s+|any\s+|the\s+)?(?:previous|prior|above|earlier)\s+(?:instruction|prompt|rule|direction)",
    r"disregard\s+(?:all\s+|any\s+|the\s+)?(?:previous|prior|above|earlier)",
    r"forget\s+(?:everything|all|your)\s+(?:you\s+)?(?:know|instruction|rule|prompt)",
    r"\byou\s+are\s+now\b.{0,40}\b(?:not|no\s+longer)\b",
    r"\b(?:system|developer)\s*(?:prompt|message)\b.{0,30}\b(?:show|print|reveal|repeat|output|ignore)",
    r"\b(?:show|print|reveal|repeat|leak)\b.{0,30}\b(?:system\s*prompt|your\s+instruction|api[_\s-]?key|secret)",
    r"\bact\s+as\s+(?:if\s+you\s+are\s+)?(?:a\s+|an\s+)?(?:dan|jailbr|unrestricted|uncensored)",
    r"\bdeveloper\s+mode\b",
    r"</?\s*(?:system|assistant)\s*>",
]

# Advice ORCA is not qualified to give. These are refused with a redirect to a
# real authority rather than answered badly.
_UNSAFE_TOPICS = [
    (r"\b(?:diagnos|prescri|dosage|medicine|symptom|treat\s+my)\b",
     "medical questions"),
    (r"\b(?:lawsuit|legal\s+advice|sue|court\s+case|attorney)\b",
     "legal questions"),
    (r"\b(?:invest|stock|share\s+price|trading|crypto|mutual\s+fund)\b",
     "financial questions"),
]

# Vocabulary that puts a question inside ORCA's remit even when no place is
# named. Kept explicit rather than learned, so the boundary is reviewable.
_DOMAIN_TERMS = {
    "ocean", "oceanic", "sea", "seas", "marine", "maritime", "coast", "coastal",
    "shore", "offshore", "beach", "bay", "gulf", "eez", "harbour", "harbor",
    "port", "tide", "tides", "tidal", "current", "currents", "swell", "surge",
    "wave", "waves", "tsunami", "sst", "salinity", "chlorophyll",
    "cyclone", "cyclones", "cyclonic", "storm", "storms", "depression",
    "hurricane", "typhoon", "squall", "gale", "landfall", "imd", "incois",
    "weather", "climate", "forecast", "rain", "rainfall", "rains", "monsoon",
    "wind", "winds", "gust", "gusts", "humidity", "temperature", "pressure",
    "flood", "flooding", "flooded", "waterlogging", "inundation", "drought",
    "heatwave", "lightning", "thunderstorm", "hail", "erosion", "disaster",
    "fish", "fishing", "fisherman", "fishermen", "fisher", "trawler", "boat",
    "boats", "vessel", "vessels", "craft", "catch", "pfz", "sail", "sailing",
    "voyage", "route", "navigation", "anchorage",
    "hazard", "risk", "risky", "danger", "dangerous", "safe", "safety",
    "warning", "alert", "alerts", "advisory", "evacuate", "evacuation",
    "shelter", "rescue", "orca",
}

# Words that look like place names to a bare geocoder but are not. Without this
# a question such as "is it safe today" would search for a town called "Safe".
_PLACE_STOPWORDS = {
    "a", "an", "the", "is", "are", "am", "was", "were", "be", "been", "being",
    "do", "does", "did", "can", "could", "will", "would", "shall", "should",
    "may", "might", "must", "have", "has", "had", "i", "we", "you", "he", "she",
    "it", "they", "me", "us", "them", "my", "our", "your", "his", "her", "its",
    "their", "this", "that", "these", "those", "there", "here", "what", "when",
    "where", "which", "who", "whom", "why", "how", "and", "or", "but", "if",
    "then", "than", "so", "because", "for", "from", "with", "without", "about",
    "into", "onto", "over", "under", "between", "of", "to", "in", "on", "at",
    "by", "as", "near", "off", "around", "close", "beside", "along", "towards",
    "toward", "outside", "inside", "across",
    "not", "no", "yes", "please", "tell", "give", "show", "explain",
    "help", "want", "need", "know", "get", "any", "some", "all", "more", "most",
    "much", "many", "very", "now", "today", "tomorrow", "yesterday", "tonight",
    "morning", "evening", "night", "week", "month", "year", "day", "days",
    "hour", "hours", "time", "next", "last", "current", "currently", "chance",
    "chances", "probability", "likely", "highest", "lowest", "best", "worst",
    "good", "bad", "level", "levels", "index", "score", "report", "update",
    "condition", "conditions", "situation", "status", "news", "area", "region",
    "place", "location", "spot", "zone", "district", "state", "country",
    "india", "indian",
}

# Domain vocabulary must never be geocoded either: "Cyclone" and "Storm" are
# both real town names somewhere, and matching one would silently relocate the
# advisory to another continent.
_PLACE_STOPWORDS |= _DOMAIN_TERMS

_GREETING_RE = re.compile(
    r"^\s*(?:hi|hey|hello|yo|namaste|namaskar|vanakkam|salaam|good\s+(?:morning|afternoon|evening)|"
    r"thanks|thank\s+you|thx|ok|okay|bye|goodbye)\b[\s!.?,]*$",
    re.IGNORECASE,
)

_CAPABILITY_RE = re.compile(
    r"\b(?:who\s+are\s+you|what\s+are\s+you|what\s+can\s+you\s+do|what\s+do\s+you\s+do|"
    r"how\s+do\s+you\s+work|what\s+is\s+orca|your\s+(?:capabilit|feature|purpose)|help\s+me\s+with\s+what)\b",
    re.IGNORECASE,
)

# A question that asks for conditions rather than for a definition. "Is it safe
# to fish off Paradip" wants readings; "what is a cyclone" does not.
_ADVISORY_RE = re.compile(
    r"\b(?:safe|safety|should\s+i|can\s+i|is\s+it|go\s+out|put\s+out|set\s+sail|venture|"
    r"right\s+now|today|tonight|tomorrow|current|currently|now|forecast|outlook|"
    r"warning|alert|advisory|risk|conditions?)\b",
    re.IGNORECASE,
)

_DEFINITION_RE = re.compile(
    r"^\s*(?:what|which|why|how|when|who|explain|define|describe|tell\s+me\s+about|"
    r"difference\s+between)\b",
    re.IGNORECASE,
)


def sanitize_question(raw: Optional[str]) -> str:
    """Normalise the question before anything else looks at it.

    Collapses whitespace, strips control characters and truncates. Truncation
    happens here rather than at the model call so that intent, place lookup and
    the model all judge exactly the same text.
    """
    text = raw or ""
    # Control characters are stripped rather than escaped: they carry no
    # meaning in a question, and are a common way to smuggle fake role
    # markers into the transcript.
    text = re.sub(r"[\x00-\x08\x0b-\x1f\x7f]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) > MAX_QUESTION_CHARS:
        text = text[:MAX_QUESTION_CHARS].rstrip() + "..."
    return text


def sanitize_history(raw: Any) -> List[Dict[str, str]]:
    """Accept only well-formed prior turns, and only a few of them.

    The history arrives from the browser, so it is treated as untrusted input:
    roles are restricted to the two the chat uses, content is sanitised the same
    way the question is, and the whole transcript is capped. Anything else is
    dropped rather than repaired.
    """
    if not isinstance(raw, list):
        return []

    turns: List[Dict[str, str]] = []
    for item in raw[-MAX_HISTORY_TURNS * 2:]:
        if not isinstance(item, dict):
            continue
        role = item.get("role")
        if role not in ("user", "assistant"):
            continue
        content = sanitize_question(item.get("content"))
        if content:
            turns.append({"role": role, "content": content})

    turns = turns[-MAX_HISTORY_TURNS:]

    # Trim from the front until the transcript fits, so the most recent context
    # survives when the cap bites.
    while turns and sum(len(t["content"]) for t in turns) > MAX_HISTORY_CHARS:
        turns.pop(0)
    return turns


def _detect_injection(question: str) -> Optional[str]:
    for pattern in _INJECTION_PATTERNS:
        if re.search(pattern, question, re.IGNORECASE):
            return "instruction_override"
    return None


def _detect_unsafe_topic(question: str) -> Optional[str]:
    for pattern, label in _UNSAFE_TOPICS:
        if re.search(pattern, question, re.IGNORECASE):
            return label
    return None


def _has_domain_term(question: str) -> bool:
    words = set(re.findall(r"[a-z]+", question.lower()))
    return bool(words & _DOMAIN_TERMS)


def is_latin_script(question: str) -> bool:
    """Whether the keyword lists in this module can judge the question at all.

    The domain vocabulary and stopword lists are English. A question written in
    Devanagari, Tamil, Bengali or any other Indic script contains none of those
    words, so applying the lists would refuse every non-English question as
    off-topic. Callers use this to skip the keyword gate and let the model's own
    scope rules decide instead.
    """
    letters = [ch for ch in question if ch.isalpha()]
    if not letters:
        return True
    latin = sum(1 for ch in letters if ch.isascii())
    return latin / len(letters) >= 0.5


def precheck(question: str) -> Optional[Tuple[Intent, Optional[str]]]:
    """Decide the intents that need no place lookup and no live data.

    Run before :func:`extract_place` so a refused or trivial question never
    reaches the geocoder: sending "prescribe medicine for fever" to a place
    search wastes a round trip and risks matching a town called Fever.

    Returns None when the question needs the full pipeline.
    """
    if not question:
        return None

    injection = _detect_injection(question)
    if injection:
        logger.warning("Guardrail: refused a question matching %s", injection)
        return Intent.UNSAFE, injection

    unsafe = _detect_unsafe_topic(question)
    if unsafe:
        return Intent.UNSAFE, unsafe

    if _GREETING_RE.match(question):
        return Intent.SMALLTALK, None

    if _CAPABILITY_RE.search(question):
        return Intent.CAPABILITY, None

    return None


def classify(question: str, place_found: bool,
             place_phrase: Optional[str] = None,
             place_country: Optional[str] = None,
             in_conversation: bool = False) -> Tuple[Intent, Optional[str]]:
    """Sort a question into an :class:`Intent`.

    ``place_found`` is passed in rather than recomputed because a bare place
    name ("Paradip") is an advisory request even though it contains no domain
    vocabulary at all.

    ``place_phrase`` is the text that actually geocoded. A hit alone is not
    enough to accept a question: the geocoder has a town for almost any word, so
    "write me a python quicksort" resolves to Writers Island. A hit only carries
    an out-of-domain question when the question is essentially just that place
    name; anything left over means the question was about something else.

    Returns the intent and, for the refusing intents, a short machine-readable
    reason the caller can put in the reply.
    """
    if not question:
        return Intent.ADVISORY, None

    early = precheck(question)
    if early:
        return early

    # A question the English word lists cannot read is never refused on their
    # evidence. The model is told the scope and declines out-of-scope questions
    # itself; a false refusal of every Hindi or Tamil question would be worse.
    if not is_latin_script(question):
        return Intent.ADVISORY, None

    in_domain = _has_domain_term(question)

    # A follow-up carries its subject in the turn before it: "and tomorrow?"
    # names neither a place nor a hazard, but the conversation it continues
    # already passed this check. Only short follow-ups are given this pass, so
    # a fresh off-topic question mid-conversation is still refused.
    is_followup = in_conversation and len(question.split()) <= 8

    if not in_domain and not is_followup:
        if not place_found:
            return Intent.OUT_OF_SCOPE, "no_domain_term"

        content = {w for w in re.findall(r"[a-z]+", question.lower())
                   if w not in _PLACE_STOPWORDS}
        matched = set(re.findall(r"[a-z]+", (place_phrase or "").lower()))
        if content - matched:
            return Intent.OUT_OF_SCOPE, "place_match_only"

        # A bare word that resolves only to somewhere outside India is a
        # coincidence, not a request: "tell me a joke" finds Joke, Liberia.
        # A genuine question about foreign water still carries a domain term
        # ("cyclone risk near Dhaka") and never reaches this check.
        if place_country and place_country.lower() != "india":
            return Intent.OUT_OF_SCOPE, "place_outside_india"

    # A definition-shaped question with no place is answered as knowledge, not
    # as a station readout — "what is a cyclone" should not print wave heights.
    if _DEFINITION_RE.match(question) and not place_found and not _ADVISORY_RE.search(question):
        return Intent.EXPLAINER, None

    if place_found or _ADVISORY_RE.search(question) or not _DEFINITION_RE.match(question):
        return Intent.ADVISORY, None

    return Intent.EXPLAINER, None


# ---------------------------------------------------------------------------
# Place extraction
# ---------------------------------------------------------------------------

_CACHE_TTL_SECONDS = 3600
_geo_cache: Dict[Tuple[str, str], Tuple[float, Optional[Dict[str, Any]]]] = {}
_geo_lock = asyncio.Lock()


def candidate_places(question: str) -> List[str]:
    """Pull the phrases from a question that could be a place name.

    Two sources, most reliable first:

    1. Whatever follows a locative preposition -- "flood in Raisen", "off
       Nagapattinam". This is where a place almost always sits in these
       questions, and it survives lowercase input, which capitalisation-based
       extraction does not.
    2. Remaining runs of words that are not stopwords or domain vocabulary.

    Candidates are capped because each one costs a geocoder round trip.
    """
    if not question:
        return []

    candidates: List[str] = []

    # In an Indic script none of the stopword or preposition rules below apply,
    # and the geocoder only matches a native name when it is queried on its own.
    # Each word is tried instead, longest first, which finds "पारादीप" inside a
    # full Hindi sentence.
    #
    # Punctuation is stripped by an explicit list rather than by `\W`, because
    # `\w` excludes the combining vowel marks that Indic scripts are written
    # with: substituting on it turned "विशाखापत्तनम" into "तनम".
    if not is_latin_script(question):
        stripped = re.sub(r"[!?.,;:()\[\]{}\"'|/\\।॥]", " ", question)
        words = [w for w in stripped.split() if len(w) >= 3]
        for word in sorted(words, key=len, reverse=True)[:4]:
            if word not in candidates:
                candidates.append(word)
        return candidates

    text = re.sub(r"[^\w\s'\-]", " ", question)
    lowered = text.lower()

    def add(phrase: str) -> None:
        phrase = phrase.strip(" -'")
        if not phrase or len(phrase) < 3:
            return
        # A phrase containing a digit is a measurement or an index value, not a
        # town: "hazard index 0.4" must not be geocoded.
        if any(ch.isdigit() for ch in phrase):
            return
        words = phrase.split()
        if len(words) > 3:
            words = words[:3]
            phrase = " ".join(words)
        if all(w in _PLACE_STOPWORDS for w in words):
            return
        if phrase not in candidates:
            candidates.append(phrase)

    # Source 1: after a locative preposition, up to three words, stopping at the
    # next stopword so "in Raisen today" does not become "Raisen today".
    for match in re.finditer(r"\b(?:in|at|near|off|around|over|for|from)\s+(.+)$", lowered):
        tail = match.group(1).split()
        run: List[str] = []
        for word in tail[:4]:
            if word in _PLACE_STOPWORDS:
                break
            run.append(word)
        if run:
            add(" ".join(run))

    # Source 2: any surviving run of non-stopwords, longest first, since a
    # two-word district beats either of its halves.
    runs: List[List[str]] = []
    current: List[str] = []
    for word in lowered.split():
        if word in _PLACE_STOPWORDS:
            if current:
                runs.append(current)
                current = []
        else:
            current.append(word)
    if current:
        runs.append(current)

    for run in sorted(runs, key=len, reverse=True):
        add(" ".join(run))

    return candidates[:4]


async def _geocode_one(client: httpx.AsyncClient, name: str,
                       language: str) -> Optional[Dict[str, Any]]:
    try:
        res = await client.get(
            GEOCODE_URL,
            params={"name": name, "count": 5, "language": language, "format": "json"},
        )
        if res.status_code != 200:
            return None
        results = [r for r in (res.json().get("results") or [])
                   if r.get("latitude") is not None and r.get("longitude") is not None]
        if not results:
            return None
        # ORCA advises on the Indian coast, so an Indian match wins over a more
        # populous namesake elsewhere -- Salem, Tamil Nadu rather than Salem,
        # Oregon. Foreign places are still returned when nothing Indian matches.
        for hit in results:
            if (hit.get("country_code") or "").upper() == "IN":
                return hit
        return results[0]
    except Exception as exc:
        logger.warning("Geocoding lookup failed for %r: %s", name, exc)
        return None


async def extract_place(question: str, language: str = "en") -> Dict[str, Any]:
    """Resolve the place a question is about, if it names one.

    Each candidate phrase is looked up concurrently and the first candidate in
    priority order that resolves wins. Returning ``{"found": False}`` is a normal
    outcome, not a failure: most questions name no place, and the caller then
    answers for the station the dashboard is showing.

    ``language`` is passed to the geocoder because it only matches a native
    spelling when asked in that language: "\u0935\u093f\u0936\u093e\u0916\u093e\u092a\u0924\u094d\u0924\u0928\u092e" resolves under ``hi`` and
    returns nothing under ``en``.

    Native-script coverage is partial -- the upstream index has Hindi
    Visakhapatnam but not Hindi Paradip, and it does not handle case-inflected
    Tamil ("\u0b9a\u0bc6\u0ba9\u0bcd\u0ba9\u0bc8\u0baf\u0bbf\u0bb2\u0bcd"). A miss is not an error: the answer is then given for
    the point the dashboard is showing, and says so.
    """
    candidates = candidate_places(question)
    if not candidates:
        return {"found": False}

    now = time.monotonic()
    async with _geo_lock:
        for key in [k for k, (ts, _) in _geo_cache.items() if now - ts > _CACHE_TTL_SECONDS]:
            _geo_cache.pop(key, None)
        cached = {c: _geo_cache[(language, c)][1]
                  for c in candidates if (language, c) in _geo_cache}

    pending = [c for c in candidates if c not in cached]
    fetched: Dict[str, Optional[Dict[str, Any]]] = {}
    if pending:
        try:
            async with httpx.AsyncClient(timeout=4.0) as client:
                results = await asyncio.gather(
                    *(_geocode_one(client, c, language) for c in pending),
                    return_exceptions=True,
                )
        except Exception as exc:
            logger.warning("Geocoding batch failed: %s", exc)
            results = [None] * len(pending)

        for name, result in zip(pending, results):
            fetched[name] = None if isinstance(result, Exception) else result

        async with _geo_lock:
            for name, result in fetched.items():
                _geo_cache[(language, name)] = (now, result)

    for name in candidates:
        hit = cached.get(name, fetched.get(name))
        if not hit:
            continue
        return {
            "found": True,
            "matched_on": name,
            "city": hit.get("name"),
            "state": hit.get("admin1") or hit.get("country") or "",
            "country": hit.get("country"),
            "lat": hit.get("latitude"),
            "lon": hit.get("longitude"),
        }

    return {"found": False}


async def fetch_local_weather(lat: float, lon: float) -> Dict[str, Any]:
    """Current land weather at a resolved place.

    Kept separate from the marine observation fetch: this describes the air over
    a town, while ``ocean_data`` describes the water, and conflating the two is
    how an inland district ends up with a wave height.
    """
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            res = await client.get(
                "https://api.open-meteo.com/v1/forecast",
                params={
                    "latitude": lat,
                    "longitude": lon,
                    "current": "temperature_2m,relative_humidity_2m,wind_speed_10m,precipitation",
                },
            )
            if res.status_code != 200:
                return {}
            current = res.json().get("current", {})
            return {
                "temp": current.get("temperature_2m"),
                "humidity": current.get("relative_humidity_2m"),
                "wind": current.get("wind_speed_10m"),
                "rain": current.get("precipitation"),
            }
    except Exception as exc:
        logger.warning("Local weather fetch failed for %s,%s: %s", lat, lon, exc)
        return {}
