#!/usr/bin/env python3
"""
Deduplication & History Ledger for SOLE Bits & Bytes Automation (IGIT Sarang).
Maintains both JSON (data/published_history.json) and plain-text (data/published_history.txt)
ledgers to guarantee no News Highlight, Random Fact, or Vocabulary Word is ever repeated.
"""

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Tuple

BASE_DIR = Path("/home/yashagrawall/bits-bytes-automation")
HISTORY_JSON = BASE_DIR / "data" / "published_history.json"
HISTORY_TXT = BASE_DIR / "data" / "published_history.txt"

STOPWORDS = {
    "the", "a", "an", "in", "on", "at", "to", "for", "of", "and", "or", "is",
    "are", "was", "were", "by", "with", "from", "as", "that", "this", "it", "be",
    "has", "have", "had", "will", "its", "new", "after", "over", "into", "more",
}


def normalize_text(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"https?://\S+", "", text)
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def tokenize(text: str) -> set:
    tokens = normalize_text(text).split()
    return {t for t in tokens if len(t) > 2 and t not in STOPWORDS}


def compute_hash(text: str) -> str:
    return hashlib.sha256(normalize_text(text).encode("utf-8")).hexdigest()[:16]


def jaccard_similarity(set_a: set, set_b: set) -> float:
    if not set_a or not set_b:
        return 0.0
    intersection = len(set_a & set_b)
    union = len(set_a | set_b)
    return intersection / union if union else 0.0


def load_history() -> Dict[str, Any]:
    if not HISTORY_JSON.exists():
        HISTORY_JSON.parent.mkdir(parents=True, exist_ok=True)
        default_data = {
            "metadata": {
                "project": "SOLE Bits & Bytes Automation (IGIT Sarang)",
                "created_at": datetime.now().astimezone().isoformat(),
                "last_updated": datetime.now().astimezone().isoformat(),
                "drive_ledger_file_id": None,
            },
            "news": [],
            "facts": [],
            "vocab": [],
            "packages": [],
        }
        save_history(default_data)
        return default_data
    with open(HISTORY_JSON, "r", encoding="utf-8") as f:
        return json.load(f)


