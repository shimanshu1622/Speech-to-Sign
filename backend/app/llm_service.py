import os
import json
import re
import requests
import spacy
from typing import List, Set

# ============================================================
# NLP Initialization
# ============================================================

try:
    # Load spaCy's small English model for dynamic lemmatization
    nlp = spacy.load("en_core_web_sm")
except OSError:
    raise OSError("Missing spaCy model. Run: python -m spacy download en_core_web_sm")

# ============================================================
# Configuration
# ============================================================

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
CHAT_URL = f"{OLLAMA_URL}/api/chat"
MODEL = os.getenv("OLLAMA_MODEL", "llama3")

# ============================================================
# System Prompt
# ============================================================

SYSTEM_PROMPT = """
You are an English-to-ASL gloss INTENT extractor.

IMPORTANT:
- You do NOT generate final ASL signs or map to a dataset.
- You only extract base INTENT TOKENS in ASL grammatical order (e.g., Time-Topic-Comment).
- The backend will handle out-of-vocabulary mapping, fingerspelling, and rendering.

STRICT OUTPUT RULES:
- Output MUST be a JSON array of strings.
- No explanations. No surrounding text.
- Uppercase tokens only.
- One concept per token.

TOKEN RULES:
- Base forms: Output plain English base forms where possible (e.g., CHEAT, WALK).
- Pronouns: Output standard English pronouns (I, ME, YOU, HE, SHE, IT, THEY). Do NOT use IX- prefixes.
- Proper Nouns: Output the plain name (LINCOLN, MICKEY, MOUSE). Do NOT use NS- prefixes.
- Fingerspelling: Output the plain word (AC, ZENDAYA). Do NOT use HASH- or FS- prefixes.
- Exclusions: Drop articles (A, AN, THE) and "to be" verbs (AM, IS, ARE, WAS, WERE).
- Do NOT invent ASL grammar markers, classifiers, or punctuation.
- Question words must appear as their own token (WHO, WHAT, WHERE, WHY, WHEN, HOW).

You are allowed to be incomplete.
You are NOT allowed to hallucinate markers or prefixes.
"""

EXAMPLES = """
English: Who cheated in AC?
Output: ["AC", "CHEAT", "WHO"]

English: Good morning
Output: ["GOOD", "MORNING"]

English: What is your name?
Output: ["YOUR", "NAME", "WHAT"]

English: I liked the movie Mickey Mouse.
Output: ["I", "LIKE", "MOVIE", "MICKEY", "MOUSE"]
"""

# ============================================================
# Utility: JSON extraction
# ============================================================

def _extract_json_array(text: str) -> List[str]:
    match = re.search(r"\[[\s\S]*?\]", text)
    if not match:
        raise ValueError(f"No JSON array found in LLM output: {text}")

    try:
        data = json.loads(match.group())
    except json.JSONDecodeError:
        raise ValueError(f"Invalid JSON array: {match.group()}")

    if not isinstance(data, list):
        raise ValueError("Parsed JSON is not a list")

    return data

# ============================================================
# Normalization & Validation
# ============================================================

WH_WORDS: Set[str] = {"WHO", "WHAT", "WHERE", "WHY", "WHEN", "HOW"}

DROP_TOKENS: Set[str] = {
    "A", "AN", "THE",
    "IS", "ARE", "AM", "WAS", "WERE", "BE", "BEEN",
    "IN", "ON", "AT", "OF", "TO", "FROM", "WITH", "BY", "FOR"
}

VALID_TOKEN_RE = re.compile(r"^[A-Z0-9\-]+$")

def _normalize_token(token: str) -> List[str]:
    # 1. Clean up token and strip any hallucinated ASL prefixes just in case
    token = re.sub(r"^(HASH-|FS-|IX-|NS-|POSS-)", "", token.strip().upper())

    if not token or token in DROP_TOKENS:
        return []

    # 2. Dynamic Lemmatization via spaCy (e.g., "RUNNING" -> "RUN", "MICE" -> "MOUSE")
    doc = nlp(token.lower())
    if doc:
        # Take the lemma of the main token and convert back to uppercase
        token = doc[0].lemma_.upper()

    # Re-check against drop tokens in case the lemmatized version is a drop token (e.g., "being" -> "be")
    if token in DROP_TOKENS:
        return []

    # 3. Basic sanity check
    if not VALID_TOKEN_RE.match(token):
        return []

    return [token]

def normalize_gloss_intent(tokens: List[str]) -> List[str]:
    normalized: List[str] = []

    for t in tokens:
        if not isinstance(t, str):
            continue
        normalized.extend(_normalize_token(t))

    # ASL WH-movement: WH words go last
    wh = [t for t in normalized if t in WH_WORDS]
    rest = [t for t in normalized if t not in WH_WORDS]

    return rest + wh

# ============================================================
# Main API
# ============================================================

def english_to_asl_gloss_intent(text: str) -> List[str]:
    """
    Convert English text to ASL gloss INTENT tokens.
    Output is guaranteed to be:
    - deterministic
    - JSON-safe
    - strictly lemmatized English base words
    """

    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": f"""
Examples:
{EXAMPLES}

English sentence:
{text}
"""
            }
        ],
        "stream": False,
        "options": {
            "temperature": 0.0
        }
    }

    response = requests.post(CHAT_URL, json=payload, timeout=60)
    response.raise_for_status()

    raw = response.json()["message"]["content"]

    tokens = _extract_json_array(raw)
    tokens = normalize_gloss_intent(tokens)

    if not tokens:
        raise ValueError(f"Empty gloss intent after normalization. Raw LLM output: {raw}")

    return tokens