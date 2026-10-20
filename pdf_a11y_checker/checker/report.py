"""
Builds a single unified report structure for one PDF, combining registry
metadata with the live check results. This is the object every exporter
(HTML / Markdown / XLSX) and the web UI consume.
"""
import datetime
import os

from .registry import get_test_case, all_ids_in_order
from .checks import run_all_checks
from .structure import load_context

STATUS_LABELS = {
    "pass": "Pass",
    "fail": "Fail",
    "na": "N/A",
    "manual": "Manual check needed",
    "review": "Needs review",
}


def build_report_for_pdf(path, display_name=None, source_url=None, source_page=None):
    display_name = display_name or os.path.basename(path)
    ctx = load_context(path)

    row_errors = list(ctx.errors)

    if ctx.pdf is None:
        rows = []
        for tc_id in all_ids_in_order():
            tc = get_test_case(tc_id)
            rows.append({
                "id": tc_id, "title": tc["title"], "category": tc["category"],
                "status": "manual", "status_label": STATUS_LABELS["manual"],
                "summary": "Could not analyze this PDF automatically.",
                "evidence": row_errors, "pages": [],
                "wcag": tc["wcag"], "pdfua": tc["pdfua"],
                "automation": tc["automation"],
                "remediation": tc.get("remediation") or tc.get("manual_steps") or [],
            })
        summary = _summarize(rows)
        ctx.close()
        return {
            "filename": display_name, "source_url": source_url,
            "source_page": source_page, "page_count": None,
            "generated_at": datetime.datetime.now().isoformat(timespec="seconds"),
            "errors": row_errors, "rows": rows, "summary": summary,
        }

    results = run_all_checks(ctx)
    rows = []
    for tc_id in all_ids_in_order():
        tc = get_test_case(tc_id)
        res = results.get(tc_id, {"status": "manual", "summary": "Not run.",
                                    "evidence": []})
        rows.append({
            "id": tc_id,
            "title": tc["title"],
            "category": tc["category"],
            "status": res["status"],
            "status_label": STATUS_LABELS.get(res["status"], res["status"]),
            "summary": res["summary"],
            "evidence": res.get("evidence", []),
            "pages": res.get("pages", []),
            "wcag": tc["wcag"],
            "pdfua": tc["pdfua"],
            "automation": tc["automation"],
            "remediation": tc.get("remediation") or tc.get("manual_steps") or [],
        })

    summary = _summarize(rows)
    report = {
        "filename": display_name,
        "source_url": source_url,
        "source_page": source_page,
        "page_count": ctx.page_count,
        "title": ctx.title,
        "language": ctx.lang,
        "tagged": ctx.tagged_pdf,
        "generated_at": datetime.datetime.now().isoformat(timespec="seconds"),
        "errors": row_errors,
        "rows": rows,
        "summary": summary,
    }
    ctx.close()
    return report


def _summarize(rows):
    counts = {"pass": 0, "fail": 0, "na": 0, "manual": 0, "review": 0}
    for r in rows:
        counts[r["status"]] = counts.get(r["status"], 0) + 1
    total = len(rows)
    scored = counts["pass"] + counts["fail"]
    score_pct = round(100 * counts["pass"] / scored) if scored else None
    return {
        "total": total,
        "pass": counts["pass"],
        "fail": counts["fail"],
        "na": counts["na"],
        "manual": counts["manual"],
        "review": counts["review"],
        "score_pct": score_pct,
    }
