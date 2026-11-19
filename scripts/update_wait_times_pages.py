#!/usr/bin/env python3
"""Regenerate the static, crawler-readable wait-times pages from the live API payload.

Why this exists: the LittleBuggy app is a Vue SPA — crawlers and AI assistants
that don't run JavaScript only see "Loading the latest wait times…". These
static pages carry a real data snapshot (with its timestamp) in plain HTML:

  - ``public/wait-times/index.html``          — full ER + UPCC snapshot table
  - ``public/wait-times/<slug>/index.html``   — per-facility snapshot pages
  - ``public/data/wait-times.json``           — the raw payload, same origin

The always-fresh source is the API text feed
(``https://littlebuggy-api.onrender.com/wait-times.txt``, rendered live per
request); these pages link to it prominently and label their snapshot time.
Facilities that are not publishing show "Not currently published" — never an
estimated or stale number presented as live.

Usage:  python3 scripts/update_wait_times_pages.py [--api-base URL]
Requires network. No third-party deps (stdlib only).
"""

from __future__ import annotations

import argparse
import html
import json
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_API_BASE = "https://littlebuggy-api.onrender.com"
TXT_FEED = "https://littlebuggy-api.onrender.com/wait-times.txt"

# Static page slug → API hospital key
FACILITY_PAGES = {
    "bc-childrens": "bc_children",
    "burnaby-hospital": "burnaby",
    "langley-memorial": "lmh",
    "lions-gate": "lgh",
    "richmond-hospital": "richmond",
    "royal-columbian": "royal_columbian",
    "surrey-memorial-pediatrics": "smh_p",
    "vancouver-general": "vgh",
}

STYLE = """
  body { font-family: system-ui, -apple-system, sans-serif; margin: 0; color: #1f2430; background: #faf9fc; }
  main { max-width: 760px; margin: 0 auto; padding: 24px 16px 48px; }
  h1 { font-size: 1.6rem; line-height: 1.25; }
  h2 { font-size: 1.15rem; margin-top: 2rem; }
  .updated { color: #555; font-size: 0.92rem; }
  .wait-now { font-size: 2rem; font-weight: 700; color: #7c3aed; margin: 0.5rem 0; }
  table { width: 100%; border-collapse: collapse; background: #fff; }
  th, td { text-align: left; padding: 8px 10px; border-bottom: 1px solid #e7e4ee; font-size: 0.95rem; }
  th { background: #f1edfa; }
  td.wait { font-weight: 600; white-space: nowrap; }
  .note { background: #fff7e6; border: 1px solid #f0dfae; border-radius: 8px; padding: 10px 14px; }
  a { color: #6d28d9; }
"""

FAQ_JSON_LD = """
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "How long is the ER wait at BC Children's Hospital right now?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Wait times change through the day. LittleBuggy shows the latest published estimate for BC Children's Hospital and every other Metro Vancouver emergency department on this page, drawn from the official provincial feed and refreshed throughout the day."
      }
    },
    {
      "@type": "Question",
      "name": "Should I take my child to an emergency department or an urgent care centre (UPCC)?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "For emergencies — trouble breathing, a seizure, a serious injury, or an infant under 3 months with a fever — go to an emergency department or call 911. For less urgent problems that still need same-day care, an urgent and primary care centre (UPCC) is usually the faster route. If you are not sure, call HealthLink BC at 8-1-1 any time."
      }
    },
    {
      "@type": "Question",
      "name": "Why do some hospitals show no wait time?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Hospitals only appear with a number when their health authority is publishing one. Fraser Health paused publishing ER wait times on August 17, 2026, so its hospitals (including Surrey Memorial, Burnaby and Royal Columbian) currently show as not published — we display that honestly rather than showing an old number, and their times will reappear here as soon as publishing resumes."
      }
    }
  ]
}
"""

