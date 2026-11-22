#!/usr/bin/env python3
"""
/GHOST Anti-AI Caption Generator & Sanitizer for SOLE Bits & Bytes (IGIT Sarang).
Instagram-only (@sole_igit):
1. Zero em dashes (—) or en dashes (–) anywhere in the prose.
2. Strips AI-tell vocabulary and raw Markdown (**bold**, __italic__, `code`).
3. Prevents duplicate hashtag blocks by stripping inline hashtags from body text
   and appending one unified, deduplicated Instagram hashtag block.
"""

import math
import re
from typing import Any, Dict, List, Optional

BANNED_PHRASES = [
    (r"\bdelve(?:s|d)?\s+into\b", "look at"),
    (r"\bdelve(?:s|d)?\b", "dig"),
    (r"\ba\s+testament\s+to\b", "proof of"),
    (r"\btapestry\s+of\b", "mix of"),
    (r"\bunderscore(?:s|d)?\b", "show"),
    (r"\bpivotal\b", "major"),
    (r"\blandscape\b", "scene"),
    (r"\bvibrant\b", "lively"),
    (r"\bseamless(?:ly)?\b", "smooth"),
    (r"\bcrucial\b", "important"),
    (r"\bfostering\b", "building"),
    (r"\bmoreover,?\s*", ""),
    (r"\bfurthermore,?\s*", ""),
    (r"\bin\s+conclusion,?\s*", ""),
    (r"\bit\s+is\s+worth\s+noting\s+that\s*", ""),
    (r"\bin\s+today'?s\s+fast-paced\s+world,?\s*", ""),
    (r"\bever-evolving\b", "changing"),
    (r"\bgame-changer\b", "big shift"),
    (r"\bunlock(?:ing)?\s+the\s+power\s+of\b", "using"),
    (r"\bembark\s+on\b", "start"),
    (r"\bbeacon\s+of\b", "example of"),
    (r"\brealm\s+of\b", "world of"),
]

CORE_HASHTAGS_IG = [
    "#IGITSarang",
    "#SOLE",
    "#SOLEIGIT",
    "#BitsAndBytes",
    "#LiteraryClub",
    "#IGIT",
    "#OdishaColleges",
    "#CampusLife",
]


def strip_markdown_formatting(text: str) -> str:
    """Removes raw Markdown bold/italic/code syntax so captions render cleanly everywhere."""
    if not text:
        return ""
    cleaned = re.sub(r"\*\*([^\n*]+?)\*\*", r"\1", text)
    cleaned = re.sub(r"__([^\n_]+?)__", r"\1", cleaned)
    cleaned = re.sub(r"`([^`\n]+?)`", r"\1", cleaned)
    return cleaned


