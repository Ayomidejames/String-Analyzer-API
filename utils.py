# utils.py
import hashlib
import json
import re
from datetime import datetime, timezone

def now_iso_z():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

def sha256_hex(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()

def analyze_string(s: str) -> dict:
    # s is stored exactly as provided (case preserved),
    # but some checks are case-insensitive (palindrome).
    length = len(s)
    cleaned = ''.join(s.split())  # remove whitespace for palindrome check? decide policy
    # here we will treat palindrome as case-insensitive and ignoring whitespace:
    normalized = re.sub(r"\s+", "", s).lower()
    is_palindrome = normalized == normalized[::-1]
    unique_characters = len(set(s))
    word_count = 0
    if s.strip() != "":
        word_count = len(re.findall(r"\S+", s))
    freq = {}
    for ch in s:
        freq[ch] = freq.get(ch, 0) + 1

    sha = sha256_hex(s)
    props = {
        "length": length,
        "is_palindrome": is_palindrome,
        "unique_characters": unique_characters,
        "word_count": word_count,
        "sha256_hash": sha,
        "character_frequency_map": freq
    }
    return props

def props_to_json(props: dict) -> str:
    return json.dumps(props, ensure_ascii=False)

def json_to_props(s: str) -> dict:
    return json.loads(s)