ITEMLIST_JSON_LD = """
{
  "@context": "https://schema.org",
  "@type": "ItemList",
  "name": "Metro Vancouver ER wait times by hospital",
  "itemListElement": [
    { "@type": "ListItem", "position": 1, "name": "BC Children's Hospital ER wait time", "url": "https://littlebuggy.ca/wait-times/bc-childrens/" },
    { "@type": "ListItem", "position": 2, "name": "Surrey Memorial Hospital children's ER wait time", "url": "https://littlebuggy.ca/wait-times/surrey-memorial-pediatrics/" },
    { "@type": "ListItem", "position": 3, "name": "Vancouver General Hospital ER wait time", "url": "https://littlebuggy.ca/wait-times/vancouver-general/" },
    { "@type": "ListItem", "position": 4, "name": "Richmond Hospital ER wait time", "url": "https://littlebuggy.ca/wait-times/richmond-hospital/" },
    { "@type": "ListItem", "position": 5, "name": "Lions Gate Hospital ER wait time", "url": "https://littlebuggy.ca/wait-times/lions-gate/" },
    { "@type": "ListItem", "position": 6, "name": "Royal Columbian Hospital ER wait time", "url": "https://littlebuggy.ca/wait-times/royal-columbian/" },
    { "@type": "ListItem", "position": 7, "name": "Burnaby Hospital ER wait time", "url": "https://littlebuggy.ca/wait-times/burnaby-hospital/" },
    { "@type": "ListItem", "position": 8, "name": "Langley Memorial Hospital ER wait time", "url": "https://littlebuggy.ca/wait-times/langley-memorial/" }
  ]
}
"""

FRASER_NOTE = (
    "Some hospitals show \u201cNot currently published\u201d: Fraser Health paused publishing "
    "ER wait times on August 17, 2026. LittleBuggy shows that honestly rather than an old "
    "number, and their times will reappear as soon as publishing resumes."
)


def fmt_ts(raw: str | None) -> str:
    if not raw:
        return "not available"
    return str(raw).replace("T", " ")[:16]


def wait_display(row: dict) -> str:
    text = (row.get("wait_text") or "").strip()
    if row.get("wait_status") == "live" and text:
        return text
    if row.get("wait_status") == "not_published":
        return "Not currently published"
    return text or "Not currently published"


def esc(s) -> str:
    return html.escape(str(s or ""), quote=True)


def snapshot_line(payload: dict) -> str:
    return (
        f"Data snapshot: {esc(fmt_ts(payload.get('checked_at')))} Pacific Time · "
        f"source data updated {esc(fmt_ts(payload.get('source_updated_at')))} Pacific Time. "
        f"Wait times change through the day — for the newest numbers use the "
        f'<a href="{TXT_FEED}">live text feed</a> or '
        f'<a href="/?go=wait-times">open the live LittleBuggy app</a>.'
    )


def table_html(rows: list[dict], kind: str) -> str:
    out = ["<table>", f"<tr><th>{kind}</th><th>City</th><th>Wait</th></tr>"]
    for r in rows:
        out.append(
            f"<tr><td>{esc(r.get('name'))}</td><td>{esc(r.get('city'))}</td>"
            f'<td class="wait">{esc(wait_display(r))}</td></tr>'
        )
    out.append("</table>")
    return "\n".join(out)