def strip_embedded_hashtags(text: str) -> tuple[str, List[str]]:
    """
    Removes hashtag-only lines and trailing hashtag clusters from caption prose
    so the final caption never has two separate hashtag blocks.
    Returns (cleaned_text, extracted_hashtags).
    """
    if not text:
        return "", []
    extracted: List[str] = []
    kept_lines: List[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        # Drop spacer dots if an LLM already included them
        if stripped == ".":
            continue
        tokens = stripped.split()
        if tokens and all(tok.startswith("#") and len(tok) > 1 for tok in tokens):
            extracted.extend(tokens)
            continue
        kept_lines.append(line)
    body = "\n".join(kept_lines)
    # Also remove any trailing inline hashtags at the very end of the caption
    trailing_tags = re.findall(r"(?:\s+#[A-Za-z0-9_]+)+\s*$", body)
    if trailing_tags:
        extracted.extend(re.findall(r"#[A-Za-z0-9_]+", trailing_tags[-1]))
        body = re.sub(r"(?:\s+#[A-Za-z0-9_]+)+\s*$", "", body)
    body = re.sub(r"\n{3,}", "\n\n", body).strip()
    return body, extracted


def ghost_sanitize(text: str) -> str:
    """
    Mechanical pass that removes em/en dashes, raw Markdown, and AI vocabulary tells.
    """
    if not text:
        return ""
    cleaned = strip_markdown_formatting(text)
    cleaned = re.sub(r"\s*[—–]\s*", " - ", cleaned)
    for pattern, replacement in BANNED_PHRASES:
        cleaned = re.sub(pattern, replacement, cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"[ \t]{2,}", " ", cleaned)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.strip()


def audit_ghost_compliance(text: str) -> Dict[str, Any]:
    """
    Verifies that a caption contains zero em/en dashes, zero raw Markdown asterisks,
    and zero banned AI buzzwords.
    """
    has_em_dash = "—" in text or "–" in text
    has_raw_markdown = bool(re.search(r"\*\*|__|`.+?`", text))
    found_buzzwords = []
    for pattern, _ in BANNED_PHRASES:
        if re.search(pattern, text, flags=re.IGNORECASE):
            found_buzzwords.append(pattern)
    return {
        "passed": (not has_em_dash) and (not has_raw_markdown) and (len(found_buzzwords) == 0),
        "has_em_or_en_dash": has_em_dash,
        "has_raw_markdown": has_raw_markdown,
        "found_buzzwords": found_buzzwords,
    }


def _dedupe_hashtags(tags: List[str], max_tags: int = 16) -> List[str]:
    seen: set = set()
    result: List[str] = []
    for raw in tags:
        clean = re.sub(r"[^A-Za-z0-9_#]", "", str(raw or "").strip())
        if not clean:
            continue
        if not clean.startswith("#"):
            clean = f"#{clean}"
        if len(clean) <= 1:
            continue
        key = clean.lower()
        if key not in seen:
            seen.add(key)
            result.append(clean)
        if len(result) >= max_tags:
            break
    return result


def build_captions(
    content_type: str,
    selected_items: List[Dict[str, Any]],
    week_label: str,
    custom_caption: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Builds or sanitizes the Instagram (@sole_igit) caption and unified hashtag block.
    """
    extracted_tags: List[str] = []

    if custom_caption and isinstance(custom_caption.get("instagram"), str) and custom_caption["instagram"].strip():
        body_no_tags, extracted_tags = strip_embedded_hashtags(custom_caption["instagram"])
        ig_raw = ghost_sanitize(body_no_tags)
        extra_tags = list(custom_caption.get("hashtags") or []) + extracted_tags
    elif content_type == "news":
        n_items = len(selected_items)
        top1 = selected_items[0] if n_items > 0 else {}
        top2 = selected_items[1] if n_items > 1 else {}
        top3 = selected_items[2] if n_items > 2 else {}
        # Slide 1 = Cover, ceil((n_items - 2)/2) slides for #n..#3, +1 for #02, +1 for #01
        top1_slide = 1 + math.ceil(max(0, n_items - 2) / 2) + 2
        ig_lines = [
            f"{n_items} big stories happened this week while you were busy with classes and labs ({week_label}).",
            "",
            "Here is a quick peek inside our Weekly News Highlights:",
            f"- {top3.get('headline', '')}",
            f"- {top2.get('headline', '')}",
            f"- Plus our #01 highlight on Slide {top1_slide} ({top1.get('category', 'Campus Spotlight')}).",
            "",
            "Swipe till the last slide and vote A, B, or C in our weekly poll.",
        ]
        ig_raw = ghost_sanitize("\n".join(ig_lines))
        extra_tags = [
            "#WeeklyNews", "#CurrentAffairs", "#Top10News", "#NewsDigest",
            "#TechNews", "#WorldNews", "#IndiaNews", "#StudentReads", "#StayInformed",
        ]
    elif content_type == "facts":
        item = selected_items[0]
        ig_lines = [
            f"Wait... is this actually real? ({item.get('category', 'Fact Drop')})",
            "",
            f"Today's mystery: {item.get('title', '')}.",
            "Most people only know half the story, but the plot twist on Slide 3 changes everything.",
            "",
            f"Verified Source: {item.get('source', 'Archival Research')}",
            "",
            "Swipe to the last slide and comment A, B, or C: did you know this before today?",
        ]
        ig_raw = ghost_sanitize("\n".join([l for l in ig_lines if l is not None]))
        extra_tags = [
            "#DidYouKnow", "#FactOfTheWeek", "#RandomFacts", "#Trivia",
            "#ScienceFacts", "#HistoryFacts", "#CuriousMinds", "#LearnSomethingNew",
        ]
    else:  # vocab
        item = selected_items[0]
        word = item.get("word", "")
        pos = item.get("part_of_speech", "")
        defn = item.get("definition", "")
        ig_lines = [
            "Ever experienced this exact feeling, but didn't know there was a single word for it?",
            "",
            f"\"{defn}\"",
            "",
            f"Can you guess the {len(word)}-letter {pos} (starts with '{word[0].upper() if word else ''}') before swiping to Slide 3?",
            "",
            "Swipe through to unlock the word, then drop a short sentence using it in the comments. Best sentence gets pinned by @sole_igit.",
        ]
        ig_raw = ghost_sanitize("\n".join(ig_lines))
        extra_tags = [
            "#WordOfTheWeek", "#Vocabulary", "#Thesaurus", "#EnglishLiterature",
            "#Lexicon", "#WritersOfInstagram", "#WordNerd", "#LanguageLovers",
        ]

    all_ig_tags = _dedupe_hashtags(CORE_HASHTAGS_IG + extra_tags, max_tags=16)
    ig_full = f"{ig_raw}\n\n.\n.\n.\n{' '.join(all_ig_tags)}"

    return {
        "instagram_caption": ig_full,
        "hashtags": all_ig_tags,
        "ghost_audit_ig": audit_ghost_compliance(ig_full),
    }
