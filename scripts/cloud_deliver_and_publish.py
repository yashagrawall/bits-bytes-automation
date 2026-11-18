#!/usr/bin/env python3
"""
Cloud Delivery (Google Drive, Google Docs, Gmail, Google Calendar) & Social Publishing Bridge
for SOLE Bits & Bytes Automation (IGIT Sarang).
"""

import argparse
import json
import os
import re
import shutil
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

from package_and_deliver import build_html_email, load_contacts

BASE_DIR = Path(__file__).resolve().parent.parent

GDRIVE_INIT = Path("/home/yashagrawall/.gemini/config/plugins/gdrive/skills/gdrive/scripts/gdrive")
GDOCS_INIT = Path("/home/yashagrawall/.gemini/config/plugins/gdocs/skills/gdocs/scripts/gdocs")
GMAIL_INIT = Path("/home/yashagrawall/.gemini/config/plugins/gmail/skills/gmail/scripts/gmail")
GCAL_INIT = Path("/home/yashagrawall/.gemini/config/plugins/gcalendar/skills/gcalendar/scripts/gcalendar")


def init_google_clis() -> Dict[str, bool]:
    status = {}
    for name, path in [
        ("gdrive", GDRIVE_INIT),
        ("gdocs", GDOCS_INIT),
        ("gmail", GMAIL_INIT),
        ("gcalendar", GCAL_INIT),
    ]:
        if path.exists():
            res = subprocess.run([str(path), "--version"], capture_output=True, text=True, check=False)
            status[name] = res.returncode == 0
        else:
            status[name] = False
    return status


def prepare_social_publishing_payloads(manifest: Dict[str, Any], artifact_dir: Optional[Path] = None) -> Dict[str, Any]:
    """
    Generates ready-to-execute payloads for:
    1. Zapier MCP (`InstagramBusinessCLIAPI`, `LinkedInCLIAPI`, `BufferCLIAPI`)
    2. Self-hosted n8n webhook (`http://localhost:5678/webhook/bits-bytes-publish`)
    3. Antigravity `browser` subagent (stages PNGs into browser_sandbox/uploads/)
    """
    png_paths: List[str] = manifest.get("design_assets", {}).get("png_paths", [])
    ig_caption: str = manifest.get("captions", {}).get("instagram_caption", "")
    li_caption: str = manifest.get("captions", {}).get("linkedin_caption", "")
    drive_url: Optional[str] = manifest.get("drive_folder_url")

    staged_uploads: List[str] = []
    if artifact_dir and artifact_dir.exists():
        uploads_dir = artifact_dir / "browser_sandbox" / "uploads"
        uploads_dir.mkdir(parents=True, exist_ok=True)
        for p in png_paths:
            src = Path(p)
            if src.exists():
                dst_name = f"{manifest['package_id']}_{src.name}"
                shutil.copy2(src, uploads_dir / dst_name)
                staged_uploads.append(dst_name)

    zapier_payloads = {
        "instagram_for_business": {
            "selected_api": "InstagramBusinessCLIAPI",
            "account_handle": "@sole_igit",
            "params": {
                "caption": ig_caption,
                "media_paths": png_paths,
                "drive_folder_url": drive_url,
            },
        },
        "linkedin": {
            "selected_api": "LinkedInCLIAPI",
            "params": {
                "comment": li_caption,
                "carousel_pdf_path": manifest.get("design_assets", {}).get("linkedin_pdf_path"),
                "drive_folder_url": drive_url,
            },
        },
        "buffer": {
            "selected_api": "BufferCLIAPI",
            "params": {
                "text": ig_caption,
                "media": png_paths,
                "scheduled_post_day": manifest.get("post_day", "Sunday"),
            },
        },
    }

    n8n_webhook_payload = {
        "webhook_url": "http://localhost:5678/webhook/bits-bytes-publish",
        "package_id": manifest["package_id"],
        "content_type": manifest["content_type"],
        "subject": manifest["subject"],
        "instagram_handle": "@sole_igit",
        "instagram_caption": ig_caption,
        "linkedin_caption": li_caption,
        "png_paths": png_paths,
        "linkedin_pdf_path": manifest.get("design_assets", {}).get("linkedin_pdf_path"),
        "drive_folder_url": drive_url,
        "gdoc_url": manifest.get("gdoc_url"),
    }

    browser_subagent_brief = {
        "staged_filenames_in_uploads": staged_uploads,
        "instagram_target_url": "https://www.instagram.com/sole_igit/",
        "instagram_caption": ig_caption,
        "linkedin_caption": li_caption,
    }

    return {
        "zapier_mcp": zapier_payloads,
        "n8n_webhook": n8n_webhook_payload,
        "browser_subagent": browser_subagent_brief,
    }


