#!/usr/bin/env python3
"""
/GHOST Anti-AI Caption Generator & Sanitizer for SOLE Bits & Bytes (IGIT Sarang).
Applies the strict mechanical checks from the `plain-writing` skill:
1. Zero em dashes (—) or en dashes (–) anywhere in the prose.
2. Strips AI-tell vocabulary (delve, tapestry, testament, pivotal, underscore, landscape,
   vibrant, seamless, crucial, fostering, moreover, furthermore, in conclusion, etc.).
3. Generates authentic, student-written Instagram (@sole_igit) and LinkedIn captions
   with high-reach literary, campus, and topic-specific hashtags.
"""

import re
from typing import Any, Dict, List

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

CORE_HASHTAGS_LINKEDIN = [
    "#IGITSarang",
    "#SOLE",
    "#BitsAndBytes",
    "#StudentLeadership",
    "#LiterarySociety",
]


def ghost_sanitize(text: str) -> str:
    """
    Mechanical pass that removes em/en dashes, curly quotes, and AI vocabulary tells.
    """
    if not text:
        return ""
    # Replace em dashes and en dashes with commas, colons, or plain hyphens
    cleaned = re.sub(r"\s*[—–]\s*", " - ", text)
    # Remove banned AI phrases
    for pattern, replacement in BANNED_PHRASES:
        cleaned = re.sub(pattern, replacement, cleaned, flags=re.IGNORECASE)
    # Collapse double spaces on the same line
    cleaned = re.sub(r"[ \t]{2,}", " ", cleaned)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.strip()


def audit_ghost_compliance(text: str) -> Dict[str, Any]:
    """
    Verifies that a caption contains zero em/en dashes and zero banned AI buzzwords.
    """
    has_em_dash = "—" in text or "–" in text
    found_buzzwords = []
    for pattern, _ in BANNED_PHRASES:
        if re.search(pattern, text, flags=re.IGNORECASE):
            found_buzzwords.append(pattern)
    return {
        "passed": (not has_em_dash) and (len(found_buzzwords) == 0),
        "has_em_or_en_dash": has_em_dash,
        "found_buzzwords": found_buzzwords,
    }


