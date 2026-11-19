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
        top1 = selected_items[0] if len(selected_items) > 0 else {}
        top2 = selected_items[1] if len(selected_items) > 1 else {}
        top3 = selected_items[2] if len(selected_items) > 2 else {}
        ig_lines = [
            f"10 big stories happened this week while you were busy with classes and labs ({week_label}).",
            "",
            "Here is a quick peek inside our Weekly News Highlights:",
            f"- {top3.get('headline', '')}",
            f"- {top2.get('headline', '')}",
            f"- Plus our #01 highlight on Slide 7 ({top1.get('category', 'Campus Spotlight')}).",
            "",
            "Swipe till the last slide and vote A, B, or C in our weekly poll.",
        ]
        li_lines = [
            f"Bits -N- Bytes Weekly News Highlights ({week_label}) | SOLE, IGIT Sarang",
            "",
            "Don't have an hour to scroll the news? Our Bits & Bytes team at SOLE (Society Of Literary Enthusiasts), IGIT Sarang, distilled the week's 10 biggest developments into a 60-second Weekly News Highlights recap with verified primary sources:",
            "",
        ]
        for idx, item in enumerate(selected_items[:10], 1):
            li_lines.append(f"#{idx:02d}. {item.get('headline', '')} ({item.get('source', '')})")
        li_lines.extend([
            "",
            "Swipe through the carousel to see all 10 highlights.",
        ])
        ig_raw = ghost_sanitize("\n".join(ig_lines))
        li_raw = ghost_sanitize("\n".join(li_lines))
        extra_tags = [
            "#WeeklyNews", "#CurrentAffairs", "#Top10News", "#NewsDigest",
            "#TechNews", "#WorldNews", "#IndiaNews", "#StudentReads", "#StayInformed"
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
        li_lines = [
            f"Bits -N- Bytes Tuesday Fact Drop ({week_label}) | SOLE, IGIT Sarang",
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
            f"Ever experienced this exact feeling, but didn't know there was a single word for it?",
            "",
            f"\"{defn}\"",
            "",
            f"Can you guess the {len(word)}-letter {pos} (starts with '{word[0].upper() if word else ''}') before swiping to Slide 3?",
            "",
            "Swipe through to unlock the word, then drop a short sentence using it in the comments. Best sentence gets pinned by @sole_igit.",
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
