#!/usr/bin/env python3
"""
100% Standalone, Zero-Subscription, Offline-Capable Automation Engine
for SOLE — Bits & Bytes (IGIT Sarang, @sole_igit).

Runs autonomously on free GitHub Actions cron runners (even when your laptop is off)
OR inside Docker (`docker compose up -d`).

Zero Paid Subscriptions Required ($0/month):
- Content Discovery: Direct RSS/Atom feeds (The Hindu, Indian Express, Nature,
  Ars Technica, The Guardian Books, Hacker News), Curated Facts Archive + filtered
  Wikipedia API, Curated Literary Vocabulary Bank + Free Dictionary/Datamuse API.
- AI Caption Refinement (optional): Local Ollama (`gemma4:e2b`) or free Google AI Studio
  (`GEMINI_API_KEY`), with deterministic `/GHOST` sanitizer & fallback.
- Graphic & Carousel Design: Built-in Pillow 1080x1350 JPG + dated Carousel PDF renderer.
- Email Delivery: RFC-5322 compliant multipart email (clean plain-text + HTML with inline
  HD logos + JPG slides & dated Carousel PDF) via Gmail TLS SMTP (`smtp.gmail.com:587`).
"""

import argparse
import email.encoders
import email.utils
import html as html_lib
import json
import mimetypes
import os
import re
import smtplib
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from dedup_ledger import commit_selected, filter_and_rank_candidates, load_history
from ghost_caption import build_captions, ghost_sanitize
from package_and_deliver import (
    BASE_DIR,
    OUTPUT_ROOT,
    build_html_email,
    build_markdown_brief,
    build_plain_text_email,
    format_date_code,
    load_contacts,
    render_content_block_html,
    render_signature_html,
    resolve_recipients,
)
from render_designs import render_package_designs

IST = timezone(timedelta(hours=5, minutes=30))

# Canonical IST Mail Schedule (weekday: 0=Mon .. 6=Sun)
MAIL_DAY_MAP: Dict[int, str] = {
    1: "facts",  # Tuesday 6:00 PM IST -> Wednesday post
    2: "vocab",  # Wednesday 6:00 PM IST -> Thursday post
    5: "news",   # Saturday 6:00 PM IST -> Sunday post
}

# Free RSS Feeds for Weekly Top 10 News (No API keys or subscriptions required)
FREE_NEWS_FEEDS = [
    ("SCIENCE & TECH", "The Hindu Sci-Tech", "https://www.thehindu.com/sci-tech/science/feeder/default.rss"),
    ("HIGHER EDUCATION", "Indian Express Education", "https://indianexpress.com/section/education/feed/"),
    ("TECHNOLOGY", "Ars Technica", "https://feeds.arstechnica.com/arstechnica/index"),
    ("SCIENCE", "Nature News", "https://www.nature.com/nature.rss"),
    ("INDIA & POLICY", "The Hindu National", "https://www.thehindu.com/news/national/feeder/default.rss"),
    ("LITERATURE & BOOKS", "The Guardian Books", "https://www.theguardian.com/books/rss"),
    ("COMPUTING", "ScienceDaily Tech", "https://www.sciencedaily.com/rss/top/technology.xml"),
]

JUNK_NEWS_PATTERNS = [
    r"\bdaily quiz\b",
    r"^watch\s*\|",
    r"\bschool assembly\b",
    r"\bcrossword\b",
    r"\bhoroscope\b",
    r"\blive updates?\b",
    r"\blive blog\b",
    r"\bweb stor(?:y|ies)\b",
    r"\bpodcast\b",
    r"^ask hn:",
    r"^show hn:",
    r"^launch hn:",
]