def save_history(data: Dict[str, Any]) -> None:
    data["metadata"]["last_updated"] = datetime.now().astimezone().isoformat()
    HISTORY_JSON.parent.mkdir(parents=True, exist_ok=True)
    with open(HISTORY_JSON, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    sync_txt_mirror(data)


def sync_txt_mirror(data: Dict[str, Any]) -> None:
    lines = [
        "====================================================================",
        "SOLE (IGIT SARANG) — BITS & BYTES PUBLISHED CONTENT LEDGER",
        f"Last Updated: {data['metadata']['last_updated']}",
        "====================================================================",
        "",
        f"--- WEEKLY TOP 10 NEWS HIGHLIGHTS ({len(data.get('news', []))} items) ---",
    ]
    for idx, item in enumerate(data.get("news", []), 1):
        lines.append(
            f"{idx}. [{item.get('date_added', '')[:10]}] {item.get('headline', '')} "
            f"({item.get('source', '')}) | URL: {item.get('url', '')} | Hash: {item.get('hash', '')}"
        )
    lines.append("")
    lines.append(f"--- RANDOM FACTS ({len(data.get('facts', []))} items) ---")
    for idx, item in enumerate(data.get("facts", []), 1):
        lines.append(
            f"{idx}. [{item.get('date_added', '')[:10]}] {item.get('title', '')}: "
            f"{item.get('fact', '')} | Hash: {item.get('hash', '')}"
        )
    lines.append("")
    lines.append(f"--- RANDOM VOCABULARY / THESAURUS ({len(data.get('vocab', []))} items) ---")
    for idx, item in enumerate(data.get("vocab", []), 1):
        lines.append(
            f"{idx}. [{item.get('date_added', '')[:10]}] {item.get('word', '')} "
            f"({item.get('part_of_speech', '')}): {item.get('definition', '')} | Hash: {item.get('hash', '')}"
        )
    lines.append("")
    with open(HISTORY_TXT, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def is_duplicate_news(candidate: Dict[str, Any], existing_news: List[Dict[str, Any]]) -> Tuple[bool, str]:
    cand_headline = candidate.get("headline", "")
    cand_url = candidate.get("url", "").strip().rstrip("/")
    cand_hash = compute_hash(cand_headline)
    cand_tokens = tokenize(cand_headline + " " + candidate.get("summary", ""))

    for item in existing_news:
        if item.get("hash") == cand_hash:
            return True, f"Exact headline hash match with '{item.get('headline')}'"
        ex_url = item.get("url", "").strip().rstrip("/")
        if cand_url and ex_url and cand_url.lower() == ex_url.lower():
            return True, f"Same source URL as '{item.get('headline')}'"
        ex_tokens = tokenize(item.get("headline", "") + " " + item.get("summary", ""))
        sim = jaccard_similarity(cand_tokens, ex_tokens)
        if sim >= 0.45:
            return True, f"High topic overlap ({sim:.2f}) with '{item.get('headline')}'"
    return False, ""


def is_duplicate_fact(candidate: Dict[str, Any], existing_facts: List[Dict[str, Any]]) -> Tuple[bool, str]:
    cand_text = f"{candidate.get('title', '')} {candidate.get('fact', '')}"
    cand_hash = compute_hash(cand_text)
    cand_tokens = tokenize(cand_text)

    for item in existing_facts:
        if item.get("hash") == cand_hash:
            return True, f"Exact fact hash match with '{item.get('title')}'"
        ex_tokens = tokenize(f"{item.get('title', '')} {item.get('fact', '')}")
        sim = jaccard_similarity(cand_tokens, ex_tokens)
        if sim >= 0.40:
            return True, f"High semantic overlap ({sim:.2f}) with '{item.get('title')}'"
    return False, ""


def is_duplicate_vocab(candidate: Dict[str, Any], existing_vocab: List[Dict[str, Any]]) -> Tuple[bool, str]:
    cand_word = normalize_text(candidate.get("word", ""))
    for item in existing_vocab:
        ex_word = normalize_text(item.get("word", ""))
        if cand_word == ex_word:
            return True, f"Word '{candidate.get('word')}' was already featured on {item.get('date_added', '')[:10]}"
    return False, ""


def filter_and_rank_candidates(
    content_type: str,
    candidates: List[Dict[str, Any]],
    limit: int = 10,
) -> Dict[str, Any]:
    """
    Filters out repeated items against published_history.json and within the batch itself,
    then ranks remaining candidates by combined Relevance + Popularity score.
    """
    history = load_history()
    accepted: List[Dict[str, Any]] = []
    rejected: List[Dict[str, Any]] = []

    if content_type == "news":
        pool = list(history.get("news", []))
        check_fn = is_duplicate_news
    elif content_type == "facts":
        pool = list(history.get("facts", []))
        check_fn = is_duplicate_fact
    elif content_type == "vocab":
        pool = list(history.get("vocab", []))
        check_fn = is_duplicate_vocab
    else:
        raise ValueError(f"Unsupported content_type: {content_type}")

    for cand in candidates:
        is_dup, reason = check_fn(cand, pool)
        if is_dup:
            cand_copy = dict(cand)
            cand_copy["rejection_reason"] = reason
            rejected.append(cand_copy)
            continue

        rel = float(cand.get("relevance_score", 8.0))
        pop = float(cand.get("popularity_score", 8.0))
        cand_copy = dict(cand)
        cand_copy["relevance_score"] = round(rel, 1)
        cand_copy["popularity_score"] = round(pop, 1)
        cand_copy["combined_score"] = round(0.5 * rel + 0.5 * pop, 2)

        if content_type == "news":
            cand_copy["hash"] = compute_hash(cand.get("headline", ""))
        elif content_type == "facts":
            cand_copy["hash"] = compute_hash(f"{cand.get('title', '')} {cand.get('fact', '')}")
        else:
            cand_copy["hash"] = compute_hash(cand.get("word", ""))

        accepted.append(cand_copy)
        pool.append(cand_copy)

    accepted.sort(
        key=lambda x: (x.get("combined_score", 0), x.get("relevance_score", 0), x.get("popularity_score", 0)),
        reverse=True,
    )
    selected = accepted[:limit]
    return {
        "content_type": content_type,
        "total_candidates": len(candidates),
        "accepted_count": len(accepted),
        "rejected_duplicates_count": len(rejected),
        "selected": selected,
        "rejected_duplicates": rejected,
    }


def commit_selected(content_type: str, selected_items: List[Dict[str, Any]], package_meta: Dict[str, Any] = None) -> None:
    history = load_history()
    now_iso = datetime.now().astimezone().isoformat()
    target_list = history.setdefault(content_type, [])

    for item in selected_items:
        entry = dict(item)
        entry["date_added"] = now_iso
        target_list.append(entry)

    if package_meta:
        pkg = dict(package_meta)
        pkg["created_at"] = now_iso
        history.setdefault("packages", []).append(pkg)

    save_history(history)


def main() -> None:
    parser = argparse.ArgumentParser(description="SOLE Bits & Bytes Deduplication Ledger")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("stats", help="Show counts of recorded items in the deduplication ledger")

    p_filter = sub.add_parser("filter", help="Filter and rank a JSON candidate file")
    p_filter.add_argument("--type", choices=["news", "facts", "vocab"], required=True)
    p_filter.add_argument("--input", required=True, help="Input JSON file with list of candidates")
    p_filter.add_argument("--output", required=True, help="Output JSON file for selected items")
    p_filter.add_argument("--limit", type=int, default=10)
    p_filter.add_argument("--commit", action="store_true", help="Commit selected items to history immediately")

    args = parser.parse_args()
    if args.cmd == "stats":
        h = load_history()
        sync_txt_mirror(h)
        print(json.dumps({
            "news_count": len(h.get("news", [])),
            "facts_count": len(h.get("facts", [])),
            "vocab_count": len(h.get("vocab", [])),
            "packages_count": len(h.get("packages", [])),
            "last_updated": h.get("metadata", {}).get("last_updated"),
        }, indent=2))
    elif args.cmd == "filter":
        with open(args.input, "r", encoding="utf-8") as f:
            payload = json.load(f)
        candidates = payload if isinstance(payload, list) else payload.get("candidates", [])
        result = filter_and_rank_candidates(args.type, candidates, limit=args.limit)
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        if args.commit:
            commit_selected(args.type, result["selected"])
        print(json.dumps({
            "status": "ok",
            "total_candidates": result["total_candidates"],
            "rejected_duplicates_count": result["rejected_duplicates_count"],
            "selected_count": len(result["selected"]),
            "committed": args.commit,
        }))


if __name__ == "__main__":
    main()
