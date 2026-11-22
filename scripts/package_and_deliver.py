#!/usr/bin/env python3
"""
End-to-End Packaging, Single-Source HTML & Plain-Text Email Builder
for SOLE Bits & Bytes (IGIT Sarang).
"""

import argparse
import html
import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from dedup_ledger import commit_selected, filter_and_rank_candidates
from ghost_caption import build_captions
from render_designs import render_package_designs

BASE_DIR = Path(__file__).resolve().parent.parent
CONTACTS_PATH = BASE_DIR / "config" / "contacts.json"
CONTACTS_EXAMPLE_PATH = BASE_DIR / "config" / "contacts.example.json"
OUTPUT_ROOT = BASE_DIR / "output"


IST = timezone(timedelta(hours=5, minutes=30))


def format_date_code(dt: Optional[datetime] = None) -> str:
    """Formats [YYYY-MMM-WW-dddd] e.g. 2026-Nov-W3-Saturday (IST by default)."""
    dt = dt or datetime.now(IST)
    week_of_month = (dt.day - 1) // 7 + 1
    return f"{dt.strftime('%Y-%b')}-W{week_of_month}-{dt.strftime('%A')}"


def load_contacts() -> Dict[str, Any]:
    """
    Loads recipient roster & sender config in priority order:
    1. `CONTACTS_JSON` environment variable (recommended for GitHub Actions secrets)
    2. `config/contacts.json` (local gitignored file)
    3. `config/contacts.example.json` (redacted fallback for CI & public clones)
    """
    raw_env = os.environ.get("CONTACTS_JSON", "").strip()
    if raw_env:
        return json.loads(raw_env)
    if CONTACTS_PATH.exists():
        with open(CONTACTS_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    with open(CONTACTS_EXAMPLE_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def resolve_recipients(contacts: Dict[str, Any]) -> Tuple[List[str], List[str]]:
    to_emails: List[str] = []
    for group in contacts.get("recipients", {}).get("to", {}).values():
        for person in group:
            email_addr = person.get("email", "").strip()
            if email_addr and email_addr not in to_emails:
                to_emails.append(email_addr)

    cc_emails: List[str] = []
    for group in contacts.get("recipients", {}).get("cc", {}).values():
        for person in group:
            email_addr = person.get("email", "").strip()
            if email_addr and email_addr not in cc_emails and email_addr not in to_emails:
                cc_emails.append(email_addr)

    return to_emails, cc_emails


def render_content_block_html(
    content_type: str,
    selected_items: List[Dict[str, Any]],
    heading: Optional[str] = None,
) -> str:
    """Single canonical HTML renderer for news, facts, and vocab content blocks."""
    if content_type == "news":
        title = heading or "1. Curated Weekly Top 10 News Highlights (with Sources)"
        rows_html = []
        for idx, item in enumerate(selected_items, 1):
            bg = "#ffffff" if idx % 2 == 1 else "#f8fafc"
            hl = html.escape(item.get("headline", ""))
            summary = html.escape(item.get("summary", ""))
            src = html.escape(item.get("source", "Source"))
            url = html.escape(item.get("url", "#"))
            cat = html.escape(item.get("category", "General"))
            rel = item.get("relevance_score", 9.0)
            pop = item.get("popularity_score", 9.0)
            rows_html.append(
                f'<tr style="background-color:{bg};">'
                f'<td style="padding:12px 10px;border:1px solid #cbd5e1;text-align:center;font-weight:700;color:#0887A8;">#{idx:02d}</td>'
                f'<td style="padding:12px 10px;border:1px solid #cbd5e1;font-weight:600;color:#0f172a;">'
                f'<span style="display:inline-block;background:#e0f2fe;color:#0369a1;font-size:11px;padding:2px 8px;border-radius:10px;margin-bottom:4px;">{cat}</span><br>{hl}</td>'
                f'<td style="padding:12px 10px;border:1px solid #cbd5e1;color:#334155;font-size:13.5px;line-height:1.5;">{summary}</td>'
                f'<td style="padding:12px 10px;border:1px solid #cbd5e1;text-align:center;font-size:12.5px;">'
                f'Rel: <b>{rel}</b>/10<br>Pop: <b>{pop}</b>/10</td>'
                f'<td style="padding:12px 10px;border:1px solid #cbd5e1;text-align:center;">'
                f'<a href="{url}" style="color:#0887A8;font-weight:600;text-decoration:none;">{src} &#8599;</a></td>'
                f'</tr>'
            )
        return (
            f'<h3 style="color:#0f172a;margin:20px 0 10px 0;font-size:17px;">{html.escape(title)}</h3>'
            '<table style="width:100%;border-collapse:collapse;font-family:Arial,sans-serif;font-size:14px;margin-bottom:24px;">'
            '<thead>'
            '<tr style="background-color:#070c14;color:#ffffff;">'
            '<th style="padding:12px 10px;border:1px solid #070c14;width:48px;">Rank</th>'
            '<th style="padding:12px 10px;border:1px solid #070c14;width:28%;text-align:left;">Headline</th>'
            '<th style="padding:12px 10px;border:1px solid #070c14;text-align:left;">Highlight Summary</th>'
            '<th style="padding:12px 10px;border:1px solid #070c14;width:90px;">Ratings</th>'
            '<th style="padding:12px 10px;border:1px solid #070c14;width:110px;">Source</th>'
            '</tr>'
            '</thead>'
            f'<tbody>{"".join(rows_html)}</tbody>'
            '</table>'
        )
    if content_type == "facts":
        title = heading or "1. Curated Random Fact of the Week"
        item = selected_items[0]
        return (
            f'<h3 style="color:#0f172a;margin:20px 0 10px 0;font-size:17px;">{html.escape(title)}</h3>'
            '<div style="background:#f8fafc;border-left:5px solid #0887A8;padding:18px 20px;border-radius:8px;margin-bottom:24px;">'
            f'<div style="font-size:12px;font-weight:700;color:#0887A8;text-transform:uppercase;letter-spacing:0.5px;">Category: {html.escape(item.get("category", "General"))}</div>'
            f'<h4 style="margin:6px 0 10px 0;font-size:19px;color:#0f172a;">{html.escape(item.get("title", ""))}</h4>'
            f'<p style="margin:0 0 12px 0;font-size:15px;color:#1e293b;line-height:1.6;"><b>Fact:</b> {html.escape(item.get("fact", ""))}</p>'
            f'<p style="margin:0 0 12px 0;font-size:14px;color:#475569;line-height:1.55;"><b>Context:</b> {html.escape(item.get("context", ""))}</p>'
            f'<div style="font-size:13px;color:#64748b;"><b>Primary Source:</b> <a href="{html.escape(item.get("url", "#"))}" style="color:#0887A8;">{html.escape(item.get("source", "Verified"))}</a> '
            f'&nbsp;|&nbsp; <b>Relevance:</b> {item.get("relevance_score", 9.0)}/10 &nbsp;|&nbsp; <b>Popularity:</b> {item.get("popularity_score", 9.0)}/10</div>'
            '</div>'
        )
    # vocab
    title = heading or "1. Curated Random Vocabulary / Thesaurus of the Week"
    item = selected_items[0]
    syns = ", ".join(item.get("synonyms", []))
    ants = ", ".join(item.get("antonyms", []))
    return (
        f'<h3 style="color:#0f172a;margin:20px 0 10px 0;font-size:17px;">{html.escape(title)}</h3>'
        '<div style="background:#f8fafc;border-left:5px solid #0887A8;padding:18px 20px;border-radius:8px;margin-bottom:24px;">'
        f'<h4 style="margin:0 0 4px 0;font-size:22px;color:#0f172a;">{html.escape(item.get("word", ""))} '
        f'<span style="font-size:14px;font-weight:400;color:#0887A8;">({html.escape(item.get("pronunciation", ""))} &bull; {html.escape(item.get("part_of_speech", ""))})</span></h4>'
        f'<p style="margin:10px 0;font-size:15px;color:#1e293b;line-height:1.6;"><b>Definition:</b> {html.escape(item.get("definition", ""))}</p>'
        f'<p style="margin:8px 0;font-size:14px;color:#334155;font-style:italic;"><b>Example:</b> &ldquo;{html.escape(item.get("example", ""))}&rdquo;</p>'
        f'<p style="margin:8px 0;font-size:13.5px;color:#0f766e;"><b>Synonyms:</b> {html.escape(syns)}</p>'
        f'<p style="margin:4px 0 8px 0;font-size:13.5px;color:#be123c;"><b>Antonyms:</b> {html.escape(ants)}</p>'
        f'<div style="font-size:12.5px;color:#64748b;"><b>Etymology:</b> {html.escape(item.get("etymology", ""))} '
        f'&nbsp;|&nbsp; <b>Relevance:</b> {item.get("relevance_score", 9.0)}/10 &nbsp;|&nbsp; <b>Popularity:</b> {item.get("popularity_score", 9.0)}/10</div>'
        '</div>'
    )


def render_signature_html(sender: Dict[str, Any]) -> str:
    """Single canonical HTML email signature block."""
    return (
        '  <hr style="border:none;border-top:1px solid #cbd5e1;margin:24px 0 16px 0;">\n'
        '  <div style="font-size:13.5px;color:#334155;line-height:1.55;">\n'
        f'    <b>{html.escape(sender.get("name", "SOLE Bits & Bytes Maintainer"))}</b><br>\n'
        f'    {html.escape(sender.get("batch_branch", ""))}<br>\n'
        f'    {html.escape(sender.get("role", "Bits & Bytes SOLE"))}<br>\n'
        f'    {html.escape(sender.get("college", "IGIT Sarang"))}<br>\n'
        f'    Ph. No. {html.escape(sender.get("phone", ""))}<br>\n'
        f'    Instagram Handle : <a href="{html.escape(sender.get("instagram_url", "https://www.instagram.com/sole_igit/"))}" style="color:#0887A8;">{html.escape(sender.get("instagram_handle", "@sole_igit"))}</a><br>\n'
        f'    LinkedIn Handle : <a href="{html.escape(sender.get("linkedin_url", "https://www.linkedin.com/"))}" style="color:#0887A8;">{html.escape(sender.get("linkedin_handle", ""))}</a><br>\n'
        '    <div style="margin-top:12px;">\n'
        '      <img src="cid:igit_logo" alt="IGIT Sarang Logo" style="height:64px;width:auto;vertical-align:middle;margin-right:10px;">\n'
        '      <img src="cid:sole_logo" alt="SOLE Logo" style="height:60px;width:auto;vertical-align:middle;">\n'
        '    </div>\n'
        '  </div>'
    )


def build_html_email(
    content_type: str,
    content_title: str,
    date_code: str,
    selected_items: List[Dict[str, Any]],
    captions: Dict[str, Any],
    contacts: Dict[str, Any],
    drive_folder_url: Optional[str] = None,
    gdoc_url: Optional[str] = None,
    canva_edit_url: Optional[str] = None,
    slide_count: int = 0,
    carousel_pdf_name: Optional[str] = None,
) -> str:
    sender = contacts.get("sender", {})
    content_block = render_content_block_html(content_type, selected_items)
    pdf_label = html.escape(carousel_pdf_name or f"{date_code}_{content_type}.pdf")

    links_items = []
    if drive_folder_url:
        links_items.append(
            f'<li><b>Google Drive Asset Folder ({slide_count} JPG Slides + Carousel PDF + Canva CSV):</b> '
            f'<a href="{html.escape(drive_folder_url)}" style="color:#0887A8;font-weight:600;">Open Drive Folder &#8599;</a></li>'
        )
    if gdoc_url:
        links_items.append(
            f'<li><b>Google Docs Content &amp; Caption Sheet:</b> '
            f'<a href="{html.escape(gdoc_url)}" style="color:#0887A8;font-weight:600;">Open Google Doc &#8599;</a></li>'
        )
    if canva_edit_url:
        links_items.append(
            f'<li><b>Canva Editable Design Template:</b> '
            f'<a href="{html.escape(canva_edit_url)}" style="color:#0887A8;font-weight:600;">Edit in Canva &#8599;</a></li>'
        )
    if not links_items:
        links_items.append(
            f'<li><b>Attached Design Package ({slide_count} Ready-to-Post 1080&times;1350 Slides + Carousel PDF):</b> '
            f'All {slide_count} slides (<code>slide_01.jpg</code> &ndash; <code>slide_{slide_count:02d}.jpg</code>) and '
            f'<code>{pdf_label}</code> are attached to this email.</li>'
            f'<li><b>Design &amp; Posting Note:</b> Feel free to post the attached design directly on <code>@sole_igit</code>, '
            f'or use the content above to create a new design if preferred.</li>'
        )

    ig_caption_html = html.escape(captions.get("instagram_caption", "")).replace("\n", "<br>")
    sig_html = render_signature_html(sender)

    return f"""<!DOCTYPE html>
<html>
<body style="font-family:Arial,Helvetica,sans-serif;color:#1e293b;line-height:1.6;max-width:820px;margin:0 auto;padding:12px;">
  <p style="margin-top:0;">Hi Social Media &amp; Design Team Leads,</p>
  <p>Please find below the curated <b>Bits &amp; Bytes</b> content, Instagram caption for <b>@sole_igit</b>, and attached 1080&times;1350 design slides for <b>{html.escape(content_title)}</b> ({html.escape(date_code)}). You are free to use the attached design directly or create a new design from this content.</p>

  {content_block}

  <h3 style="color:#0f172a;margin:22px 0 8px 0;font-size:16px;">2. Attached Design Files</h3>
  <ul style="padding-left:22px;margin-bottom:22px;">
    {"".join(links_items)}
  </ul>

  <h3 style="color:#0f172a;margin:22px 0 8px 0;font-size:16px;">3. Instagram Caption &amp; Hashtags (@sole_igit)</h3>
  <div style="background:#f8fafc;border-left:3px solid #0887A8;padding:14px 16px;font-size:14px;line-height:1.55;margin-bottom:26px;">
    {ig_caption_html}
  </div>

{sig_html}
</body>
</html>"""


def build_plain_text_email(
    content_type: str,
    content_title: str,
    date_code: str,
    selected_items: List[Dict[str, Any]],
    captions: Dict[str, Any],
    contacts: Dict[str, Any],
    slide_count: int = 0,
    carousel_pdf_name: Optional[str] = None,
) -> str:
    """Clean plain-text counterpart matching the HTML email (no raw Markdown syntax)."""
    sender = contacts.get("sender", {})
    pdf_label = carousel_pdf_name or f"{date_code}_{content_type}.pdf"

    lines = [
        "Hi Social Media & Design Team Leads,",
        "",
        f"Please find below the curated Bits & Bytes content, Instagram caption for @sole_igit, "
        f"and attached 1080x1350 design slides for {content_title} ({date_code}). "
        f"You are free to use the attached design directly or create a new design from this content.",
        "",
    ]

    if content_type == "news":
        lines.append("1. CURATED WEEKLY TOP 10 NEWS HIGHLIGHTS (WITH SOURCES)")
        lines.append("-" * 60)
        for idx, item in enumerate(selected_items, 1):
            lines.append(f"#{idx:02d} [{item.get('category', 'General')}] {item.get('headline', '')}")
            lines.append(f"    {item.get('summary', '')}")
            lines.append(
                f"    Source: {item.get('source', 'Source')} ({item.get('url', '')}) | "
                f"Rel: {item.get('relevance_score', 9.0)}/10, Pop: {item.get('popularity_score', 9.0)}/10"
            )
            lines.append("")
    elif content_type == "facts":
        item = selected_items[0]
        lines.extend([
            "1. CURATED RANDOM FACT OF THE WEEK",
            "-" * 60,
            f"Category: {item.get('category', 'General')}",
            f"Title: {item.get('title', '')}",
            f"Fact: {item.get('fact', '')}",
            f"Context: {item.get('context', '')}",
            f"Primary Source: {item.get('source', 'Verified')} ({item.get('url', '')})",
            f"Scores: Relevance {item.get('relevance_score', 9.0)}/10 | Popularity {item.get('popularity_score', 9.0)}/10",
            "",
        ])
    else:
        item = selected_items[0]
        lines.extend([
            "1. CURATED RANDOM VOCABULARY / THESAURUS OF THE WEEK",
            "-" * 60,
            f"Word: {item.get('word', '')} ({item.get('pronunciation', '')} | {item.get('part_of_speech', '')})",
            f"Definition: {item.get('definition', '')}",
            f"Example: \"{item.get('example', '')}\"",
            f"Synonyms: {', '.join(item.get('synonyms', []))}",
            f"Antonyms: {', '.join(item.get('antonyms', []))}",
            f"Etymology: {item.get('etymology', '')}",
            f"Scores: Relevance {item.get('relevance_score', 9.0)}/10 | Popularity {item.get('popularity_score', 9.0)}/10",
            "",
        ])

    lines.extend([
        "2. ATTACHED DESIGN FILES",
        "-" * 60,
        f"- {slide_count} Ready-to-Post 1080x1350 Slides (slide_01.jpg - slide_{slide_count:02d}.jpg) + {pdf_label}",
        "- Feel free to post the attached design directly on @sole_igit, or use the content above to create a new design.",
        "",
        "3. INSTAGRAM CAPTION & HASHTAGS (@sole_igit)",
        "-" * 60,
        captions.get("instagram_caption", ""),
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
    return "\n".join(lines)


def build_markdown_brief(
    content_type: str,
    content_title: str,
    date_code: str,
    selected_items: List[Dict[str, Any]],
    captions: Dict[str, Any],
    contacts: Dict[str, Any],
    to_emails: List[str],
    cc_emails: List[str],
    drive_folder_url: Optional[str] = None,
) -> str:
    subject = f"[{date_code}] : Bits & Bytes Social Media Post : {content_title}"
    lines = [
        f"# {subject}",
        "",
        f"- **To**: {', '.join(to_emails)}",
        f"- **Cc**: {', '.join(cc_emails)}",
        f"- **Google Drive Folder**: {drive_folder_url or 'Local Package'}",
        "",
        "## Curated Content",
        "",
    ]
    if content_type == "news":
        lines.append("| Rank | Category | Headline | Summary | Ratings | Source |")
        lines.append("| :--- | :--- | :--- | :--- | :--- | :--- |")
        for idx, item in enumerate(selected_items, 1):
            lines.append(
                f"| #{idx:02d} | {item.get('category', '')} | **{item.get('headline', '')}** | "
                f"{item.get('summary', '')} | Rel: {item.get('relevance_score')}/10, Pop: {item.get('popularity_score')}/10 | "
                f"[{item.get('source', 'Link')}]({item.get('url', '#')}) |"
            )
    elif content_type == "facts":
        item = selected_items[0]
        lines.extend([
            f"- **Category**: {item.get('category', '')}",
            f"- **Title**: {item.get('title', '')}",
            f"- **Fact**: {item.get('fact', '')}",
            f"- **Context**: {item.get('context', '')}",
            f"- **Source**: [{item.get('source', 'Source')}]({item.get('url', '#')})",
            f"- **Scores**: Relevance {item.get('relevance_score')}/10 | Popularity {item.get('popularity_score')}/10",
        ])
    else:
        item = selected_items[0]
        lines.extend([
            f"- **Word**: **{item.get('word', '')}** ({item.get('pronunciation', '')} - *{item.get('part_of_speech', '')}*)",
            f"- **Definition**: {item.get('definition', '')}",
            f"- **Example**: \"{item.get('example', '')}\"",
            f"- **Synonyms**: {', '.join(item.get('synonyms', []))}",
            f"- **Antonyms**: {', '.join(item.get('antonyms', []))}",
            f"- **Etymology**: {item.get('etymology', '')}",
        ])

    sender = contacts.get("sender", {})
    lines.extend([
        "",
        "## Instagram Caption (@sole_igit)",
        "",
        "```text",
        captions.get("instagram_caption", ""),
        "```",
        "",
        "## Email Signature",
        "",
        sender.get("name", "SOLE Bits & Bytes Maintainer"),
        sender.get("batch_branch", ""),
        sender.get("role", "Bits & Bytes SOLE"),
        sender.get("college", "IGIT Sarang"),
        f"Ph. No. {sender.get('phone', '')}",
        f"Instagram Handle : [{sender.get('instagram_handle', '@sole_igit')}]({sender.get('instagram_url', 'https://www.instagram.com/sole_igit/')})",
        f"LinkedIn Handle : [{sender.get('linkedin_handle', '')}]({sender.get('linkedin_url', 'https://www.linkedin.com/')})",
    ])
    return "\n".join(lines)


def run_package_pipeline(
    content_type: str,
    candidates_path: Path,
    date_code: Optional[str] = None,
    custom_caption: Optional[Dict[str, str]] = None,
    commit_ledger: bool = True,
) -> Dict[str, Any]:
    contacts = load_contacts()
    sched_info = contacts.get("schedule", {}).get(content_type, {})
    content_title = sched_info.get("content_type", content_type.upper())
    date_code = date_code or format_date_code()

    with open(candidates_path, "r", encoding="utf-8") as f:
        raw_payload = json.load(f)

    candidates = raw_payload if isinstance(raw_payload, list) else raw_payload.get("candidates", [])
    if not custom_caption and isinstance(raw_payload, dict):
        custom_caption = raw_payload.get("captions")

    limit = 10 if content_type == "news" else 1
    dedup_result = filter_and_rank_candidates(content_type, candidates, limit=limit)
    selected_items = dedup_result["selected"]
    if not selected_items:
        raise RuntimeError(f"No non-duplicate candidates remained for {content_type}!")

    slug = f"{date_code}_{content_type}".replace(" ", "_")
    pkg_dir = OUTPUT_ROOT / slug
    pkg_dir.mkdir(parents=True, exist_ok=True)

    # 1. Render Branded 1080x1350 JPGs, Dated Carousel PDF, and Canva CSV
    design_res = render_package_designs(content_type, selected_items, date_code, pkg_dir)

    # 2. Build /GHOST Instagram Caption & Hashtags
    captions = build_captions(content_type, selected_items, date_code, custom_caption=custom_caption)

    # 3. Resolve Recipients
    to_emails, cc_emails = resolve_recipients(contacts)
    subject = f"[{date_code}] : Bits & Bytes Social Media Post : {content_title}"

    # 4. Write HTML Email Body, Clean Plain-Text Body & Markdown Brief
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

    package_manifest = {
        "package_id": slug,
        "content_type": content_type,
        "content_title": content_title,
        "date_code": date_code,
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

    manifest_path = pkg_dir / "package_manifest.json"
    manifest_path.write_text(json.dumps(package_manifest, indent=2, ensure_ascii=False), encoding="utf-8")

    if commit_ledger:
        commit_selected(content_type, selected_items, package_meta={
            "package_id": slug,
            "content_type": content_type,
            "subject": subject,
            "manifest_path": str(manifest_path),
            "email_sent": False,
        })

    return package_manifest


def main() -> None:
    parser = argparse.ArgumentParser(description="Package & Deliver SOLE Bits & Bytes Automation Run")
    parser.add_argument("--type", choices=["news", "facts", "vocab"], required=True)
    parser.add_argument("--candidates", required=True, help="Path to JSON file with candidate items")
    parser.add_argument("--date-code", default=None, help="Optional override for [YYYY-MMM-WW-dddd]")
    parser.add_argument("--no-commit", action="store_true", help="Do not commit items to published_history.json")
    args = parser.parse_args()

    manifest = run_package_pipeline(
        content_type=args.type,
        candidates_path=Path(args.candidates),
        date_code=args.date_code,
        commit_ledger=not args.no_commit,
    )
    print(json.dumps({
        "status": "ok",
        "package_id": manifest["package_id"],
        "subject": manifest["subject"],
        "slide_count": manifest["design_assets"]["slide_count"],
        "first_slide": manifest["design_assets"]["slide_paths"][0],
        "carousel_pdf": manifest["design_assets"]["carousel_pdf_path"],
        "email_html_path": manifest["email_html_path"],
        "email_txt_path": manifest["email_txt_path"],
        "markdown_brief_path": manifest["markdown_brief_path"],
        "ghost_audit_ig": manifest["captions"]["ghost_audit_ig"],
    }, indent=2))


if __name__ == "__main__":
    main()