# Curated Literary Vocabulary Bank (28 words + live API fallback when exhausted)
VOCAB_WORD_BANK = [
    {
        "word": "Vellichor",
        "pronunciation": "/ˈvɛl.ɪ.kɔːr/",
        "part_of_speech": "noun",
        "definition": "The strange wistfulness and rich atmosphere of used bookstores, filled with thousands of old books you may never have time to read.",
        "example": "Walking into the quiet corner of the central library before semester exams gave everyone a sudden sense of vellichor.",
        "synonyms": ["bibliophilia", "nostalgia", "reverie", "wistfulness"],
        "antonyms": ["indifference", "apathy", "detachment"],
        "etymology": "Coined by John Koenig in The Dictionary of Obscure Sorrows, blending 'vellum' (parchment) and 'ichor' (ethereal fluid).",
    },
    {
        "word": "Perspicacious",
        "pronunciation": "/ˌpɜː.spɪˈkeɪ.ʃəs/",
        "part_of_speech": "adjective",
        "definition": "Having a ready insight into and sharp understanding of subtle things; mentally discerning and perceptive.",
        "example": "Her perspicacious critique during the SOLE literary debate uncovered the hidden irony in the author's final chapter.",
        "synonyms": ["astute", "discerning", "shrewd", "perceptive"],
        "antonyms": ["obtuse", "unobservant", "naive"],
        "etymology": "From Latin 'perspicax' meaning 'sharp-sighted', from 'perspicere' (to look closely into).",
    },
    {
        "word": "Ephemeral",
        "pronunciation": "/ɪˈfɛm.ər.əl/",
        "part_of_speech": "adjective",
        "definition": "Lasting for a very short time; fleeting, transitory, and prized precisely because it does not endure.",
        "example": "Winter mornings in Sarang have an ephemeral mist over the hostel grounds that vanishes before the first lecture begins.",
        "synonyms": ["fleeting", "transient", "evanescent", "momentary"],
        "antonyms": ["perennial", "enduring", "eternal"],
        "etymology": "From Greek 'ephemeros' meaning 'lasting only one day'.",
    },
    {
        "word": "Equanimity",
        "pronunciation": "/ˌɛk.wəˈnɪm.ɪ.ti/",
        "part_of_speech": "noun",
        "definition": "Mental calmness, composure, and evenness of temper, especially in a high-pressure or difficult situation.",
        "example": "Debugging a segmentation fault ten minutes before the lab evaluation requires rare equanimity.",
        "synonyms": ["composure", "poise", "serenity", "aplomb"],
        "antonyms": ["agitation", "anxiety", "discomposure"],
        "etymology": "From Latin 'aequanimitas', from 'aequus' (even) + 'animus' (mind).",
    },
    {
        "word": "Susurrus",
        "pronunciation": "/sʊˈsʌr.əs/",
        "part_of_speech": "noun",
        "definition": "A low, soft whispering, murmuring, or rustling sound, like wind moving through leaves or pages turning in a reading room.",
        "example": "A quiet susurrus of turning notebook pages filled the auditorium right before the guest speaker stepped up to the podium.",
        "synonyms": ["murmur", "whisper", "rustle", "sigh"],
        "antonyms": ["clamor", "uproar", "din"],
        "etymology": "Directly from Latin 'susurrus' meaning 'a humming, muttering, or whisper'.",
    },
    {
        "word": "Quixotic",
        "pronunciation": "/kwɪkˈsɒt.ɪk/",
        "part_of_speech": "adjective",
        "definition": "Exceedingly idealistic, romantic, and optimistic; pursuing noble goals without regard to practicality.",
        "example": "Rewriting the entire project codebase from scratch the night before submission was a quixotic adventure.",
        "synonyms": ["idealistic", "visionary", "chivalrous", "impractical"],
        "antonyms": ["pragmatic", "realistic", "hardheaded"],
        "etymology": "Named after Cervantes' literary hero Don Quixote.",
    },
    {
        "word": "Mellifluous",
        "pronunciation": "/məˈlɪf.lu.əs/",
        "part_of_speech": "adjective",
        "definition": "Sweet or musical; pleasant and smooth to hear, typically describing a voice, verse, or acoustic melody.",
        "example": "The open-mic poetry evening closed with a mellifluous recitation that held the entire quadrangle still.",
        "synonyms": ["euphonious", "dulcet", "lyrical", "harmonious"],
        "antonyms": ["cacophonous", "grating", "discordant"],
        "etymology": "From Late Latin 'mellifluus', combining 'mel' (honey) + 'fluere' (to flow).",
    },
    {
        "word": "Palimpsest",
        "pronunciation": "/ˈpæl.ɪmp.sɛst/",
        "part_of_speech": "noun",
        "definition": "A manuscript page from which earlier writing has been scraped off and reused, yet still bears visible traces of its earlier form.",
        "example": "The old noticeboard outside the department was a palimpsest of five years of fest posters, seminar flyers, and exam schedules.",
        "synonyms": ["chronicle", "manuscript", "overlay", "trace"],
        "antonyms": ["blank slate", "tabula rasa"],
        "etymology": "From Greek 'palimpsestos', meaning 'scraped again'.",
    },
    {
        "word": "Sonder",
        "pronunciation": "/ˈsɒn.dər/",
        "part_of_speech": "noun",
        "definition": "The sudden realization that every random passerby is living a life as vivid, complex, and deeply felt as your own.",
        "example": "Sitting on the train back to campus after semester break brought a quiet wave of sonder while watching strangers on the platform.",
        "synonyms": ["empathy", "awareness", "perspective", "epiphany"],
        "antonyms": ["solipsism", "detachment", "obliviousness"],
        "etymology": "Coined by John Koenig, drawing on German 'sonder-' (special) and French 'sonder' (to probe).",
    },
    {
        "word": "Laconic",
        "pronunciation": "/ləˈkɒn.ɪk/",
        "part_of_speech": "adjective",
        "definition": "Using very few words; expressing much in a concise, pointed, and spare style.",
        "example": "His laconic two-line commit message explained a bug fix that had stumped the team for three days.",
        "synonyms": ["terse", "succinct", "concise", "pithy"],
        "antonyms": ["verbose", "loquacious", "wordy"],
        "etymology": "From Greek 'Lakonikos' (Spartan), referring to the famously brief speech of ancient Spartans.",
    },
    {
        "word": "Petrichor",
        "pronunciation": "/ˈpɛt.rɪ.kɔːr/",
        "part_of_speech": "noun",
        "definition": "The warm, earthy scent produced when rain falls on dry soil after a long stretch of heat.",
        "example": "After a blistering June afternoon in Odisha, the sudden monsoon petrichor pulled everyone out onto the hostel balcony.",
        "synonyms": ["earthiness", "rain-scent", "aroma", "fragrance"],
        "antonyms": ["aridity", "staleness", "dryness"],
        "etymology": "Coined in 1964 by CSIRO researchers from Greek 'petra' (stone) and 'ichor' (ethereal fluid).",
    },
    {
        "word": "Halcyon",
        "pronunciation": "/ˈhæl.si.ən/",
        "part_of_speech": "adjective",
        "definition": "Denoting a period of time in the past that was idyllically peaceful, calm, and golden.",
        "example": "Final-year students often look back on the halcyon evenings of their first winter fest.",
        "synonyms": ["serene", "tranquil", "idyllic", "peaceful"],
        "antonyms": ["turbulent", "chaotic", "stormy"],
        "etymology": "From Greek 'alkyon' (kingfisher), a bird mythically said to calm the sea while nesting.",
    },
    {
        "word": "Apricity",
        "pronunciation": "/əˈprɪs.ɪ.ti/",
        "part_of_speech": "noun",
        "definition": "The gentle warmth of the sun felt on a cold winter day.",
        "example": "Students gathered on the library steps between classes to soak in the December apricity.",
        "synonyms": ["sun-warmth", "radiance", "glow", "balminess"],
        "antonyms": ["chill", "frost", "bleakness"],
        "etymology": "From Latin 'apricitas', derived from 'apricus' meaning 'warmed by the sun'.",
    },
    {
        "word": "Limerence",
        "pronunciation": "/ˈlɪm.ər.əns/",
        "part_of_speech": "noun",
        "definition": "An involuntary state of intense romantic infatuation paired with an acute longing for emotional reciprocation.",
        "example": "Classic Victorian novels frequently blur the line between enduring devotion and fleeting limerence.",
        "synonyms": ["infatuation", "ardor", "yearning", "besottedness"],
        "antonyms": ["indifference", "apathy", "detachment"],
        "etymology": "Coined by psychologist Dorothy Tennov in 1979 to distinguish infatuation from long-term love.",
    },
    {
        "word": "Ineffable",
        "pronunciation": "/ɪnˈɛf.ə.bəl/",
        "part_of_speech": "adjective",
        "definition": "Too great, subtle, or extreme to be captured or expressed adequately in words.",
        "example": "There is an ineffable relief in handing in your final exam paper and walking out into the evening air.",
        "synonyms": ["indescribable", "unutterable", "transcendent", "unspeakable"],
        "antonyms": ["definable", "expressible", "ordinary"],
        "etymology": "From Latin 'ineffabilis', from 'in-' (not) + 'effari' (to speak out).",
    },
    {
        "word": "Soliloquy",
        "pronunciation": "/səˈlɪl.ə.kwi/",
        "part_of_speech": "noun",
        "definition": "An act of speaking one's thoughts aloud when alone or regardless of listeners, especially in drama.",
        "example": "Her rehearsed soliloquy for the college drama competition echoed across the empty seminar hall.",
        "synonyms": ["monologue", "aside", "speech", "address"],
        "antonyms": ["dialogue", "conversation", "colloquy"],
        "etymology": "From Late Latin 'soliloquium', from 'solus' (alone) + 'loqui' (to speak).",
    },
    {
        "word": "Ebullient",
        "pronunciation": "/ɪˈbʌl.jənt/",
        "part_of_speech": "adjective",
        "definition": "Overflowing with cheerful enthusiasm, energy, and high spirits.",
        "example": "The ebullient freshers turned a routine club orientation into a two-hour spontaneous debate.",
        "synonyms": ["exuberant", "buoyant", "vivacious", "spirited"],
        "antonyms": ["subdued", "listless", "gloomy"],
        "etymology": "From Latin 'ebullire' meaning 'to bubble up or boil over'.",
    },
    {
        "word": "Verisimilitude",
        "pronunciation": "/ˌvɛr.ɪ.sɪˈmɪl.ɪ.tjuːd/",
        "part_of_speech": "noun",
        "definition": "The appearance or quality of being true, believable, or grounded in reality within fiction or art.",
        "example": "Small details like hostel tea stalls and power cuts gave the short story unmistakable verisimilitude.",
        "synonyms": ["realism", "authenticity", "plausibility", "credibility"],
        "antonyms": ["implausibility", "artificiality", "absurdity"],
        "etymology": "From Latin 'verisimilitudo', combining 'verus' (true) + 'similis' (similar).",
    },
    {
        "word": "Numinous",
        "pronunciation": "/ˈnjuː.mɪ.nəs/",
        "part_of_speech": "adjective",
        "definition": "Having a strong spiritual or awe-inspiring quality; evoking quiet wonder and transcendence.",
        "example": "Standing under a clear rural sky during a meteor shower feels genuinely numinous.",
        "synonyms": ["awe-inspiring", "sublime", "ethereal", "transcendent"],
        "antonyms": ["mundane", "prosaic", "commonplace"],
        "etymology": "From Latin 'numen' (divine presence or spirit), popularized by Rudolf Otto in 1917.",
    },
    {
        "word": "Iconoclast",
        "pronunciation": "/aɪˈkɒn.ə.klæst/",
        "part_of_speech": "noun",
        "definition": "A person who challenges or overturns cherished beliefs, traditional institutions, or accepted conventions.",
        "example": "Every literary movement begins with an iconoclast who refuses to write in the previous decade's style.",
        "synonyms": ["maverick", "nonconformist", "dissenter", "rebel"],
        "antonyms": ["conformist", "traditionalist", "orthodox"],
        "etymology": "From Greek 'eikonoklastes', literally 'image-breaker'.",
    },
    {
        "word": "Sanguine",
        "pronunciation": "/ˈsæŋ.ɡwɪn/",
        "part_of_speech": "adjective",
        "definition": "Confidently optimistic and positive, especially in an apparently difficult or uncertain situation.",
        "example": "Even after the server crashed an hour before the demo, the team stayed sanguine and shipped a clean fix.",
        "synonyms": ["optimistic", "hopeful", "upbeat", "confident"],
        "antonyms": ["pessimistic", "despondent", "gloomy"],
        "etymology": "From Latin 'sanguineus' (of blood), rooted in medieval temperament theory.",
    },
    {
        "word": "Ephemera",
        "pronunciation": "/ɪˈfɛm.ər.ə/",
        "part_of_speech": "noun",
        "definition": "Things that exist or are used for only a short time, especially printed collectibles like tickets, posters, and pamphlets.",
        "example": "A shoebox of old train tickets, fest passes, and handwritten notes becomes precious campus ephemera years later.",
        "synonyms": ["memorabilia", "keepsakes", "relics", "mementos"],
        "antonyms": ["monuments", "classics", "permanence"],
        "etymology": "Plural of Greek 'ephemeron', meaning 'something lasting only a day'.",
    },
    {
        "word": "Alacrity",
        "pronunciation": "/əˈlæk.rɪ.ti/",
        "part_of_speech": "noun",
        "definition": "Brisk, cheerful readiness and eager willingness to act.",
        "example": "She accepted the invitation to moderate the annual literary panel with unmistakable alacrity.",
        "synonyms": ["eagerness", "enthusiasm", "promptness", "zeal"],
        "antonyms": ["reluctance", "hesitation", "apathy"],
        "etymology": "From Latin 'alacritas', from 'alacer' meaning 'lively, brisk'.",
    },
    {
        "word": "Chiaroscuro",
        "pronunciation": "/kiˌɑː.rəˈskjʊə.rəʊ/",
        "part_of_speech": "noun",
        "definition": "The dramatic interplay of strong light and deep shadow in visual art, cinema, or descriptive prose.",
        "example": "Streetlights filtering through banyan trees cast a striking chiaroscuro across the campus road at night.",
        "synonyms": ["contrast", "shading", "light-and-shadow", "relief"],
        "antonyms": ["flatness", "uniformity", "monotony"],
        "etymology": "From Italian 'chiaro' (clear, bright) + 'scuro' (dark, obscure).",
    },
    {
        "word": "Zeitgeist",
        "pronunciation": "/ˈzaɪt.ɡaɪst/",
        "part_of_speech": "noun",
        "definition": "The defining mood, spirit, and dominant set of ideas characterizing a particular era or generation.",
        "example": "AI-assisted coding and open-source collaboration have reshaped the engineering campus zeitgeist.",
        "synonyms": ["spirit of the age", "ethos", "climate", "temper"],
        "antonyms": ["anachronism", "antiquity"],
        "etymology": "From German 'Zeit' (time) + 'Geist' (spirit).",
    },
    {
        "word": "Recalcitrant",
        "pronunciation": "/rɪˈkæl.sɪ.trənt/",
        "part_of_speech": "adjective",
        "definition": "Having an obstinately uncooperative attitude toward authority, rules, or routine.",
        "example": "No amount of restarting could persuade the recalcitrant lab projector to recognize the HDMI cable.",
        "synonyms": ["unruly", "defiant", "obstinate", "stubborn"],
        "antonyms": ["compliant", "amenable", "cooperative"],
        "etymology": "From Latin 'recalcitrare', literally 'to kick back with the heel'.",
    },
    {
        "word": "Ersatz",
        "pronunciation": "/ˈɛə.zæts/",
        "part_of_speech": "adjective",
        "definition": "Made or used as a substitute, typically an inferior or artificial imitation of the real thing.",
        "example": "An ersatz summary written by skimming only headings rarely survives a real viva question.",
        "synonyms": ["imitation", "artificial", "synthetic", "makeshift"],
        "antonyms": ["authentic", "genuine", "original"],
        "etymology": "Borrowed from German 'Ersatz' meaning 'replacement or substitute'.",
    },
    {
        "word": "Serendipity",
        "pronunciation": "/ˌsɛr.ənˈdɪp.ɪ.ti/",
        "part_of_speech": "noun",
        "definition": "The occurrence of finding valuable, pleasant, or insightful things purely by fortunate chance.",
        "example": "Pulling the wrong volume off the shelf led to pure serendipity: a forgotten anthology of Odia short fiction.",
        "synonyms": ["fortuity", "fluke", "happy accident", "providence"],
        "antonyms": ["misfortune", "design", "premeditation"],
        "etymology": "Coined by Horace Walpole in 1754 from the Persian fairy tale 'The Three Princes of Serendip'.",
    },
]

