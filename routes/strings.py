# routes/strings.py
from flask import Blueprint, request, jsonify
from models import get_session, StoredString
from utils import analyze_string, props_to_json, json_to_props, now_iso_z, sha256_hex
from sqlalchemy.exc import IntegrityError
import json

strings_bp = Blueprint("strings", __name__, url_prefix="")

@strings_bp.route("/", methods=["POST"])
def create_string():
    if not request.is_json:
        return jsonify({"error": "Invalid Content-Type, expected application/json"}), 400
    payload = request.get_json()
    if "value" not in payload:
        return jsonify({"error": 'Missing "value" field'}), 400
    value = payload["value"]
    if not isinstance(value, str):
        return jsonify({"error": '"value" must be a string'}), 422

    session = get_session()
    sha = sha256_hex(value)
    exists = session.query(StoredString).filter_by(id=sha).first()
    if exists:
        session.close()
        return jsonify({"error": "String already exists"}), 409

    props = analyze_string(value)
    record = StoredString(id=props["sha256_hash"], value=value, properties=props_to_json(props), created_at=None)
    # created_at default will be set by model default if None
    try:
        session.add(record)
        session.commit()
        # refresh to load created_at
        session.refresh(record)
    except IntegrityError:
        session.rollback()
        session.close()
        return jsonify({"error": "String already exists"}), 409

    result = {
        "id": record.id,
        "value": record.value,
        "properties": json.loads(record.properties),
        "created_at": record.created_at.replace(microsecond=0).isoformat() + "Z"
    }
    session.close()
    return jsonify(result), 201

@strings_bp.route("/<path:string_value>", methods=["GET"])
def get_string(string_value):
    session = get_session()
    rec = session.query(StoredString).filter_by(value=string_value).first()
    session.close()
    if not rec:
        return jsonify({"error": "String not found"}), 404
    return jsonify({
        "id": rec.id,
        "value": rec.value,
        "properties": json.loads(rec.properties),
        "created_at": rec.created_at.replace(microsecond=0).isoformat() + "Z"
    }), 200

@strings_bp.route("/", methods=["GET"])
def list_strings():
    args = request.args
    # helper to parse booleans
    def parse_bool(v):
        if v is None: return None
        if v.lower() in ("true","1","t","yes","y"): return True
        if v.lower() in ("false","0","f","no","n"): return False
        return None

    try:
        is_palindrome = parse_bool(args.get("is_palindrome"))
        min_length = int(args["min_length"]) if args.get("min_length") else None
        max_length = int(args["max_length"]) if args.get("max_length") else None
        word_count = int(args["word_count"]) if args.get("word_count") else None
        contains_character = args.get("contains_character")
        if contains_character and len(contains_character) != 1:
            return jsonify({"error": "contains_character must be a single character"}), 400
    except ValueError:
        return jsonify({"error": "Invalid query parameter types"}), 400

    session = get_session()
    all_recs = session.query(StoredString).all()
    filtered = []
    for r in all_recs:
        props = json.loads(r.properties)
        ok = True
        if is_palindrome is not None and props.get("is_palindrome") != is_palindrome:
            ok = False
        if min_length is not None and props.get("length", 0) < min_length:
            ok = False
        if max_length is not None and props.get("length", 0) > max_length:
            ok = False
        if word_count is not None and props.get("word_count") != word_count:
            ok = False
        if contains_character is not None and contains_character not in r.value:
            ok = False
        if ok:
            filtered.append({
                "id": r.id,
                "value": r.value,
                "properties": props,
                "created_at": r.created_at.replace(microsecond=0).isoformat() + "Z"
            })
    session.close()

    filters_applied = {}
    for k in ("is_palindrome", "min_length", "max_length", "word_count", "contains_character"):
        if args.get(k) is not None:
            filters_applied[k] = args.get(k) if k != "is_palindrome" else parse_bool(args.get(k))

    return jsonify({"data": filtered, "count": len(filtered), "filters_applied": filters_applied}), 200

@strings_bp.route("/<path:string_value>", methods=["DELETE"])
def delete_string(string_value):
    session = get_session()
    rec = session.query(StoredString).filter_by(value=string_value).first()
    if not rec:
        session.close()
        return jsonify({"error": "String not found"}), 404
    session.delete(rec)
    session.commit()
    session.close()
    return ("", 204)
