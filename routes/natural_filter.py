# routes/natural_filter.py
from flask import Blueprint, request, jsonify
import re, json
from models import get_session, StoredString

natural_bp = Blueprint("natural_filter", __name__, url_prefix="")

def parse_nl_query(q: str):
    original = q
    q = q.lower()
    parsed = {}
    # single word
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
    # "strings containing the letter z" or "containing the letter z"
    m3 = re.search(r'containing the letter (\w)', q)
    if m3 and 'contains_character' not in parsed:
        parsed['contains_character'] = m3.group(1).lower()
    m4 = re.search(r'(\d+)\s+words\b', q)
    if m4:
        parsed['word_count'] = int(m4.group(1))

    if not parsed:
        raise ValueError("Unable to parse natural language query")
    return {"original": original, "parsed_filters": parsed}

@natural_bp.route("/filter-by-natural-language", methods=["GET"])
def filter_by_nl():
    q = request.args.get("query")
    if not q:
        return jsonify({"error": "query parameter required"}), 400
    try:
        interpreted = parse_nl_query(q)
    except ValueError:
        return jsonify({"error": "Unable to parse natural language query"}), 400

    filters = interpreted["parsed_filters"]
    session = get_session()
    all_recs = session.query(StoredString).all()
    results = []
    for rec in all_recs:
        props = json.loads(rec.properties)
        ok = True
        if 'is_palindrome' in filters and props.get("is_palindrome") != filters['is_palindrome']:
            ok = False
        if 'min_length' in filters and props.get("length", 0) < filters['min_length']:
            ok = False
        if 'max_length' in filters and props.get("length", 0) > filters['max_length']:
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
