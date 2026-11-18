# Multi-Agent Orchestrator for SOLE Bits & Bytes Automation (IGIT Sarang)
# Run with Antigravity's `run_workflow` tool:
#   run_workflow(ScriptPath="/home/yashagrawall/bits-bytes-automation/workflows/bits_bytes_workflow.py", Args={"content_type": "news"})
# Supports content_type in {"news", "facts", "vocab"} (or "all" to run all three).

import json
from pathlib import Path

BASE_DIR = Path("/home/yashagrawall/bits-bytes-automation")
HISTORY_JSON = BASE_DIR / "data" / "published_history.json"

content_type = args.get("content_type", "news") if "args" in dir() and isinstance(args, dict) else "news"
date_code = args.get("date_code", "") if "args" in dir() and isinstance(args, dict) else ""

if HISTORY_JSON.exists():
    history = json.loads(HISTORY_JSON.read_text(encoding="utf-8"))
else:
    history = {"news": [], "facts": [], "vocab": []}

existing_news_titles = [item.get("headline", "") for item in history.get("news", [])[-60:]]
existing_facts = [item.get("title", "") for item in history.get("facts", [])[-60:]]
existing_words = [item.get("word", "") for item in history.get("vocab", [])[-100:]]

phase("1. Multi-Agent Candidate Discovery & Research")

if content_type == "news":
    raw_candidates = await agent(
        prompt=(
            "You are Agent 1 (Weekly News Discovery Agent) for Bits & Bytes, the literary & current-affairs wing of "
            "SOLE (Society Of Literary Enthusiasts) at IGIT Sarang. "
            "Use `search_web` to find 16 distinct, verified major news highlights from the past 7 days across Science & Tech, "
            "India & Policy, Global Affairs, Literature & Culture, and Higher Education/Space. "
            f"Do NOT repeat any of these previously covered headlines: {json.dumps(existing_news_titles)}. "
            "Return an array of 16 candidate objects with fields: category, headline, summary (2 concise sentences), source (publication name), and url."
        ),
        schema={
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "category": {"type": "string"},
                    "headline": {"type": "string"},
                    "summary": {"type": "string"},
                    "source": {"type": "string"},
                    "url": {"type": "string"},
                },
                "required": ["category", "headline", "summary", "source", "url"],
            },
        },
        role="Agent 1: News Discovery",
    )
elif content_type == "facts":
    raw_candidates = await agent(
        prompt=(
            "You are Agent 3 (Random Fact Discovery Agent) for Bits & Bytes, SOLE at IGIT Sarang. "
            "Use `search_web` to curate 5 fascinating, verifiable, lesser-known facts across literature, science, linguistics, history, or technology. "
            f"Do NOT repeat any of these previously covered facts: {json.dumps(existing_facts)}. "
            "Return an array of 5 candidate objects with fields: category, title, fact (2 sentences), context (why it matters / backstory), source, and url."
        ),
        schema={
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "category": {"type": "string"},
                    "title": {"type": "string"},
                    "fact": {"type": "string"},
                    "context": {"type": "string"},
                    "source": {"type": "string"},
                    "url": {"type": "string"},
                },
                "required": ["category", "title", "fact", "context", "source", "url"],
            },
        },
        role="Agent 3: Random Fact Discovery",
    )
else:
    raw_candidates = await agent(
        prompt=(
            "You are Agent 5 (Vocabulary & Thesaurus Discovery Agent) for Bits & Bytes, SOLE at IGIT Sarang. "
            "Curate 5 evocative, literary English vocabulary words that college writers and literary enthusiasts can use. "
            f"Do NOT repeat any of these previously featured words: {json.dumps(existing_words)}. "
            "Return an array of 5 candidate objects with fields: word, pronunciation, part_of_speech, definition, example (a vivid sentence relatable to campus, literature, or life), synonyms (array of 4 strings), antonyms (array of 3 strings), and etymology."
        ),
        schema={
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "word": {"type": "string"},
                    "pronunciation": {"type": "string"},
                    "part_of_speech": {"type": "string"},
                    "definition": {"type": "string"},
                    "example": {"type": "string"},
                    "synonyms": {"type": "array", "items": {"type": "string"}},
                    "antonyms": {"type": "array", "items": {"type": "string"}},
                    "etymology": {"type": "string"},
                },
                "required": ["word", "pronunciation", "part_of_speech", "definition", "example", "synonyms", "antonyms", "etymology"],
            },
        },
        role="Agent 5: Vocabulary Discovery",
    )

phase("2. Parallel Deduplication, Relevance & Popularity Rating")

rel_and_pop = await parallel(
    ["relevance", "popularity"],
    lambda metric: agent(
        prompt=(
            f"You are the {metric.upper()} Rating Agent (Agents 7 & 8) for Bits & Bytes SOLE (IGIT Sarang). "
            f"Score each candidate below from 1.0 to 10.0 on {metric.upper()} for engineering & literary students at IGIT Sarang. "
            f"Candidates: {json.dumps(raw_candidates)}. "
            "Return an array of numbers (1.0 to 10.0) in the exact same order as the input array."
        ),
        schema={"type": "array", "items": {"type": "number"}},
        role=f"Rate {metric.capitalize()}",
    ),
)

rel_scores = rel_and_pop[0] if len(rel_and_pop) > 0 else []
pop_scores = rel_and_pop[1] if len(rel_and_pop) > 1 else []

for idx, cand in enumerate(raw_candidates):
    cand["relevance_score"] = rel_scores[idx] if idx < len(rel_scores) else 8.8
    cand["popularity_score"] = pop_scores[idx] if idx < len(pop_scores) else 8.8

phase("3. /GHOST Anti-AI Caption & Hashtag Generation")

caption_data = await agent(
    prompt=(
        "You are Agent 11 (/GHOST Caption Writer) for SOLE (@sole_igit), the literary society of IGIT Sarang. "
        f"Content Type: {content_type}. Top Candidates: {json.dumps(raw_candidates[:10 if content_type == 'news' else 1])}. "
        "Write an Instagram caption and a LinkedIn caption following `/GHOST` rules: "
        "1. NEVER use em dashes (—) or en dashes (–). "
        "2. NEVER use AI buzzwords (delve, tapestry, testament, pivotal, underscore, landscape, vibrant, seamless, crucial, fostering, moreover, furthermore). "
        "3. Sound like a sharp college student editor at IGIT Sarang talking to peers. "
        "4. Return JSON with fields: instagram (caption text without hashtags), linkedin (post text without hashtags), and hashtags (array of 12 relevant hashtags)."
    ),
    schema={
        "type": "object",
        "properties": {
            "instagram": {"type": "string"},
            "linkedin": {"type": "string"},
            "hashtags": {"type": "array", "items": {"type": "string"}},
        },
        "required": ["instagram", "linkedin", "hashtags"],
    },
    role="Agent 11: /GHOST Caption Writer",
)

candidates_file = BASE_DIR / "data" / f"latest_candidates_{content_type}.json"
candidates_file.write_text(
    json.dumps({"candidates": raw_candidates, "captions": caption_data}, indent=2, ensure_ascii=False),
    encoding="utf-8",
)
log(f"Saved {len(raw_candidates)} scored candidates and /GHOST captions to {candidates_file}")
print(str(candidates_file))