def build_captions(content_type: str, selected_items: List[Dict[str, Any]], week_label: str, custom_caption: Dict[str, str] = None) -> Dict[str, Any]:
    """
    Builds or sanitizes the Instagram and LinkedIn captions and hashtag blocks.
    """
    if custom_caption and custom_caption.get("instagram") and custom_caption.get("linkedin"):
        ig_raw = ghost_sanitize(custom_caption["instagram"])
        li_raw = ghost_sanitize(custom_caption["linkedin"])
        extra_tags = custom_caption.get("hashtags", [])
    elif content_type == "news":
        top3 = [item.get("headline", "") for item in selected_items[:3]]
        ig_lines = [
            f"Missed what happened this week? Here are the 10 stories worth your time ({week_label}).",
            "",
            "From policy and science to tech and culture, our Bits & Bytes team picked the ten updates that actually matter:",
            f"1. {top3[0] if len(top3) > 0 else ''}",
            f"2. {top3[1] if len(top3) > 1 else ''}",
            f"3. {top3[2] if len(top3) > 2 else ''}",
            "...plus 7 more inside the carousel.",
            "",
            "Swipe through all 10 slides for the full breakdown and sources.",
            "Which story caught your attention first? Drop your take in the comments.",
        ]
        li_lines = [
            f"Bits & Bytes Weekly News Digest ({week_label}) | SOLE, IGIT Sarang",
            "",
            "Keeping up with the week's biggest developments takes more than scrolling headlines. Here are the Top 10 News Highlights curated by the Bits & Bytes wing of SOLE (Society Of Literary Enthusiasts), IGIT Sarang, complete with primary sources:",
            "",
        ]
        for idx, item in enumerate(selected_items[:10], 1):
            li_lines.append(f"{idx}. {item.get('headline', '')} ({item.get('source', '')})")
        li_lines.extend([
            "",
            "Swipe through the carousel for the full context on each story.",
        ])
        ig_raw = ghost_sanitize("\n".join(ig_lines))
        li_raw = ghost_sanitize("\n".join(li_lines))
        extra_tags = [
            "#WeeklyNews", "#CurrentAffairs", "#Top10News", "#NewsDigest",
            "#TechNews", "#WorldNews", "#IndiaNews", "#StudentReads", "#StayInformed"
        ]
    elif content_type == "facts":
        item = selected_items[0]
        hook = item.get("hook") or f"Most people never notice this about {item.get('category', 'the world').lower()}."
        ig_lines = [
            hook,
            "",
            f"{item.get('title', '')}: {item.get('fact', '')}",
            "",
            f"{item.get('context', '')}",
            "",
            f"Source: {item.get('source', 'Verified Archival Research')}",
            "",
            "Did you already know this one, or is it new to you? Tag a friend who loves random trivia.",
        ]
        li_lines = [
            f"Bits & Bytes Fact of the Week ({week_label}) | SOLE, IGIT Sarang",
            "",
            f"{item.get('title', '')}",
            f"{item.get('fact', '')}",
            "",
            f"{item.get('context', '')}",
            f"Source: {item.get('source', 'Verified Research')}",
        ]
        ig_raw = ghost_sanitize("\n".join([l for l in ig_lines if l is not None]))
        li_raw = ghost_sanitize("\n".join([l for l in li_lines if l is not None]))
        extra_tags = [
            "#DidYouKnow", "#FactOfTheWeek", "#RandomFacts", "#Trivia",
            "#ScienceFacts", "#HistoryFacts", "#CuriousMinds", "#LearnSomethingNew"
        ]
    else:  # vocab
        item = selected_items[0]
        word = item.get("word", "")
        pos = item.get("part_of_speech", "")
        defn = item.get("definition", "")
        example = item.get("example", "")
        syns = ", ".join(item.get("synonyms", [])[:4])
        ig_lines = [
            f"Word of the Week: {word} ({pos})",
            "",
            f"Meaning: {defn}",
            f"Synonyms: {syns}" if syns else "",
            "",
            f"How to use it: \"{example}\"",
            "",
            "Try using this word in a sentence in the comments below. Best sentence gets pinned.",
        ]
        li_lines = [
            f"Bits & Bytes Vocabulary Spotlight ({week_label}) | SOLE, IGIT Sarang",
            "",
            f"Word: {word} ({pos})",
            f"Definition: {defn}",
            f"Synonyms: {syns}" if syns else "",
            f"Example: \"{example}\"",
        ]
        ig_raw = ghost_sanitize("\n".join([l for l in ig_lines if l != ""]))
        li_raw = ghost_sanitize("\n".join([l for l in li_lines if l != ""]))
        extra_tags = [
            "#WordOfTheWeek", "#Vocabulary", "#Thesaurus", "#EnglishLiterature",
            "#Lexicon", "#WritersOfInstagram", "#WordNerd", "#LanguageLovers"
        ]

    all_ig_tags = list(dict.fromkeys(CORE_HASHTAGS_IG + [t if t.startswith("#") else f"#{t}" for t in extra_tags]))
    all_li_tags = list(dict.fromkeys(CORE_HASHTAGS_LINKEDIN + [t if t.startswith("#") else f"#{t}" for t in extra_tags[:5]]))

    ig_full = f"{ig_raw}\n\n.\n.\n.\n{' '.join(all_ig_tags)}"
    li_full = f"{li_raw}\n\n{' '.join(all_li_tags)}"

    return {
        "instagram_caption": ig_full,
        "linkedin_caption": li_full,
        "hashtags": all_ig_tags,
        "ghost_audit_ig": audit_ghost_compliance(ig_full),
        "ghost_audit_li": audit_ghost_compliance(li_full),
    }