def update_manifest_with_cloud_links(
    manifest_path: Path,
    drive_folder_url: Optional[str] = None,
    gdoc_url: Optional[str] = None,
    canva_edit_url: Optional[str] = None,
    gmail_draft_id: Optional[str] = None,
    calendar_event_url: Optional[str] = None,
    artifact_dir: Optional[Path] = None,
) -> Dict[str, Any]:
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    if drive_folder_url:
        manifest["drive_folder_url"] = drive_folder_url
    if gdoc_url:
        manifest["gdoc_url"] = gdoc_url
    if canva_edit_url:
        manifest["canva_edit_url"] = canva_edit_url
    if gmail_draft_id:
        manifest["gmail_draft_id"] = gmail_draft_id
    if calendar_event_url:
        manifest["calendar_event_url"] = calendar_event_url

    # Regenerate HTML email so it includes live clickable Drive, Docs, and Canva links
    contacts = load_contacts()
    email_html = build_html_email(
        content_type=manifest["content_type"],
        content_title=manifest["content_title"],
        date_code=manifest["date_code"],
        selected_items=manifest["selected_items"],
        captions=manifest["captions"],
        contacts=contacts,
        drive_folder_url=manifest.get("drive_folder_url"),
        gdoc_url=manifest.get("gdoc_url"),
        canva_edit_url=manifest.get("canva_edit_url"),
        slide_count=manifest["design_assets"]["slide_count"],
    )
    with open(manifest["email_html_path"], "w", encoding="utf-8") as f:
        f.write(email_html)

    manifest["social_publishing"] = prepare_social_publishing_payloads(manifest, artifact_dir=artifact_dir)

    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)

    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description="Update manifest with cloud URLs and stage social publishing payloads")
    parser.add_argument("--manifest", required=True, help="Path to package_manifest.json")
    parser.add_argument("--drive-url", default=None)
    parser.add_argument("--gdoc-url", default=None)
    parser.add_argument("--canva-url", default=None)
    parser.add_argument("--gmail-draft-id", default=None)
    parser.add_argument("--calendar-url", default=None)
    parser.add_argument("--artifact-dir", default=None, help="Optional Antigravity artifact dir for staging browser uploads")
    args = parser.parse_args()

    manifest = update_manifest_with_cloud_links(
        manifest_path=Path(args.manifest),
        drive_folder_url=args.drive_url,
        gdoc_url=args.gdoc_url,
        canva_edit_url=args.canva_url,
        gmail_draft_id=args.gmail_draft_id,
        calendar_event_url=args.calendar_url,
        artifact_dir=Path(args.artifact_dir) if args.artifact_dir else None,
    )
    print(json.dumps({
        "status": "ok",
        "package_id": manifest["package_id"],
        "drive_folder_url": manifest.get("drive_folder_url"),
        "gdoc_url": manifest.get("gdoc_url"),
        "gmail_draft_id": manifest.get("gmail_draft_id"),
        "staged_browser_uploads": manifest["social_publishing"]["browser_subagent"]["staged_filenames_in_uploads"],
    }, indent=2))


if __name__ == "__main__":
    main()