# Multi-Domain Verifiable Facts Archive (15 curated high-signal facts; always outrank random Wikipedia stubs)
FACTS_ARCHIVE = [
    {
        "category": "LITERATURE & COMPUTING HISTORY",
        "title": "The First Known Computer Algorithm Was Published With Literary Footnotes Longer Than the Paper Itself",
        "fact": "In 1843, Ada Lovelace translated Luigi Menabrea's French article on Charles Babbage's Analytical Engine and appended seven 'Notes' labeled A through G. Her footnotes were nearly three times longer than the original engineering paper and contained Note G, the first published algorithm for computing Bernoulli numbers.",
        "context": "Lovelace called her approach 'poetical science', blending mathematical logic with literary imagination. She also predicted that computing machines could one day compose music and manipulate symbols beyond pure arithmetic.",
        "source": "Bodleian Libraries, University of Oxford",
        "url": "https://bodleian.ox.ac.uk/",
        "relevance_score": 9.6,
        "popularity_score": 9.4,
    },
    {
        "category": "LINGUISTICS & INFORMATION THEORY",
        "title": "Every Human Language Transmits Information at Roughly 39 Bits Per Second",
        "fact": "A cross-linguistic study of 17 languages across Europe, Asia, and the Americas found that while some languages pack more information per syllable and others are spoken at faster syllable rates, they all converge on an average information transmission rate of about 39.15 bits per second.",
        "context": "Languages with dense syllables like Mandarin or English tend to be spoken with fewer syllables per second, whereas syllable-light languages like Spanish or Japanese are spoken faster, balancing out to the same cognitive bandwidth.",
        "source": "Science Advances (Coupé et al.)",
        "url": "https://www.science.org/doi/10.1126/sciadv.aaw2594",
        "relevance_score": 9.5,
        "popularity_score": 9.4,
    },
    {
        "category": "SPACE & ENGINEERING",
        "title": "Voyager 1 Communicates Across 24 Billion Kilometers Using a 23-Watt Transmitter",
        "fact": "NASA's Voyager 1 spacecraft, now in interstellar space over 24 billion kilometers from Earth, transmits telemetry back to the Deep Space Network using roughly 23 watts of radio power, comparable to a standard refrigerator light bulb.",
        "context": "By the time the signal reaches Earth, its power is less than a billionth of a billionth of a watt, requiring 70-meter dish antennas and error-correcting codes to reconstruct each bit.",
        "source": "NASA Jet Propulsion Laboratory (JPL)",
        "url": "https://voyager.jpl.nasa.gov/",
        "relevance_score": 9.5,
        "popularity_score": 9.5,
    },
    {
        "category": "PUBLISHING & TYPOGRAPHY",
        "title": "Oxford University Press Kept a Single Lead-Type Book in Print for 191 Years Before Selling Out Its First Run",
        "fact": "In 1716, Oxford University Press printed 500 copies of a Coptic translation of the New Testament by David Wilkins. The last copy of that original 500-book print run was finally sold in 1907, taking 191 years to clear the warehouse without ever going out of print.",
        "context": "Academic university presses historically served as long-term cultural archives, storing unbound sheets in vaults for over a century until scholars requested them.",
        "source": "Oxford University Press Archives",
        "url": "https://global.oup.com/about/oup_history/",
        "relevance_score": 9.4,
        "popularity_score": 9.2,
    },
    {
        "category": "PHYSICS & TIMEKEEPING",
        "title": "Optical Atomic Clocks Are So Precise They Detect Gravitational Time Dilation Across a Single Millimeter",
        "fact": "Modern strontium optical lattice clocks measure time with such precision that raising one clock by just one millimeter relative to another produces a measurable tick-rate shift predicted by Einstein's general theory of relativity.",
        "context": "These clocks would neither gain nor lose a single second over 300 billion years, more than twenty times the current age of the universe.",
        "source": "JILA / NIST Physical Review Letters",
        "url": "https://www.nist.gov/",
        "relevance_score": 9.5,
        "popularity_score": 9.3,
    },
    {
        "category": "LITERATURE & SCIENCE",
        "title": "Mary Shelley Wrote Frankenstein During the 'Year Without a Summer' Caused by a Volcanic Eruption",
        "fact": "In 1815, Mount Tambora in Indonesia erupted so violently that volcanic ash cooled global temperatures in 1816. Trapped indoors by relentless rain in Geneva, 18-year-old Mary Shelley entered a ghost-story contest with Lord Byron and Percy Shelley and conceived Frankenstein.",
        "context": "That single climate anomaly also inspired Byron's poem 'Darkness' and John Polidori's 'The Vampyre', linking atmospheric physics directly to the birth of modern science fiction.",
        "source": "Smithsonian Magazine",
        "url": "https://www.smithsonianmag.com/",
        "relevance_score": 9.5,
        "popularity_score": 9.3,
    },
    {
        "category": "COMPUTING & LANGUAGE",
        "title": "The Word 'Robot' Came From a 1920 Czech Play, Not an Engineering Lab",
        "fact": "Czech writer Karel Čapek popularized the word 'robot' in his 1920 sci-fi play R.U.R. (Rossum's Universal Robots), suggested by his brother Josef from the Czech word 'robota', meaning forced labor.",
        "context": "Unlike modern metal machines, Čapek's original robots were synthetic biological workers assembled in factories, raising early questions about automation and human dignity.",
        "source": "Oxford English Dictionary / NPR",
        "url": "https://www.oed.com/",
        "relevance_score": 9.4,
        "popularity_score": 9.4,
    },
    {
        "category": "MATHEMATICS & INDIA",
        "title": "Ancient Indian Prosody Inspired Binary-Like Combinatorics Centuries Before Modern Computers",
        "fact": "Around the 3rd to 2nd century BCE, Indian scholar Pingala analyzed Sanskrit poetic meters using short (laghu) and long (guru) syllables in his treatise Chandahshastra, producing a systematic binary enumeration and what later became known as Pascal's triangle (Meru Prastara).",
        "context": "Poetry and discrete mathematics evolved together in classical India, where memorizing exact syllable counts required algorithmic notation.",
        "source": "Indian Journal of History of Science",
        "url": "https://insa.nic.in/",
        "relevance_score": 9.6,
        "popularity_score": 9.3,
    },
    {
        "category": "ASTRONOMY & HISTORY",
        "title": "Oxford University Is Older Than the Aztec Empire",
        "fact": "Teaching existed at Oxford by 1096 CE, and formal university structures grew rapidly after 1167. By contrast, Tenochtitlan, the capital that launched the Aztec Empire, was founded in 1325 CE, more than two centuries later.",
        "context": "Similarly, India's ancient Nalanda Mahavihara operated for over 700 years from the 5th century CE, drawing scholars from across Asia long before European universities formed.",
        "source": "University of Oxford Archives",
        "url": "https://www.ox.ac.uk/about/organisation/history",
        "relevance_score": 9.3,
        "popularity_score": 9.5,
    },
    {
        "category": "BIOLOGY & INFORMATION",
        "title": "A Single Gram of DNA Can Theoretically Store Over 200 Petabytes of Digital Data",
        "fact": "Because DNA encodes information in four nucleotide bases (A, C, G, T) at the molecular scale, researchers have demonstrated storing books, images, and operating systems in synthetic DNA at densities millions of times higher than flash drives.",
        "context": "Unlike hard drives that degrade in decades, properly stored DNA remains readable for thousands of years without consuming electricity.",
        "source": "Nature / Harvard Wyss Institute",
        "url": "https://www.nature.com/",
        "relevance_score": 9.5,
        "popularity_score": 9.3,
    },
    {
        "category": "LITERATURE & CRYPTOGRAPHY",
        "title": "A 50,000-Word Novel Was Written Without Using the Letter 'E' Once - And Then Translated Without 'E' Either",
        "fact": "French author Georges Perec published the 1969 novel La Disparition without a single occurrence of the letter 'e', the most common letter in French. In 1994, Gilbert Adair translated the entire novel into English as A Void while obeying the exact same lipogrammatic constraint.",
        "context": "Perec belonged to Oulipo, a workshop of writers and mathematicians who used strict mathematical constraints to spark creative breakthroughs.",
        "source": "Encyclopaedia Britannica",
        "url": "https://www.britannica.com/",
        "relevance_score": 9.5,
        "popularity_score": 9.3,
    },
    {
        "category": "EARTH SCIENCE & ENGINEERING",
        "title": "The Deepest Hole Ever Drilled by Humans Reached Only 0.2 Percent of the Way to Earth's Center",
        "fact": "The Kola Superdeep Borehole in Russia reached 12,262 meters (12.26 km) in 1989 before temperatures hit 180 degrees Celsius and forced engineers to stop, leaving over 6,350 kilometers of planet still untouched below.",
        "context": "Scientists discovered microscopic plankton fossils 6 kilometers underground and unexpected free-flowing water trapped in fractured rock.",
        "source": "BBC Future / Geological Archives",
        "url": "https://www.bbc.com/future",
        "relevance_score": 9.4,
        "popularity_score": 9.4,
    },
    {
        "category": "COMPUTING & SPACE",
        "title": "Apollo 11's Guidance Computer Had Less RAM Than a Modern USB-C Charger Controller",
        "fact": "The Apollo Guidance Computer that navigated astronauts to the Moon in 1969 operated at 0.043 MHz with just 2,048 words (about 4 KB) of erasable magnetic core memory and 72 KB of hand-woven rope ROM.",
        "context": "Margaret Hamilton's team designed priority-scheduled flight software so resilient that it recovered cleanly from radar overload alarms minutes before touchdown.",
        "source": "NASA History Division",
        "url": "https://www.nasa.gov/history/",
        "relevance_score": 9.5,
        "popularity_score": 9.5,
    },
    {
        "category": "LINGUISTICS & HISTORY",
        "title": "The Earliest Known Recorded Author in Human History Was a Mesopotamian High Priestess",
        "fact": "Around 2285 BCE, Enheduanna, high priestess of the moon god Nanna in Ur, signed her own name to Sumerian temple hymns pressed onto clay tablets, making her the earliest named author known to history.",
        "context": "Her writings predate Homer by more than 1,500 years and establish the first recorded use of the first-person literary voice.",
        "source": "The Morgan Library & Museum",
        "url": "https://www.themorgan.org/",
        "relevance_score": 9.4,
        "popularity_score": 9.2,
    },
    {
        "category": "PHYSICS & ACOUSTICS",
        "title": "The World's Quietest Room Is So Silent You Can Hear Your Own Blood Flowing",
        "fact": "Anechoic chambers like the one at Microsoft's Building 87 measure around -20.6 decibels, absorbing 99.99 percent of sound waves. Without ambient noise, visitors quickly hear their heartbeat, joints, and blood pulsing in their ears.",
        "context": "Engineers use anechoic chambers to test microphones, headphones, and hardware acoustics with near-zero external interference.",
        "source": "Guinness World Records / Microsoft Research",
        "url": "https://www.guinnessworldrecords.com/",
        "relevance_score": 9.3,
        "popularity_score": 9.4,
    },
]


