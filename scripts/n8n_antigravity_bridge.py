#!/usr/bin/env python3
"""
HTTP Bridge & CLI Connector between `bits-bytes-n8n` (Docker) and Antigravity's
Design, /GHOST Caption, Google Drive (`1l5PmICOOz5qM61L-6cKgEz-7nQlh5CaS`), and Social Publishing Pipeline.

From inside the `bits-bytes-n8n` Docker container (which has `host.docker.internal:host-gateway`
in docker-compose.yml), an n8n HTTP Request node can POST curated items to:
    POST http://host.docker.internal:8765/api/v1/package
with JSON body:
    {
      "content_type": "news" | "facts" | "vocab",
      "date_code": "2026-Nov-W3-Saturday",
      "candidates": [...],
      "captions": {"instagram": "...", "linkedin": "...", "hashtags": [...]}
    }
and receive back the rendered 1080x1350 PNG paths, LinkedIn Carousel PDF, Canva CSV,
Google Slides batch JSON, /GHOST-sanitized captions, and styled HTML email body.
"""

import argparse
import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any, Dict

from cloud_deliver_and_publish import prepare_social_publishing_payloads
from dedup_ledger import commit_selected, filter_and_rank_candidates
from ghost_caption import build_captions
from package_and_deliver import (
    BASE_DIR,
    OUTPUT_ROOT,
    build_html_email,
    build_markdown_brief,
    format_date_code,
    load_contacts,
    resolve_recipients,
)
from render_designs import render_package_designs

EXISTING_DRIVE_FOLDER_ID = "1l5PmICOOz5qM61L-6cKgEz-7nQlh5CaS"


def process_payload(payload: Dict[str, Any], commit_ledger: bool = True) -> Dict[str, Any]:
    content_type = payload.get("content_type", "news").lower()
    if content_type not in ("news", "facts", "vocab"):
        raise ValueError(f"Invalid content_type '{content_type}'. Must be 'news', 'facts', or 'vocab'.")

    date_code = payload.get("date_code") or format_date_code()
    candidates = payload.get("candidates") or payload.get("items") or []
    if not candidates:
        raise ValueError("Payload must include non-empty 'candidates' or 'items' array.")

    contacts = load_contacts()
    sched_info = contacts.get("schedule", {}).get(content_type, {})
    content_title = sched_info.get("content_type", content_type.upper())

    limit = 10 if content_type == "news" else 1
    dedup_result = filter_and_rank_candidates(content_type, candidates, limit=limit)
    selected_items = dedup_result["selected"]
    if not selected_items:
        raise RuntimeError(f"All candidates for {content_type} were filtered out as duplicates!")

    slug = f"{date_code}_{content_type}".replace(" ", "_")
    pkg_dir = OUTPUT_ROOT / slug
    pkg_dir.mkdir(parents=True, exist_ok=True)

    design_res = render_package_designs(content_type, selected_items, date_code, pkg_dir)
    captions = build_captions(content_type, selected_items, date_code, custom_caption=payload.get("captions"))
    to_emails, cc_emails = resolve_recipients(contacts)
    subject = f"[{date_code}] : Bits & Bytes Social Media Post : {content_title}"

    drive_folder_url = payload.get(
        "drive_folder_url",
        f"https://drive.google.com/drive/folders/{EXISTING_DRIVE_FOLDER_ID}",
    )

    email_html = build_html_email(
        content_type=content_type,
        content_title=content_title,
        date_code=date_code,
        selected_items=selected_items,
        captions=captions,
        contacts=contacts,
        drive_folder_url=drive_folder_url,
        gdoc_url=payload.get("gdoc_url"),
        canva_edit_url=payload.get("canva_edit_url"),
        slide_count=design_res["slide_count"],
    )
    email_html_path = pkg_dir / "email_body.html"
    email_html_path.write_text(email_html, encoding="utf-8")

    md_brief = build_markdown_brief(
        content_type=content_type,
        content_title=content_title,
        date_code=date_code,
        selected_items=selected_items,
        captions=captions,
        contacts=contacts,
        to_emails=to_emails,
        cc_emails=cc_emails,
        drive_folder_url=drive_folder_url,
    )
    md_brief_path = pkg_dir / "post_brief.md"
    md_brief_path.write_text(md_brief, encoding="utf-8")

    manifest = {
        "package_id": slug,
        "content_type": content_type,
        "content_title": content_title,
        "date_code": date_code,
        "subject": subject,
        "to_emails": to_emails,
        "cc_emails": cc_emails,
        "drive_root_folder_id": EXISTING_DRIVE_FOLDER_ID,
        "drive_folder_url": drive_folder_url,
        "selected_items": selected_items,
        "deduplication_stats": {
            "total_candidates": dedup_result["total_candidates"],
            "rejected_duplicates_count": dedup_result["rejected_duplicates_count"],
            "selected_count": len(selected_items),
        },
        "design_assets": design_res,
        "captions": captions,
        "email_html_path": str(email_html_path),
        "email_html": email_html,
        "markdown_brief_path": str(md_brief_path),
    }
    manifest["social_publishing"] = prepare_social_publishing_payloads(manifest)

    manifest_path = pkg_dir / "package_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")

    if commit_ledger:
        commit_selected(content_type, selected_items, package_meta={
            "package_id": slug,
            "content_type": content_type,
            "subject": subject,
            "manifest_path": str(manifest_path),
        })

    return manifest


class BridgeHandler(BaseHTTPRequestHandler):
    def _send_json(self, status_code: int, data: Dict[str, Any]) -> None:
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        if self.path in ("/health", "/api/v1/health"):
            self._send_json(200, {
                "status": "healthy",
                "service": "SOLE Bits & Bytes Antigravity Bridge",
                "drive_folder_id": EXISTING_DRIVE_FOLDER_ID,
            })
        else:
            self._send_json(404, {"error": "Not found"})

    def do_POST(self) -> None:
        if self.path not in ("/api/v1/package", "/render-and-package"):
            self._send_json(404, {"error": f"Unknown endpoint {self.path}"})
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            raw = self.rfile.read(length).decode("utf-8")
            payload = json.loads(raw)
            commit = bool(payload.get("commit", True))
            manifest = process_payload(payload, commit_ledger=commit)
            self._send_json(200, {"ok": True, "manifest": manifest})
        except Exception as exc:
            self._send_json(400, {"ok": False, "error": str(exc)})


def main() -> None:
    parser = argparse.ArgumentParser(description="SOLE Bits & Bytes n8n <-> Antigravity Bridge")
    parser.add_argument("--serve", action="store_true", help="Run HTTP bridge server on 0.0.0.0:8765 for n8n")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()

    if args.serve:
        server = HTTPServer(("0.0.0.0", args.port), BridgeHandler)
        print(f"SOLE Bits & Bytes Antigravity Bridge listening on http://0.0.0.0:{args.port}")
        server.serve_forever()


if __name__ == "__main__":
    main()
