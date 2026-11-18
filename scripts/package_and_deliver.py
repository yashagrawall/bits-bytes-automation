#!/usr/bin/env python3
"""
End-to-End Packaging, Google Drive / Docs Sync, HTML Email Builder & Gmail Dispatcher
for SOLE Bits & Bytes (IGIT Sarang).
"""

import argparse
import html
import json
import os
import re
import shutil
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from dedup_ledger import commit_selected, filter_and_rank_candidates
from ghost_caption import build_captions
from render_designs import render_package_designs

BASE_DIR = Path(__file__).resolve().parent.parent
CONTACTS_PATH = BASE_DIR / "config" / "contacts.json"
OUTPUT_ROOT = BASE_DIR / "output"

GDRIVE_SCRIPT = Path("/home/yashagrawall/.gemini/config/plugins/gdrive/skills/gdrive/scripts/gdrive")
GDOCS_SCRIPT = Path("/home/yashagrawall/.gemini/config/plugins/gdocs/skills/gdocs/scripts/gdocs")
GMAIL_SCRIPT = Path("/home/yashagrawall/.gemini/config/plugins/gmail/skills/gmail/scripts/gmail")
GCAL_SCRIPT = Path("/home/yashagrawall/.gemini/config/plugins/gcalendar/skills/gcalendar/scripts/gcalendar")


def format_date_code(dt: Optional[datetime] = None) -> str:
    """Formats [YYYY-MMM-WW-dddd] e.g. 2026-Nov-W3-Saturday."""
    dt = dt or datetime.now().astimezone()
    week_of_month = (dt.day - 1) // 7 + 1
    return f"{dt.strftime('%Y-%b')}-W{week_of_month}-{dt.strftime('%A')}"