def load_env_file() -> None:
    env_path = BASE_DIR / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        k = k.strip()
        v = v.strip().strip('"').strip("'")
        if k and k not in os.environ:
            os.environ[k] = v


def strip_html_tags(text: str) -> str:
    text = html_lib.unescape(text or "")
    text = re.sub(r"<[^>]+>", " ", text)
    text = html_lib.unescape(text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def call_free_llm_json(prompt: str) -> Optional[Any]:
    """
    Zero-Cost Dual-Mode LLM Caller:
    1. Tries Local Ollama (`OLLAMA_URL`) using `OLLAMA_MODEL` (default `gemma4:e2b`).
    2. Tries Free Google AI Studio API (`GEMINI_API_KEY`) if configured.
    3. Returns None cleanly if neither is reachable so deterministic templates take over.
    """
    ollama_urls = [
        os.environ.get("OLLAMA_URL", "").strip(),
        "http://host.docker.internal:11434",
        "http://127.0.0.1:11434",
    ]
    ollama_model = os.environ.get("OLLAMA_MODEL", "gemma4:e2b")

    for base_url in [u for u in ollama_urls if u]:
        try:
            req_body = json.dumps({
                "model": ollama_model,
                "prompt": prompt,
                "stream": False,
                "format": "json",
            }).encode("utf-8")
            req = urllib.request.Request(
                f"{base_url.rstrip('/')}/api/generate",
                data=req_body,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=25) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                raw_resp = data.get("response", "")
                return json.loads(raw_resp)
        except Exception:
            continue

    gemini_key = os.environ.get("GEMINI_API_KEY", "").strip()
    if gemini_key:
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={gemini_key}"
            req_body = json.dumps({
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"responseMimeType": "application/json"},
            }).encode("utf-8")
            req = urllib.request.Request(
                url,
                data=req_body,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                txt = data["candidates"][0]["content"]["parts"][0]["text"]
                return json.loads(txt)
        except Exception:
            pass

    return None


def _is_junk_news_title(title: str) -> bool:
    low = (title or "").strip().lower()
    if len(low) < 20:
        return True
    return any(re.search(pat, low) for pat in JUNK_NEWS_PATTERNS)


def _clean_rss_summary(desc: str, source_name: str) -> str:
    cleaned = strip_html_tags(desc)
    # Strip Hacker News RSS boilerplate ("Article URL: ... Comments URL: ... Points: ... # Comments: ...")
    if "article url:" in cleaned.lower() and "comments url:" in cleaned.lower():
        return ""
    if len(cleaned) > 260:
        cleaned = cleaned[:257].rsplit(" ", 1)[0] + "..."
    return cleaned


def _score_news_item(category: str, title: str, desc: str) -> Tuple[float, float]:
    """Differentiated heuristic scoring so news items aren't all tied at 9.3/9.2."""
    text = f"{title} {desc}".lower()
    rel = 8.2
    pop = 8.1

    high_rel_terms = ["india", "odisha", "isro", "iit", "nit", "university", "student", "research", "science", "quantum", "space", "book", "literature", "prize", "open-source", "open source", "semiconductor", "climate", "energy"]
    high_pop_terms = ["ai", "space", "isro", "nobel", "booker", "breakthrough", "record", "moon", "mars", "google", "openai", "anthropic", "meta", "nasa", "climate", "health", "cyber"]

    rel_hits = sum(1 for k in high_rel_terms if re.search(rf"\b{re.escape(k)}\b", text))
    pop_hits = sum(1 for k in high_pop_terms if re.search(rf"\b{re.escape(k)}\b", text))

    rel += min(1.3, rel_hits * 0.35)
    pop += min(1.3, pop_hits * 0.35)

    if len(desc) >= 90:
        rel += 0.2
        pop += 0.2
    if category in ("SCIENCE & TECH", "SCIENCE", "LITERATURE & BOOKS", "HIGHER EDUCATION"):
        rel += 0.15

    return round(min(9.9, rel), 1), round(min(9.8, pop), 1)


def _xml_local_tag(tag: str) -> str:
    return tag.rsplit("}", 1)[-1].lower() if tag else ""


def _xml_child_text(elem: ET.Element, *names: str) -> str:
    wanted = {n.lower() for n in names}
    for child in elem:
        if _xml_local_tag(child.tag) in wanted:
            if child.text and child.text.strip():
                return child.text.strip()
            href = child.attrib.get("href", "").strip()
            if href:
                return href
    return ""


def _load_seed_news_candidates() -> List[Dict[str, Any]]:
    """Loads fallback seed news candidates with scores capped below live RSS items."""
    seed_path = BASE_DIR / "data" / "sample_candidates_news.json"
    if not seed_path.exists():
        return []
    seed_data = json.loads(seed_path.read_text(encoding="utf-8"))
    seed_list = seed_data if isinstance(seed_data, list) else seed_data.get("candidates", [])
    fallback_items: List[Dict[str, Any]] = []
    for item in seed_list:
        fallback_item = dict(item)
        fallback_item["relevance_score"] = min(float(fallback_item.get("relevance_score", 7.8)), 7.8)
        fallback_item["popularity_score"] = min(float(fallback_item.get("popularity_score", 7.6)), 7.6)
        fallback_items.append(fallback_item)
    return fallback_items


def collect_live_news() -> List[Dict[str, Any]]:
    """Fetches real-time news from free RSS/RDF/Atom feeds with quality filtering."""
    candidates: List[Dict[str, Any]] = []
    headers = {"User-Agent": "Mozilla/5.0 (compatible; SOLE-BitsAndBytes-Bot/2.1; +https://igitsarang.ac.in)"}

    for category, source_name, feed_url in FREE_NEWS_FEEDS:
        try:
            req = urllib.request.Request(feed_url, headers=headers)
            with urllib.request.urlopen(req, timeout=12) as resp:
                xml_bytes = resp.read()
            root = ET.fromstring(xml_bytes)
            items = [el for el in root.iter() if _xml_local_tag(el.tag) in ("item", "entry")][:20]
            kept_from_feed = 0
            for item in items:
                if kept_from_feed >= 10:
                    break
                title = strip_html_tags(_xml_child_text(item, "title"))
                link = _xml_child_text(item, "link")
                desc = _clean_rss_summary(_xml_child_text(item, "description", "summary", "content"), source_name)
                if _is_junk_news_title(title) or not link:
                    continue
                if len(desc) < 40:
                    continue
                rel, pop = _score_news_item(category, title, desc)
                candidates.append({
                    "category": category,
                    "headline": ghost_sanitize(title),
                    "summary": ghost_sanitize(desc),
                    "source": source_name,
                    "url": link,
                    "relevance_score": rel,
                    "popularity_score": pop,
                })
                kept_from_feed += 1
        except Exception:
            continue

    return candidates


def collect_live_facts() -> List[Dict[str, Any]]:
    """
    Returns curated, verified multi-domain facts first (scored 9.3-9.6),
    with a strictly filtered Wikipedia fallback (scored 8.5/8.4) only as overflow.
    """
    candidates: List[Dict[str, Any]] = [dict(f) for f in FACTS_ARCHIVE]
    headers = {"User-Agent": "SOLE-BitsAndBytes-IGITSarang/2.1 (+https://github.com/yashagrawall/bits-bytes-automation)"}
    skip_wiki_terms = (
        "footballer", "baseball", "basketball", "cricketer", "ice hockey", "rugby",
        "politician", "municipality", "village in", "census-designated place",
        "unincorporated community", "album by", "television series", "video game",
        "actor", "actress", "singer", "species of moth", "species of beetle",
        "highway", "railway station", "disambiguation", "chemical compound used in",
    )
    history = load_history()
    used_titles = {str(f.get("title", "")).strip().lower() for f in history.get("facts", [])}
    unused_curated = [f for f in candidates if f["title"].strip().lower() not in used_titles]
    max_attempts = 8 if not unused_curated else 1

    for _ in range(max_attempts):
        try:
            req = urllib.request.Request("https://en.wikipedia.org/api/rest_v1/page/random/summary", headers=headers)
            with urllib.request.urlopen(req, timeout=10) as resp:
                wdata = json.loads(resp.read().decode("utf-8"))
            extract = ghost_sanitize(wdata.get("extract", ""))
            title = ghost_sanitize(wdata.get("title", ""))
            page_url = wdata.get("content_urls", {}).get("desktop", {}).get("page", "https://en.wikipedia.org")
            low_ext = extract.lower()
            cand_title = f"The Story Behind {title}"
            if (
                title
                and cand_title.lower() not in used_titles
                and len(extract) > 140
                and not any(t in low_ext for t in skip_wiki_terms)
            ):
                candidates.append({
                    "category": "ENCYCLOPEDIC SPOTLIGHT",
                    "title": cand_title,
                    "fact": extract[:360] + ("..." if len(extract) > 360 else ""),
                    "context": f"Documented in encyclopedic archives under '{title}', showing how specific historical and scientific milestones connect to broader human knowledge.",
                    "source": "Wikipedia Archives",
                    "url": page_url,
                    "relevance_score": 8.5,
                    "popularity_score": 8.4,
                })
                break
        except Exception:
            continue
    return candidates


def _fetch_live_vocab_fallback(existing_words: set) -> List[Dict[str, Any]]:
    """Queries Datamuse + Free Dictionary API if the curated local vocab bank is ever exhausted."""
    extras: List[Dict[str, Any]] = []
    seed_topics = ["literature", "philosophy", "astronomy", "poetry", "rhetoric"]
    for topic in seed_topics:
        try:
            dm_url = f"https://api.datamuse.com/words?ml={urllib.parse.quote(topic)}&max=12"
            with urllib.request.urlopen(dm_url, timeout=8) as resp:
                words = [w.get("word", "") for w in json.loads(resp.read().decode("utf-8"))]
            for w in words:
                if not w.isalpha() or len(w) < 7 or w.lower() in existing_words:
                    continue
                dict_url = f"https://api.dictionaryapi.dev/api/v2/entries/en/{urllib.parse.quote(w)}"
                try:
                    with urllib.request.urlopen(dict_url, timeout=8) as dresp:
                        entries = json.loads(dresp.read().decode("utf-8"))
                    entry = entries[0]
                    meaning = entry.get("meanings", [{}])[0]
                    defn_obj = meaning.get("definitions", [{}])[0]
                    defn = defn_obj.get("definition", "").strip()
                    if not defn:
                        continue
                    extras.append({
                        "word": w.capitalize(),
                        "pronunciation": entry.get("phonetic") or f"/{w.lower()}/",
                        "part_of_speech": meaning.get("partOfSpeech", "noun"),
                        "definition": defn,
                        "example": defn_obj.get("example") or f"Her essay used the word '{w}' with striking precision.",
                        "synonyms": (meaning.get("synonyms") or [])[:4] or ["eloquent", "expressive"],
                        "antonyms": (meaning.get("antonyms") or [])[:3] or ["plain"],
                        "etymology": entry.get("origin") or "Documented in English literary dictionaries.",
                        "relevance_score": 8.8,
                        "popularity_score": 8.6,
                    })
                    if len(extras) >= 3:
                        return extras
                except Exception:
                    continue
        except Exception:
            continue
    return extras


def collect_live_vocab() -> List[Dict[str, Any]]:
    """Curates literary vocabulary words from the 28-word bank + live dictionary fallback."""
    candidates: List[Dict[str, Any]] = []
    for entry in VOCAB_WORD_BANK:
        item = dict(entry)
        item.setdefault("relevance_score", 9.5)
        item.setdefault("popularity_score", 9.3)
        candidates.append(item)

    history = load_history()
    used_words = {str(v.get("word", "")).strip().lower() for v in history.get("vocab", [])}
    remaining = [c for c in candidates if c["word"].lower() not in used_words]
    if len(remaining) < 3:
        candidates.extend(_fetch_live_vocab_fallback(used_words))
    return candidates


def send_email_smtp(
    manifest: Dict[str, Any],
    to_override: Optional[str] = None,
    custom_attachments: Optional[List[Tuple[str, Path]]] = None,
    plain_text_body: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Sends an RFC-5322 compliant, inbox-friendly multipart email (`multipart/mixed` ->
    `multipart/alternative` [text/plain + multipart/related [text/html + inline HD logos]])
    with proper `Date`, `Message-ID`, and `Reply-To` headers to avoid spam folders.
    """
    gmail_user = os.environ.get("GMAIL_USER", "").strip()
    gmail_app_password = os.environ.get("GMAIL_APP_PASSWORD", "").replace(" ", "").strip()
    smtp_host = os.environ.get("SMTP_HOST", "smtp.gmail.com")
    smtp_port = int(os.environ.get("SMTP_PORT", "587"))

    if not gmail_user or not gmail_app_password:
        raise RuntimeError(
            "GMAIL_USER or GMAIL_APP_PASSWORD is not configured. "
            "Set them in .env (local) or GitHub Repository Secrets before running with --send-mail."
        )

    to_list = [e.strip() for e in to_override.split(",") if e.strip()] if to_override else list(manifest.get("to_emails", []))
    cc_list = [] if to_override else list(manifest.get("cc_emails", []))

    if not to_list:
        raise RuntimeError("No TO recipients resolved. Configure CONTACTS_JSON secret or config/contacts.json.")
    placeholder_addrs = [e for e in (to_list + cc_list) if e.lower().endswith("@example.com")]
    if placeholder_addrs:
        raise RuntimeError(
            f"Refusing to send live email to placeholder address(es): {placeholder_addrs}. "
            "Set the CONTACTS_JSON GitHub Actions secret or create a real local config/contacts.json."
        )

    sender_name = manifest.get("sender_name") or load_contacts().get("sender", {}).get("name") or "SOLE Bits & Bytes"
    msgid_domain = gmail_user.split("@")[-1] if "@" in gmail_user else "gmail.com"

    msg = MIMEMultipart("mixed")
    msg["From"] = email.utils.formataddr((sender_name, gmail_user))
    msg["Reply-To"] = gmail_user
    msg["To"] = ", ".join(to_list)
    if cc_list:
        msg["Cc"] = ", ".join(cc_list)
    msg["Subject"] = manifest.get("subject", "Bits & Bytes Social Media Post")
    msg["Date"] = email.utils.formatdate(localtime=True)
    msg["Message-ID"] = email.utils.make_msgid(domain=msgid_domain)

    html_content = Path(manifest["email_html_path"]).read_text(encoding="utf-8")
    if not plain_text_body:
        txt_path = manifest.get("email_txt_path")
        if txt_path and Path(txt_path).exists():
            plain_text_body = Path(txt_path).read_text(encoding="utf-8")
        else:
            plain_text_body = strip_html_tags(html_content)

    alt = MIMEMultipart("alternative")
    alt.attach(MIMEText(plain_text_body, "plain", "utf-8"))

    related = MIMEMultipart("related")
    related.attach(MIMEText(html_content, "html", "utf-8"))

    for cid, rel_path, fname in [
        ("igit_logo", "assets/igit_logo_hd.png", "IGIT_Sarang_Logo.png"),
        ("sole_logo", "assets/sole_logo_hd.png", "SOLE_Logo.png"),
    ]:
        logo_p = BASE_DIR / rel_path
        if logo_p.exists():
            logo_part = MIMEBase("image", "png")
            logo_part.set_payload(logo_p.read_bytes())
            email.encoders.encode_base64(logo_part)
            logo_part.add_header("Content-ID", f"<{cid}>")
            logo_part.add_header("Content-Disposition", "inline", filename=fname)
            related.attach(logo_part)

    alt.attach(related)
    msg.attach(alt)

    attached_files = []
    if custom_attachments is not None:
        attach_pairs = custom_attachments
    else:
        design_assets = manifest.get("design_assets", {})
        slide_list = design_assets.get("slide_paths") or design_assets.get("png_paths") or []
        attach_pairs = [(Path(p).name, Path(p)) for p in slide_list]
        pdf_path = design_assets.get("carousel_pdf_path")
        if pdf_path and Path(pdf_path).exists():
            attach_pairs.append((Path(pdf_path).name, Path(pdf_path)))

    for fname, p in attach_pairs:
        if not p.exists():
            continue
        ctype, _ = mimetypes.guess_type(str(p))
        maintype, subtype = (ctype or "application/octet-stream").split("/", 1)
        part = MIMEBase(maintype, subtype)
        part.set_payload(p.read_bytes())
        email.encoders.encode_base64(part)
        part.add_header("Content-Disposition", "attachment", filename=fname)
        msg.attach(part)
        attached_files.append(fname)

    all_recipients = to_list + cc_list
    last_err: Optional[Exception] = None
    for attempt in range(1, 4):
        try:
            with smtplib.SMTP(smtp_host, smtp_port, timeout=180) as server:
                server.ehlo()
                server.starttls()
                server.ehlo()
                server.login(gmail_user, gmail_app_password)
                server.sendmail(gmail_user, all_recipients, msg.as_string())
            last_err = None
            break
        except Exception as exc:
            last_err = exc
            if attempt < 3:
                time.sleep(3 * attempt)
    if last_err is not None:
        raise last_err

    return {
        "sent": True,
        "to": to_list,
        "cc": cc_list,
        "recipients_count": len(all_recipients),
        "attached_files": attached_files,
    }


def already_ran_today(content_type: str, today_iso: str, cooldown_hours: int = 18) -> bool:
    """
    Returns True if this content_type was already emailed to the team today OR
    within the last `cooldown_hours` (guards against a cron slipping past midnight IST
    after a manual send earlier that same evening).
    """
    history = load_history()
    now_ist = datetime.now(IST)
    cutoff = now_ist - timedelta(hours=cooldown_hours)
    for pkg in history.get("packages", []):
        if pkg.get("content_type") != content_type:
            continue
        if pkg.get("email_sent") is not True or pkg.get("is_test_override"):
            continue
        if pkg.get("run_date_iso") == today_iso:
            return True
        created_raw = str(pkg.get("created_at", ""))
        if created_raw.startswith(today_iso):
            return True
        if created_raw:
            try:
                created_dt = datetime.fromisoformat(created_raw)
                if created_dt.tzinfo is None:
                    created_dt = created_dt.replace(tzinfo=IST)
                if created_dt >= cutoff:
                    return True
            except ValueError:
                pass
    return False


def _enforce_source_diversity(items: List[Dict[str, Any]], limit: int = 10, max_per_source: int = 3) -> List[Dict[str, Any]]:
    """Prevents a single RSS source from dominating all 10 news slots."""
    selected: List[Dict[str, Any]] = []
    overflow: List[Dict[str, Any]] = []
    counts: Dict[str, int] = {}
    for item in items:
        src = item.get("source", "Unknown")
        if counts.get(src, 0) < max_per_source:
            selected.append(item)
            counts[src] = counts.get(src, 0) + 1
        else:
            overflow.append(item)
        if len(selected) == limit:
            break
    if len(selected) < limit:
        selected.extend(overflow[: limit - len(selected)])
    return selected[:limit]


def run_autonomous_job(
    content_type: str,
    send_mail: bool = True,
    commit_ledger: bool = True,
    date_code: Optional[str] = None,
    to_override: Optional[str] = None,
    force: bool = False,
) -> Dict[str, Any]:
    """
    Executes the full standalone pipeline for `news`, `facts`, or `vocab`:
    1. Idempotency guard (blocks duplicate sends on the same day unless --force / --to-override)
    2. Live Content Collection + Deduplication + Relevance & Popularity Ranking
    3. 1080x1350 Branded JPG Carousel + Dated Carousel PDF Rendering
    4. `/GHOST` Anti-AI Instagram Caption & Unified Hashtag Block
    5. Multipart Email Dispatch (clean plain-text + HTML + inline HD logos + attachments)
    """
    load_env_file()
    now_ist = datetime.now(IST)
    today_iso = now_ist.strftime("%Y-%m-%d")
    date_code = date_code or format_date_code(now_ist)

    if send_mail and not force and not to_override and already_ran_today(content_type, today_iso):
        return {
            "status": "skipped",
            "reason": f"{content_type} was already emailed today ({today_iso}). Pass --force to send again.",
            "content_type": content_type,
            "run_date_iso": today_iso,
        }

    if content_type == "news":
        candidates = collect_live_news()
        limit = 10
    elif content_type == "facts":
        candidates = collect_live_facts()
        limit = 1
    elif content_type == "vocab":
        candidates = collect_live_vocab()
        limit = 1
    else:
        raise ValueError(f"Unsupported content_type: {content_type}")

    dedup_limit = 25 if content_type == "news" else limit
    dedup_result = filter_and_rank_candidates(content_type, candidates, limit=dedup_limit)
    selected_items = dedup_result["selected"]
    if content_type == "news":
        # Merge seed fallback ONLY for offline/dry-runs (never mix placeholder URLs into live emails)
        if len(selected_items) < 10 and not send_mail:
            seed_candidates = _load_seed_news_candidates()
            if seed_candidates:
                dedup_result = filter_and_rank_candidates(
                    content_type,
                    candidates + seed_candidates,
                    limit=dedup_limit,
                )
                selected_items = dedup_result["selected"]
        selected_items = _enforce_source_diversity(selected_items, limit=10, max_per_source=3)
        if send_mail and len(selected_items) < 3:
            raise RuntimeError(
                f"Live RSS feeds returned only {len(selected_items)} unique news items (need >= 3); "
                "refusing to send email with placeholder seed links."
            )
    else:
        selected_items = selected_items[:limit]

    if not selected_items:
        raise RuntimeError(f"No non-duplicate items available for {content_type}")

    # Optional LLM caption refinement (Instagram-only, strict plain text, no embedded hashtags)
    use_llm = os.environ.get("ENABLE_LLM_CAPTIONS", "false").strip().lower() in ("1", "true", "yes")
    custom_caption = None
    if use_llm:
        custom_caption = call_free_llm_json(
            f"Write ONE concise Instagram caption for @sole_igit (SOLE, IGIT Sarang) Bits & Bytes ({content_type}). "
            f"Items: {json.dumps(selected_items)}. "
            "Strict rules: "
            "1. NO em dashes or en dashes. "
            "2. NO Markdown formatting (never use **bold** or backticks). "
            "3. NO hashtags inside the 'instagram' text (put hashtags ONLY in the 'hashtags' array). "
            "4. NO AI buzzwords (delve, tapestry, testament, pivotal, vibrant, seamless, crucial, fostering). "
            "5. NO 'link in bio' filler. "
            "Return JSON with keys: instagram (string), hashtags (array of 8 strings)."
        )
        if not isinstance(custom_caption, dict):
            custom_caption = None

    contacts = load_contacts()
    sched_info = contacts.get("schedule", {}).get(content_type, {})
    content_title = sched_info.get("content_type", content_type.upper())

    slug = f"{date_code}_{content_type}".replace(" ", "_")
    pkg_dir = OUTPUT_ROOT / slug
    pkg_dir.mkdir(parents=True, exist_ok=True)

    design_res = render_package_designs(content_type, selected_items, date_code, pkg_dir)
    captions = build_captions(content_type, selected_items, date_code, custom_caption=custom_caption)
    to_emails, cc_emails = resolve_recipients(contacts)
    subject = f"[{date_code}] : Bits & Bytes Social Media Post : {content_title}"

    email_html = build_html_email(
        content_type=content_type,
        content_title=content_title,
        date_code=date_code,
        selected_items=selected_items,
        captions=captions,
        contacts=contacts,
        slide_count=design_res["slide_count"],
        carousel_pdf_name=design_res["carousel_pdf_name"],
    )
    email_html_path = pkg_dir / "email_body.html"
    email_html_path.write_text(email_html, encoding="utf-8")

    email_txt = build_plain_text_email(
        content_type=content_type,
        content_title=content_title,
        date_code=date_code,
        selected_items=selected_items,
        captions=captions,
        contacts=contacts,
        slide_count=design_res["slide_count"],
        carousel_pdf_name=design_res["carousel_pdf_name"],
    )
    email_txt_path = pkg_dir / "email_body.txt"
    email_txt_path.write_text(email_txt, encoding="utf-8")

    md_brief = build_markdown_brief(
        content_type=content_type,
        content_title=content_title,
        date_code=date_code,
        selected_items=selected_items,
        captions=captions,
        contacts=contacts,
        to_emails=to_emails,
        cc_emails=cc_emails,
    )
    md_brief_path = pkg_dir / "post_brief.md"
    md_brief_path.write_text(md_brief, encoding="utf-8")

    manifest: Dict[str, Any] = {
        "status": "ok",
        "package_id": slug,
        "content_type": content_type,
        "content_title": content_title,
        "date_code": date_code,
        "run_date_iso": today_iso,
        "subject": subject,
        "to_emails": to_emails,
        "cc_emails": cc_emails,
        "selected_items": selected_items,
        "deduplication_stats": {
            "total_candidates": dedup_result["total_candidates"],
            "rejected_duplicates_count": dedup_result["rejected_duplicates_count"],
            "selected_count": len(selected_items),
        },
        "design_assets": design_res,
        "captions": captions,
        "email_html_path": str(email_html_path),
        "email_txt_path": str(email_txt_path),
        "markdown_brief_path": str(md_brief_path),
    }

    if send_mail:
        manifest["email_delivery"] = send_email_smtp(manifest, to_override=to_override)

    manifest_path = pkg_dir / "package_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")

    if commit_ledger and not to_override:
        try:
            rel_manifest = str(manifest_path.relative_to(BASE_DIR))
        except ValueError:
            rel_manifest = str(manifest_path)
        commit_selected(content_type, selected_items, package_meta={
            "package_id": slug,
            "content_type": content_type,
            "run_date_iso": today_iso,
            "subject": subject,
            "manifest_path": rel_manifest,
            "email_sent": manifest.get("email_delivery", {}).get("sent", False),
            "is_test_override": bool(to_override),
        })

    return manifest


def _parse_schedule_time_ist(contacts: Dict[str, Any], content_type: str) -> Tuple[int, int]:
    """Parses (hour, minute) from config/contacts.json cron_mail (default 18:00 IST)."""
    cron_str = contacts.get("schedule", {}).get(content_type, {}).get("cron_mail", "")
    m = re.search(r"(\d{1,2})\s+(\d{1,2})\s+\*\s+\*\s+\d", cron_str)
    if m:
        return int(m.group(2)), int(m.group(1))
    return 18, 0


class _HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        if self.path in ("/health", "/api/v1/health"):
            body = json.dumps({"status": "healthy", "service": "SOLE Bits & Bytes Engine"}).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format: str, *args: Any) -> None:
        return


def daemon_loop(port: int = 8765) -> None:
    """
    24/7 Docker Daemon Mode:
    - Exposes `/health` endpoint on `0.0.0.0:8765`.
    - Internal scheduler is gated behind `ENABLE_DAEMON_SCHEDULER=true` to prevent
      split-brain duplicate emails alongside GitHub Actions cron.
    - When enabled, checks every 60 seconds and fires ONLY on the exact scheduled IST
      day AND at or after the exact scheduled IST time (18:00 IST on Tue/Wed/Sat).
    """
    load_env_file()
    server = HTTPServer(("0.0.0.0", port), _HealthHandler)
    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()
    print(f"[SOLE Bits & Bytes Daemon] Health endpoint listening on http://0.0.0.0:{port}/health", flush=True)

    scheduler_enabled = os.environ.get("ENABLE_DAEMON_SCHEDULER", "false").strip().lower() in ("1", "true", "yes")
    if not scheduler_enabled:
        print(
            "[SOLE Bits & Bytes Daemon] Internal cron disabled (ENABLE_DAEMON_SCHEDULER=false; "
            "GitHub Actions handles offline Tue/Wed/Sat 18:00 IST sends).",
            flush=True,
        )

    failed_attempts: Dict[Tuple[str, str], int] = {}
    next_retry_at: Dict[Tuple[str, str], float] = {}
    max_daily_failures = 3

    while True:
        if scheduler_enabled:
            try:
                now_ist = datetime.now(IST)
                today_iso = now_ist.strftime("%Y-%m-%d")
                wk = now_ist.weekday()

                if wk in MAIL_DAY_MAP:
                    ctype = MAIL_DAY_MAP[wk]
                    day_key = (ctype, today_iso)
                    if failed_attempts.get(day_key, 0) >= max_daily_failures:
                        time.sleep(60)
                        continue
                    if time.time() < next_retry_at.get(day_key, 0.0):
                        time.sleep(60)
                        continue

                    contacts = load_contacts()
                    target_hour, target_minute = _parse_schedule_time_ist(contacts, ctype)
                    if (now_ist.hour, now_ist.minute) >= (target_hour, target_minute):
                        if not already_ran_today(ctype, today_iso):
                            print(
                                f"[SOLE Bits & Bytes Daemon] Triggering scheduled {ctype} job at "
                                f"{now_ist.strftime('%Y-%m-%d %H:%M IST')}...",
                                flush=True,
                            )
                            res = run_autonomous_job(ctype, send_mail=True, commit_ledger=True)
                            failed_attempts.pop(day_key, None)
                            next_retry_at.pop(day_key, None)
                            print(f"[SOLE Bits & Bytes Daemon] Completed {res.get('package_id', res.get('status'))}", flush=True)
            except Exception as exc:
                now_ist = datetime.now(IST)
                today_iso = now_ist.strftime("%Y-%m-%d")
                wk = now_ist.weekday()
                if wk in MAIL_DAY_MAP:
                    day_key = (MAIL_DAY_MAP[wk], today_iso)
                    attempts = failed_attempts.get(day_key, 0) + 1
                    failed_attempts[day_key] = attempts
                    backoff_sec = 900 * attempts  # 15m, 30m, then stop for the day
                    next_retry_at[day_key] = time.time() + backoff_sec
                    print(
                        f"[SOLE Bits & Bytes Daemon] Error in check loop (attempt {attempts}/{max_daily_failures}): {exc}",
                        file=sys.stderr,
                        flush=True,
                    )
                else:
                    print(f"[SOLE Bits & Bytes Daemon] Error in check loop: {exc}", file=sys.stderr, flush=True)

        time.sleep(60)


def run_combined_sample_email(
    send_mail: bool = True,
    commit_ledger: bool = False,
    to_override: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Generates ONE single email using the exact same canonical HTML blocks and signature
    as regular scheduled emails, containing fresh editions of News, Fact, and Vocabulary
    with dated Carousel PDFs attached.
    """
    load_env_file()
    now_ist = datetime.now(IST)
    date_code = format_date_code(now_ist)
    contacts = load_contacts()
    sender = contacts.get("sender", {})
    to_emails, cc_emails = resolve_recipients(contacts)

    news_pkg = run_autonomous_job("news", send_mail=False, commit_ledger=False, date_code=date_code, force=True)
    fact_pkg = run_autonomous_job("facts", send_mail=False, commit_ledger=False, date_code=date_code, force=True)
    vocab_pkg = run_autonomous_job("vocab", send_mail=False, commit_ledger=False, date_code=date_code, force=True)

    news_pdf_name = news_pkg["design_assets"]["carousel_pdf_name"]
    fact_pdf_name = fact_pkg["design_assets"]["carousel_pdf_name"]
    vocab_pdf_name = vocab_pkg["design_assets"]["carousel_pdf_name"]

    news_block = render_content_block_html("news", news_pkg["selected_items"], heading=f"1. Weekly News Highlights (Attached: {news_pdf_name})")
    fact_block = render_content_block_html("facts", fact_pkg["selected_items"], heading=f"2. Random Fact of the Week (Attached: {fact_pdf_name})")
    vocab_block = render_content_block_html("vocab", vocab_pkg["selected_items"], heading=f"3. Random Vocabulary / Thesaurus (Attached: {vocab_pdf_name})")

    news_cap = html_lib.escape(news_pkg["captions"]["instagram_caption"]).replace("\n", "<br>")
    fact_cap = html_lib.escape(fact_pkg["captions"]["instagram_caption"]).replace("\n", "<br>")
    vocab_cap = html_lib.escape(vocab_pkg["captions"]["instagram_caption"]).replace("\n", "<br>")
    sig_html = render_signature_html(sender)

    combined_html = f"""<!DOCTYPE html>
<html>
<body style="font-family:Arial,Helvetica,sans-serif;color:#1e293b;line-height:1.6;max-width:820px;margin:0 auto;padding:12px;">
  <p style="margin-top:0;">Hi Social Media &amp; Design Team Leads,</p>
  <p>Please find below a combined sample of all three <b>Bits &amp; Bytes</b> post types (<b>Weekly News Highlights</b>, <b>Random Fact</b>, and <b>Random Vocabulary / Thesaurus</b>) for <b>{html_lib.escape(date_code)}</b>, with Instagram captions for <b>@sole_igit</b> and dated 1080&times;1350 carousel PDFs attached. You are free to use the attached designs directly or create a new design from this content.</p>

  <hr style="border:none;border-top:1px solid #cbd5e1;margin:20px 0;">
  {news_block}
  <p style="margin:8px 0 4px 0;"><b>Instagram Caption &amp; Hashtags (@sole_igit):</b></p>
  <div style="background:#f8fafc;border-left:3px solid #0887A8;padding:14px 16px;font-size:14px;line-height:1.55;margin-bottom:24px;">{news_cap}</div>

  <hr style="border:none;border-top:1px solid #cbd5e1;margin:20px 0;">
  {fact_block}
  <p style="margin:8px 0 4px 0;"><b>Instagram Caption &amp; Hashtags (@sole_igit):</b></p>
  <div style="background:#f8fafc;border-left:3px solid #0887A8;padding:14px 16px;font-size:14px;line-height:1.55;margin-bottom:24px;">{fact_cap}</div>

  <hr style="border:none;border-top:1px solid #cbd5e1;margin:20px 0;">
  {vocab_block}
  <p style="margin:8px 0 4px 0;"><b>Instagram Caption &amp; Hashtags (@sole_igit):</b></p>
  <div style="background:#f8fafc;border-left:3px solid #0887A8;padding:14px 16px;font-size:14px;line-height:1.55;margin-bottom:26px;">{vocab_cap}</div>

{sig_html}
</body>
</html>"""

    fact_item = fact_pkg["selected_items"][0]
    vocab_item = vocab_pkg["selected_items"][0]
    plain_lines = [
        "Hi Social Media & Design Team Leads,",
        "",
        f"Combined Bits & Bytes sample for {date_code} (attached: {news_pdf_name}, {fact_pdf_name}, {vocab_pdf_name}):",
        "",
        f"1. WEEKLY NEWS HIGHLIGHTS (Attached: {news_pdf_name})",
        "-" * 60,
    ]
    for idx, item in enumerate(news_pkg["selected_items"], 1):
        plain_lines.append(f"#{idx:02d} [{item.get('category', 'General')}] {item.get('headline', '')}")
        plain_lines.append(f"    {item.get('summary', '')}")
        plain_lines.append(f"    Source: {item.get('source', 'Source')} ({item.get('url', '')})")
    plain_lines.extend([
        "",
        "Instagram Caption (@sole_igit):",
        news_pkg["captions"]["instagram_caption"],
        "",
        f"2. RANDOM FACT OF THE WEEK (Attached: {fact_pdf_name})",
        "-" * 60,
        f"Title: {fact_item.get('title', '')}",
        f"Fact: {fact_item.get('fact', '')}",
        f"Context: {fact_item.get('context', '')}",
        f"Primary Source: {fact_item.get('source', 'Verified')} ({fact_item.get('url', '')})",
        "",
        "Instagram Caption (@sole_igit):",
        fact_pkg["captions"]["instagram_caption"],
        "",
        f"3. RANDOM VOCABULARY / THESAURUS (Attached: {vocab_pdf_name})",
        "-" * 60,
        f"Word: {vocab_item.get('word', '')} ({vocab_item.get('pronunciation', '')} | {vocab_item.get('part_of_speech', '')})",
        f"Definition: {vocab_item.get('definition', '')}",
        f"Example: \"{vocab_item.get('example', '')}\"",
        f"Synonyms: {', '.join(vocab_item.get('synonyms', []))}",
        f"Antonyms: {', '.join(vocab_item.get('antonyms', []))}",
        f"Etymology: {vocab_item.get('etymology', '')}",
        "",
        "Instagram Caption (@sole_igit):",
        vocab_pkg["captions"]["instagram_caption"],
        "",
        "--",
        sender.get("name", "SOLE Bits & Bytes Maintainer"),
        sender.get("batch_branch", ""),
        sender.get("role", "Bits & Bytes SOLE"),
        sender.get("college", "IGIT Sarang"),
        f"Ph. No. {sender.get('phone', '')}",
        f"Instagram Handle : {sender.get('instagram_handle', '@sole_igit')} ({sender.get('instagram_url', 'https://www.instagram.com/sole_igit/')})",
        f"LinkedIn Handle : {sender.get('linkedin_handle', '')} ({sender.get('linkedin_url', 'https://www.linkedin.com/')})",
    ])

    out_dir = OUTPUT_ROOT / f"{date_code}_combined_sample"
    out_dir.mkdir(parents=True, exist_ok=True)
    html_path = out_dir / "email_body.html"
    html_path.write_text(combined_html, encoding="utf-8")
    txt_path = out_dir / "email_body.txt"
    txt_path.write_text("\n".join(plain_lines), encoding="utf-8")

    subject = f"[{date_code}] : Bits & Bytes Social Media Post : Complete Sample (News, Fact & Vocabulary)"
    manifest = {
        "package_id": f"{date_code}_combined_sample",
        "subject": subject,
        "to_emails": to_emails,
        "cc_emails": cc_emails,
        "email_html_path": str(html_path),
        "email_txt_path": str(txt_path),
        "news_word_fact_summary": {
            "news_top1": news_pkg["selected_items"][0].get("headline"),
            "fact_title": fact_item.get("title"),
            "vocab_word": vocab_item.get("word"),
        },
    }

    custom_attachments = [
        (news_pdf_name, Path(news_pkg["design_assets"]["carousel_pdf_path"])),
        (fact_pdf_name, Path(fact_pkg["design_assets"]["carousel_pdf_path"])),
        (vocab_pdf_name, Path(vocab_pkg["design_assets"]["carousel_pdf_path"])),
    ]

    if send_mail:
        manifest["email_delivery"] = send_email_smtp(
            manifest,
            to_override=to_override,
            custom_attachments=custom_attachments,
            plain_text_body="\n".join(plain_lines),
        )

    if commit_ledger and not to_override:
        today_iso = now_ist.strftime("%Y-%m-%d")
        sent_ok = manifest.get("email_delivery", {}).get("sent", False)
        try:
            rel_html = str(html_path.relative_to(BASE_DIR))
        except ValueError:
            rel_html = str(html_path)
        for ctype, pkg in [("news", news_pkg), ("facts", fact_pkg), ("vocab", vocab_pkg)]:
            commit_selected(ctype, pkg["selected_items"], package_meta={
                "package_id": pkg["package_id"],
                "content_type": ctype,
                "run_date_iso": today_iso,
                "subject": subject,
                "manifest_path": rel_html,
                "email_sent": sent_ok,
                "is_test_override": bool(to_override),
            })

    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description="Standalone Zero-Subscription Bits & Bytes Automation Engine")
    parser.add_argument("--type", choices=["news", "facts", "vocab", "auto", "combined-sample"], default="auto")
    parser.add_argument("--send-mail", action="store_true", help="Send HTML email with slide & PDF attachments via Gmail SMTP")
    parser.add_argument("--no-commit", action="store_true", help="Dry run without committing to published_history.json")
    parser.add_argument("--force", action="store_true", help="Bypass same-day idempotency guard and send again")
    parser.add_argument("--to-override", default=None, help="Send email ONLY to this comma-separated address list (skips team To/Cc)")
    parser.add_argument("--daemon", action="store_true", help="Run 24/7 inside Docker with HTTP API (and optional exact-time scheduler)")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()

    if args.daemon:
        daemon_loop(port=args.port)
        return

    if args.type == "combined-sample":
        res = run_combined_sample_email(
            send_mail=args.send_mail,
            commit_ledger=False,
            to_override=args.to_override,
        )
        print(json.dumps({
            "status": "ok",
            "package_id": res["package_id"],
            "subject": res["subject"],
            "fresh_items": res["news_word_fact_summary"],
            "email_delivery": res.get("email_delivery"),
        }, indent=2))
        return

    ctype = args.type
    if ctype == "auto":
        now_ist = datetime.now(IST)
        wk = now_ist.weekday()
        if wk not in MAIL_DAY_MAP:
            print(json.dumps({
                "status": "skipped",
                "reason": f"Today ({now_ist.strftime('%A')}, {now_ist.strftime('%Y-%m-%d IST')}) is not a scheduled mail day (Tue=facts, Wed=vocab, Sat=news).",
            }, indent=2))
            return
        ctype = MAIL_DAY_MAP[wk]

    res = run_autonomous_job(
        content_type=ctype,
        send_mail=args.send_mail,
        commit_ledger=not args.no_commit,
        to_override=args.to_override,
        force=args.force,
    )
    if res.get("status") == "skipped":
        print(json.dumps(res, indent=2))
        return

    print(json.dumps({
        "status": "ok",
        "package_id": res["package_id"],
        "subject": res["subject"],
        "slide_count": res["design_assets"]["slide_count"],
        "carousel_pdf": res["design_assets"]["carousel_pdf_name"],
        "email_delivery": res.get("email_delivery"),
    }, indent=2))


if __name__ == "__main__":
    main()
