# app.py
"""
String Analyzer Service - single-file implementation matching HNG Stage 1 spec.
Endpoints:
 - POST   /strings
 - GET    /strings/<string_value>
 - GET    /strings
 - GET    /strings/filter-by-natural-language?query=...
 - DELETE /strings/<string_value>
"""
from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime, timezone
import hashlib
import json
import re
import os
from sqlalchemy import create_engine, Column, String, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError

# ---------- Config ----------
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///strings.db")

# ---------- DB Setup ----------
Base = declarative_base()

class StoredString(Base):
    __tablename__ = "strings"
    id = Column(String, primary_key=True)  # sha256 hex
    value = Column(Text, nullable=False, unique=True)
    properties = Column(Text, nullable=False)  # JSON text
    created_at = Column(DateTime, nullable=False)

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)
Base.metadata.create_all(bind=engine)

# ---------- App ----------
app = Flask(__name__)
CORS(app)

# ---------- Helpers ----------
def now_iso_z():
    return datetime.utcnow().replace(microsecond=0).isoformat() + "Z"

def sha256_hex(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()

def analyze_string(s: str) -> dict:
    # length is full string length (including spaces)
    length = len(s)
    # palindrome check: case-insensitive, ignore whitespace
    normalized = re.sub(r"\s+", "", s).lower()
    is_palindrome = normalized == normalized[::-1]
    unique_characters = len(set(s))
    word_count = 0 if s.strip() == "" else len(re.findall(r"\S+", s))
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

def json_props_to_string(props: dict) -> str:
    return json.dumps(props, ensure_ascii=False)

def string_to_json_props(s: str) -> dict:
    return json.loads(s)

# ---------- Routes ----------

@app.route("/strings", methods=["POST"])
def create_string():
    # Validate content-type and JSON
    if not request.is_json:
        return jsonify({"error": "Invalid Content-Type, expected application/json"}), 400
    try:
        payload = request.get_json(force=True)
    except Exception:
        return jsonify({"error": "Invalid JSON body"}), 400

    if "value" not in payload:
        return jsonify({"error": 'Missing "value" field'}), 400

    value = payload["value"]

    if not isinstance(value, str):
        return jsonify({"error": '"value" must be a string'}), 422

    # Compute props
    try:
        props = analyze_string(value)
    except Exception as e:
        return jsonify({"error": "Internal analysis error", "detail": str(e)}), 500

    session = SessionLocal()
    try:
        record = StoredString(
            id=props["sha256_hash"],
            value=value,
            properties=json_props_to_string(props),
            created_at=datetime.utcnow()
        )
        session.add(record)
        session.commit()
    except IntegrityError:
        session.rollback()
        session.close()
        return jsonify({"error": "String already exists"}), 409
    except Exception as e:
        session.rollback()
        session.close()
        return jsonify({"error": "Database error", "detail": str(e)}), 500

    # success response
    response = {
        "id": record.id,
        "value": record.value,
        "properties": props,
        "created_at": record.created_at.replace(microsecond=0).isoformat() + "Z"
    }
    session.close()
    return jsonify(response), 201


@app.route("/strings/<path:string_value>", methods=["GET"])
def get_string(string_value):
    session = SessionLocal()
    try:
        rec = session.query(StoredString).filter_by(value=string_value).first()
    except Exception as e:
        session.close()
        return jsonify({"error": "Database error", "detail": str(e)}), 500

    if not rec:
        session.close()
        return jsonify({"error": "String not found"}), 404

    response = {
        "id": rec.id,
        "value": rec.value,
        "properties": string_to_json_props(rec.properties),
        "created_at": rec.created_at.replace(microsecond=0).isoformat() + "Z"
    }
    session.close()
    return jsonify(response), 200


@app.route("/strings", methods=["GET"])
def list_strings():
    args = request.args

    def parse_bool(v):
        if v is None: return None
        if v.lower() in ("true","1","t","yes","y"): return True
        if v.lower() in ("false","0","f","no","n"): return False
        return None

    # Parse query params with validation
    try:
        is_palindrome = parse_bool(args.get("is_palindrome"))
        min_length = int(args["min_length"]) if args.get("min_length") is not None else None
        max_length = int(args["max_length"]) if args.get("max_length") is not None else None
        word_count = int(args["word_count"]) if args.get("word_count") is not None else None
        contains_character = args.get("contains_character")
        if contains_character is not None and len(contains_character) != 1:
            return jsonify({"error": "contains_character must be a single character"}), 400
    except ValueError:
        return jsonify({"error": "Invalid query parameter types"}), 400

    session = SessionLocal()
    try:
        all_recs = session.query(StoredString).all()
    except Exception as e:
        session.close()
        return jsonify({"error": "Database error", "detail": str(e)}), 500

    results = []
    for rec in all_recs:
        props = string_to_json_props(rec.properties)
        ok = True
        if is_palindrome is not None and props.get("is_palindrome") != is_palindrome:
            ok = False
        if min_length is not None and props.get("length", 0) < min_length:
            ok = False
        if max_length is not None and props.get("length", 0) > max_length:
            ok = False
        if word_count is not None and props.get("word_count") != word_count:
            ok = False
        if contains_character is not None and contains_character not in rec.value:
            ok = False
        if ok:
            results.append({
                "id": rec.id,
                "value": rec.value,
                "properties": props,
                "created_at": rec.created_at.replace(microsecond=0).isoformat() + "Z"
            })

    session.close()
    filters_applied = {}
    for k in ("is_palindrome","min_length","max_length","word_count","contains_character"):
        if args.get(k) is not None:
            filters_applied[k] = parse_bool(args.get(k)) if k == "is_palindrome" else args.get(k)

    return jsonify({"data": results, "count": len(results), "filters_applied": filters_applied}), 200


# Simple NL parser supporting the spec examples
def parse_nl_query(q: str):
    original = q
    q = q.lower()
    parsed = {}
    if re.search(r'\bsingle word\b', q) or re.search(r'\bone word\b', q):
        parsed['word_count'] = 1
    if re.search(r'palindrom(e|ic)s?\b', q) or 'palindrome' in q:
        parsed['is_palindrome'] = True
    m = re.search(r'longer than (\d+)', q)
    if m:
        parsed['min_length'] = int(m.group(1)) + 1
    m2 = re.search(r'containing the letter ([a-z])', q)
    if m2:
        parsed['contains_character'] = m2.group(1)
    m3 = re.search(r'(\d+)\s+words\b', q)
    if m3:
        parsed['word_count'] = int(m3.group(1))
    if 'first vowel' in q and 'contains_character' not in parsed:
        parsed['contains_character'] = 'a'
    if not parsed:
        raise ValueError("Unable to parse natural language query")
    return {"original": original, "parsed_filters": parsed}


@app.route("/strings/filter-by-natural-language", methods=["GET"])
def filter_by_nl():
    q = request.args.get("query")
    if not q:
        return jsonify({"error": "query parameter required"}), 400
    try:
        interpreted = parse_nl_query(q)
    except ValueError:
        return jsonify({"error": "Unable to parse natural language query"}), 400

    filters = interpreted["parsed_filters"]
    session = SessionLocal()
    try:
        all_recs = session.query(StoredString).all()
    except Exception as e:
        session.close()
        return jsonify({"error": "Database error", "detail": str(e)}), 500

    results = []
    for rec in all_recs:
        props = string_to_json_props(rec.properties)
        ok = True
        if 'is_palindrome' in filters and props.get("is_palindrome") != filters['is_palindrome']:
            ok = False
        if 'min_length' in filters and props.get("length", 0) < filters['min_length']:
            ok = False
        if 'max_length' in filters and props.get("length", 0) > filters.get('max_length', 10**9):
            ok = False
        if 'word_count' in filters and props.get("word_count") != filters['word_count']:
            ok = False
        if 'contains_character' in filters and filters['contains_character'] not in rec.value:
            ok = False
        if ok:
            results.append({
                "id": rec.id,
                "value": rec.value,
                "properties": props,
                "created_at": rec.created_at.replace(microsecond=0).isoformat() + "Z"
            })
    session.close()
    return jsonify({"data": results, "count": len(results), "interpreted_query": interpreted}), 200


@app.route("/strings/<path:string_value>", methods=["DELETE"])
def delete_string(string_value):
    session = SessionLocal()
    try:
        rec = session.query(StoredString).filter_by(value=string_value).first()
    except Exception as e:
        session.close()
        return jsonify({"error": "Database error", "detail": str(e)}), 500

    if not rec:
        session.close()
        return jsonify({"error": "String not found"}), 404

    try:
        session.delete(rec)
        session.commit()
    except Exception as e:
        session.rollback()
        session.close()
        return jsonify({"error": "Database error", "detail": str(e)}), 500

    session.close()
    return ("", 204)


# Health check root
@app.route("/", methods=["GET"])
def health():
    return jsonify({"status": "ok", "time": now_iso_z()}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