def load_contacts() -> Dict[str, Any]:
    with open(CONTACTS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def resolve_recipients(contacts: Dict[str, Any]) -> Tuple[List[str], List[str]]:
    to_emails: List[str] = []
    for group in contacts.get("recipients", {}).get("to", {}).values():
        for person in group:
            email = person.get("email", "").strip()
            if email and email not in to_emails:
                to_emails.append(email)

    cc_emails: List[str] = []
    for group in contacts.get("recipients", {}).get("cc", {}).values():
        for person in group:
            email = person.get("email", "").strip()
            if email and email not in cc_emails and email not in to_emails:
                cc_emails.append(email)

    return to_emails, cc_emails


def ensure_cli_registered(script_path: Path) -> bool:
    if not script_path.exists():
        return False
    try:
        subprocess.run([str(script_path), "--version"], check=False, capture_output=True, text=True, timeout=15)
        return True
    except Exception:
        return False


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
) -> str:
    sender = contacts.get("sender", {})

    # Build content block (HTML Table for News, Card for Facts / Vocab)
    if content_type == "news":
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
        content_block = (
            '<h3 style="color:#0f172a;margin:20px 0 10px 0;font-size:17px;">1. Curated Weekly Top 10 News Highlights (with Sources)</h3>'
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
    elif content_type == "facts":
        item = selected_items[0]
        content_block = (
            '<h3 style="color:#0f172a;margin:20px 0 10px 0;font-size:17px;">1. Curated Random Fact of the Week</h3>'
            '<div style="background:#f8fafc;border-left:5px solid #0887A8;padding:18px 20px;border-radius:8px;margin-bottom:24px;">'
            f'<div style="font-size:12px;font-weight:700;color:#0887A8;text-transform:uppercase;letter-spacing:0.5px;">Category: {html.escape(item.get("category", "General"))}</div>'
            f'<h4 style="margin:6px 0 10px 0;font-size:19px;color:#0f172a;">{html.escape(item.get("title", ""))}</h4>'
            f'<p style="margin:0 0 12px 0;font-size:15px;color:#1e293b;line-height:1.6;"><b>Fact:</b> {html.escape(item.get("fact", ""))}</p>'
            f'<p style="margin:0 0 12px 0;font-size:14px;color:#475569;line-height:1.55;"><b>Context:</b> {html.escape(item.get("context", ""))}</p>'
            f'<div style="font-size:13px;color:#64748b;"><b>Primary Source:</b> <a href="{html.escape(item.get("url", "#"))}" style="color:#0887A8;">{html.escape(item.get("source", "Verified"))}</a> '
            f'&nbsp;|&nbsp; <b>Relevance:</b> {item.get("relevance_score", 9.0)}/10 &nbsp;|&nbsp; <b>Popularity:</b> {item.get("popularity_score", 9.0)}/10</div>'
            '</div>'
        )
    else:  # vocab
        item = selected_items[0]
        syns = ", ".join(item.get("synonyms", []))
        ants = ", ".join(item.get("antonyms", []))
        content_block = (
            '<h3 style="color:#0f172a;margin:20px 0 10px 0;font-size:17px;">1. Curated Random Vocabulary / Thesaurus of the Week</h3>'
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

    # Asset links block
    links_items = []
    if drive_folder_url:
        links_items.append(f'<li><b>Google Drive Asset Folder ({slide_count} PNG Slides + LinkedIn PDF + Canva CSV):</b> <a href="{html.escape(drive_folder_url)}" style="color:#0887A8;font-weight:600;">Open Drive Folder &#8599;</a></li>')
    if gdoc_url:
        links_items.append(f'<li><b>Google Docs Content &amp; Caption Sheet:</b> <a href="{html.escape(gdoc_url)}" style="color:#0887A8;font-weight:600;">Open Google Doc &#8599;</a></li>')
    if canva_edit_url:
        links_items.append(f'<li><b>Canva Editable Design Template:</b> <a href="{html.escape(canva_edit_url)}" style="color:#0887A8;font-weight:600;">Edit in Canva &#8599;</a></li>')
    if not links_items:
        links_items.append(
            f'<li><b>Attached Design Package ({slide_count} Ready-to-Post 1080&times;1350 PNG Slides + Carousel PDF):</b> '
            f'All {slide_count} rendered PNG slides (<code>slide_01.png</code> &ndash; <code>slide_{slide_count:02d}.png</code>) and '
            f'<code>linkedin_carousel.pdf</code> are attached directly to this email.</li>'
            f'<li><b>Design &amp; Posting Flexibility:</b> The Design and Social Media teams may <b>accept and post these attached designs directly</b>, '
            f'or use the curated content below to <b>create a custom design</b> before posting on <code>@sole_igit</code>.</li>'
        )

    ig_caption_html = html.escape(captions.get("instagram_caption", "")).replace("\n", "<br>")
    li_caption_html = html.escape(captions.get("linkedin_caption", "")).replace("\n", "<br>")

    email_html = f"""<!DOCTYPE html>
<html>
<body style="font-family:Arial,Helvetica,sans-serif;color:#1e293b;line-height:1.6;max-width:840px;margin:0 auto;padding:16px;">
  <div style="background:#070c14;color:#ffffff;padding:20px 24px;border-radius:12px 12px 0 0;border-bottom:4px solid #22d3ee;">
    <div style="font-size:12px;color:#22d3ee;font-weight:700;letter-spacing:1px;text-transform:uppercase;">SOLE (Society Of Literary Enthusiasts) &bull; IGIT Sarang</div>
    <h2 style="margin:6px 0 0 0;font-size:22px;color:#ffffff;">[{html.escape(date_code)}] : Bits &amp; Bytes Social Media Post : {html.escape(content_title)}</h2>
  </div>

  <div style="border:1px solid #e2e8f0;border-top:none;padding:24px;border-radius:0 0 12px 12px;background:#ffffff;">
    <p style="margin-top:0;">Hi Social Media &amp; Design Team Leads,</p>
    <p>Please find below the curated, deduplicated <b>Bits &amp; Bytes</b> content, ready-to-copy <code>/GHOST</code> caption, and <b>attached 1080&times;1350 design slides</b> for <b>{html.escape(content_title)}</b>. Feel free to post the attached design directly or use the content to create a new design if preferred.</p>

    {content_block}

    <h3 style="color:#0f172a;margin:24px 0 10px 0;font-size:17px;">2. Attached Design &amp; Carousel Files</h3>
    <ul style="background:#f0f9ff;border:1px solid #bae6fd;padding:14px 20px 14px 36px;border-radius:8px;margin-bottom:24px;">
      {"".join(links_items)}
    </ul>

    <h3 style="color:#0f172a;margin:24px 0 10px 0;font-size:17px;">3. Ready-to-Post Caption &amp; Hashtags (@sole_igit) &mdash; /GHOST Verified</h3>
    <div style="background:#f8fafc;border:1px solid #cbd5e1;padding:16px;border-radius:8px;font-family:monospace;font-size:13.5px;line-height:1.55;margin-bottom:24px;">
      {ig_caption_html}
    </div>

    <h3 style="color:#0f172a;margin:24px 0 10px 0;font-size:17px;">4. LinkedIn Post Copy &mdash; /GHOST Verified</h3>
    <div style="background:#f8fafc;border:1px solid #cbd5e1;padding:16px;border-radius:8px;font-family:monospace;font-size:13.5px;line-height:1.55;margin-bottom:28px;">
      {li_caption_html}
    </div>

    <hr style="border:none;border-top:1px solid #cbd5e1;margin:28px 0 18px 0;">
    <div style="font-size:13.5px;color:#334155;line-height:1.55;">
      <b>{html.escape(sender.get("name", "Yash Agrawall"))}</b><br>
      {html.escape(sender.get("batch_branch", "43rd CSE"))}<br>
      {html.escape(sender.get("role", "Bits & Bytes SOLE"))}<br>
      {html.escape(sender.get("college", "IGIT Sarang"))}<br>
      Ph. No. {html.escape(sender.get("phone", "+91 72051 17574"))}<br>
      Instagram Handle : <a href="{html.escape(sender.get("instagram_url", "https://www.instagram.com/yashagrawall/"))}" style="color:#0887A8;">{html.escape(sender.get("instagram_handle", "@yashagrawall"))}</a><br>
      LinkedIn Handle : <a href="{html.escape(sender.get("linkedin_url", "https://www.linkedin.com/in/yash-agrawall"))}" style="color:#0887A8;">{html.escape(sender.get("linkedin_handle", "yash-agrawall"))}</a><br>
      <img src="cid:igit_logo" alt="IGIT Sarang Logo" style="width:72px;height:auto;margin-top:10px;display:block;">
    </div>
  </div>
</body>
</html>"""
    return email_html


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

    lines.extend([
        "",
        "## Instagram Caption (@sole_igit)",
        "",
        "```text",
        captions.get("instagram_caption", ""),
        "```",
        "",
        "## LinkedIn Caption",
        "",
        "```text",
        captions.get("linkedin_caption", ""),
        "```",
        "",
        "## Email Signature",
        "",
        "Yash Agrawall",
        "43rd CSE",
        "Bits & Bytes SOLE",
        "IGIT Sarang",
        "Ph. No. +91 72051 17574",
        "Instagram Handle : [@yashagrawall](https://www.instagram.com/yashagrawall/)",
        "LinkedIn Handle : [yash-agrawall](https://www.linkedin.com/in/yash-agrawall)",
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

    # 1. Render Branded PNGs, LinkedIn PDF, Canva CSV, and Google Slides Batch JSON
    design_res = render_package_designs(content_type, selected_items, date_code, pkg_dir)

    # 2. Build /GHOST Captions & Hashtags
    captions = build_captions(content_type, selected_items, date_code, custom_caption=custom_caption)

    # 3. Resolve Recipients
    to_emails, cc_emails = resolve_recipients(contacts)
    subject = f"[{date_code}] : Bits & Bytes Social Media Post : {content_title}"

    # 4. Write HTML Email Body & Markdown Brief
    email_html = build_html_email(
        content_type=content_type,
        content_title=content_title,
        date_code=date_code,
        selected_items=selected_items,
        captions=captions,
        contacts=contacts,
        slide_count=design_res["slide_count"],
    )
    email_html_path = pkg_dir / "email_body.html"
    with open(email_html_path, "w", encoding="utf-8") as f:
        f.write(email_html)

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
    with open(md_brief_path, "w", encoding="utf-8") as f:
        f.write(md_brief)

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
        "markdown_brief_path": str(md_brief_path),
    }

    manifest_path = pkg_dir / "package_manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(package_manifest, f, indent=2, ensure_ascii=False)

    if commit_ledger:
        commit_selected(content_type, selected_items, package_meta={
            "package_id": slug,
            "content_type": content_type,
            "subject": subject,
            "manifest_path": str(manifest_path),
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
        "first_slide": manifest["design_assets"]["png_paths"][0],
        "linkedin_pdf": manifest["design_assets"]["linkedin_pdf_path"],
        "email_html_path": manifest["email_html_path"],
        "markdown_brief_path": manifest["markdown_brief_path"],
        "ghost_audit_ig": manifest["captions"]["ghost_audit_ig"],
    }, indent=2))


if __name__ == "__main__":
    main()