def render_index(payload: dict) -> str:
    hospitals = payload.get("hospitals") or []
    upccs = payload.get("upcc_centres") or []
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>ER &amp; UPCC Wait Times in Metro Vancouver — LittleBuggy</title>
<meta name="description" content="Live emergency department and urgent care (UPCC) wait times for Metro Vancouver families: BC Children's, Vancouver General, Richmond, Surrey Memorial and more — plus which local viruses are going around this week.">
<link rel="alternate" type="text/plain" title="Live wait times (plain text, updated per request)" href="{TXT_FEED}">
<style>{STYLE}</style>
<script type="application/ld+json">{FAQ_JSON_LD}</script>
<script type="application/ld+json">{ITEMLIST_JSON_LD}</script>
</head>
<body>
<main>
<h1>ER &amp; UPCC wait times in Metro Vancouver</h1>
<p class="updated">{snapshot_line(payload)}</p>
<p>LittleBuggy tracks the published emergency department and urgent &amp; primary care centre (UPCC) wait times for Metro Vancouver families, drawn from the official provincial feed. Times are estimates and change through the day. In an emergency, call <strong>911</strong>. For health advice, call HealthLink BC at <strong>8-1-1</strong>.</p>
<h2>Emergency departments</h2>
{table_html(hospitals, "Hospital")}
<h2>Urgent &amp; primary care centres (UPCC)</h2>
{table_html(upccs, "Centre")}
<p class="note">{FRASER_NOTE}</p>
<p>See also: <a href="https://littlebuggy.ca/data/homepage-summary.json">which viruses are going around Metro Vancouver this week</a> · <a href="/llms.txt">About LittleBuggy's data (llms.txt)</a></p>
</main>
</body>
</html>
"""


def render_facility(payload: dict, row: dict) -> str:
    name = row.get("name", "")
    city = row.get("city", "")
    key = row.get("key", "")
    wait = wait_display(row)
    not_published = row.get("wait_status") == "not_published"
    address = row.get("address") or ""
    phone = row.get("phone") or ""
    website = row.get("website") or ""
    contact_bits = [esc(b) for b in (address, phone) if b]
    if website:
        contact_bits.append(f'<a href="{esc(website)}">{esc(website)}</a>')
    contact = " · ".join(contact_bits)
    fraser = f'<p class="note">{FRASER_NOTE}</p>' if not_published else ""
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(name)} ER Wait Time Today — LittleBuggy</title>
<meta name="description" content="Emergency wait time for {esc(name)} in {esc(city)}, plus the other Metro Vancouver ER and UPCC wait times parents check most — updated through the day on LittleBuggy.">
<link rel="alternate" type="text/plain" title="Live wait times (plain text, updated per request)" href="{TXT_FEED}">
<style>{STYLE}</style>
</head>
<body>
<main>
<h1>{esc(name)} ER wait time</h1>
<p class="wait-now">{esc(wait)}</p>
<p class="updated">{snapshot_line(payload)}</p>
<p>{contact}</p>
{fraser}
<p><a href="/?go=wait-times&amp;facility={esc(key)}">See this hospital live in the LittleBuggy app</a> · <a href="/wait-times/">All Metro Vancouver ER &amp; UPCC wait times</a></p>
<p>Wait times are estimates and change through the day. In an emergency, call <strong>911</strong>. For health advice, call HealthLink BC at <strong>8-1-1</strong>.</p>
</main>
</body>
</html>
"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--api-base", default=DEFAULT_API_BASE)
    args = ap.parse_args()

    url = args.api_base.rstrip("/") + "/wait-times"
    req = urllib.request.Request(url, headers={"User-Agent": "littlebuggy-static-generator"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        payload = json.loads(resp.read().decode("utf-8"))

    if not payload.get("hospitals"):
        print("ERROR: payload has no hospitals; refusing to write empty pages.", file=sys.stderr)
        return 1

    # Raw JSON snapshot, same origin
    out_json = ROOT / "public" / "data" / "wait-times.json"
    out_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {out_json.relative_to(ROOT)}")

    # Index page
    out_index = ROOT / "public" / "wait-times" / "index.html"
    out_index.write_text(render_index(payload), encoding="utf-8")
    print(f"wrote {out_index.relative_to(ROOT)}")

    # Facility pages
    by_key = {h.get("key"): h for h in payload.get("hospitals") or []}
    for slug, key in FACILITY_PAGES.items():
        row = by_key.get(key)
        if row is None:
            print(f"WARN: hospital key {key} not in payload; skipping {slug}", file=sys.stderr)
            continue
        out = ROOT / "public" / "wait-times" / slug / "index.html"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(render_facility(payload, row), encoding="utf-8")
        print(f"wrote {out.relative_to(ROOT)} ({row.get('name')}: {wait_display(row)})")

    print(f"snapshot checked_at={payload.get('checked_at')} source_updated_at={payload.get('source_updated_at')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
