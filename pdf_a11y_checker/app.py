import os
import uuid
import shutil
import traceback

from flask import Flask, request, jsonify, render_template, send_file, abort

from checker.report import build_report_for_pdf
from checker.crawler import discover_pdf_links, download_selected
from checker.exporters import to_markdown, to_html, to_xlsx
from checker.registry import TEST_CASES, all_ids_in_order

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
RESULTS_DIR = os.path.join(BASE_DIR, "results")
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(RESULTS_DIR, exist_ok=True)

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 300 * 1024 * 1024  # 300MB total upload cap

# In-memory batch store: {batch_id: {"reports": [...], "title": str}}
BATCHES = {}


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/test-cases")
def api_test_cases():
    return jsonify({tid: TEST_CASES[tid] for tid in all_ids_in_order()})


@app.route("/api/check-upload", methods=["POST"])
def api_check_upload():
    files = request.files.getlist("pdfs")
    if not files:
        return jsonify({"error": "No files uploaded."}), 400

    batch_id = uuid.uuid4().hex[:12]
    batch_dir = os.path.join(UPLOAD_DIR, batch_id)
    os.makedirs(batch_dir, exist_ok=True)

    reports = []
    for f in files:
        if not f.filename.lower().endswith(".pdf"):
            continue
        safe_name = os.path.basename(f.filename)
        dest = os.path.join(batch_dir, safe_name)
        f.save(dest)
        try:
            report = build_report_for_pdf(dest, display_name=safe_name)
        except Exception as e:
            report = _error_report(safe_name, e)
        reports.append(report)

    if not reports:
        return jsonify({"error": "No valid PDF files were uploaded."}), 400

    BATCHES[batch_id] = {"reports": reports, "title": "PDF Accessibility Report"}
    return jsonify({"batch_id": batch_id, "reports": reports})


@app.route("/api/crawl-discover", methods=["POST"])
def api_crawl_discover():
    """Step 1 of the crawl flow: find linked PDFs on the given pages, but
    don't download or test anything yet - the user picks which to run."""
    data = request.get_json(force=True, silent=True) or {}
    urls = data.get("urls", [])
    urls = [u.strip() for u in urls if u and u.strip()]
    if not urls:
        return jsonify({"error": "No URLs provided."}), 400

    try:
        result = discover_pdf_links(urls)
    except Exception as e:
        return jsonify({"error": f"Crawl failed: {e}"}), 500

    return jsonify({"pdfs": result["pdfs"], "errors": result["errors"]})


@app.route("/api/crawl-check", methods=["POST"])
def api_crawl_check():
    """Step 2 of the crawl flow: download and run checks on just the PDFs
    the user selected from the discovery list."""
    data = request.get_json(force=True, silent=True) or {}
    pdfs = data.get("pdfs", [])
    pdfs = [p for p in pdfs if isinstance(p, dict) and p.get("pdf_url")]
    if not pdfs:
        return jsonify({"error": "No PDFs were selected."}), 400

    batch_id = uuid.uuid4().hex[:12]
    batch_dir = os.path.join(UPLOAD_DIR, batch_id)
    os.makedirs(batch_dir, exist_ok=True)

    try:
        dl_result = download_selected(pdfs, batch_dir)
    except Exception as e:
        return jsonify({"error": f"Download failed: {e}"}), 500

    reports = []
    for item in dl_result["downloaded"]:
        try:
            report = build_report_for_pdf(
                item["path"],
                display_name=os.path.basename(item["path"]),
                source_url=item["pdf_url"],
                source_page=item["source_page"],
            )
        except Exception as e:
            report = _error_report(os.path.basename(item["path"]), e)
        reports.append(report)

    if reports:
        BATCHES[batch_id] = {"reports": reports, "title": "PDF Accessibility Report"}

    return jsonify({
        "batch_id": batch_id if reports else None,
        "reports": reports,
        "download_errors": dl_result["errors"],
    })


@app.route("/api/download/<batch_id>/<fmt>")
def api_download(batch_id, fmt):
    batch = BATCHES.get(batch_id)
    if not batch:
        abort(404)
    reports = batch["reports"]
    title = batch["title"]
    out_dir = os.path.join(RESULTS_DIR, batch_id)
    os.makedirs(out_dir, exist_ok=True)

    if fmt == "html":
        path = os.path.join(out_dir, "accessibility-report.html")
        with open(path, "w", encoding="utf-8") as f:
            f.write(to_html(reports, title=title))
        return send_file(path, as_attachment=True, download_name="accessibility-report.html")
    elif fmt == "md":
        path = os.path.join(out_dir, "accessibility-report.md")
        with open(path, "w", encoding="utf-8") as f:
            f.write(to_markdown(reports, title=title))
        return send_file(path, as_attachment=True, download_name="accessibility-report.md")
    elif fmt == "xlsx":
        path = os.path.join(out_dir, "accessibility-report.xlsx")
        to_xlsx(reports, path, title=title)
        return send_file(path, as_attachment=True, download_name="accessibility-report.xlsx")
    else:
        abort(404)


def _error_report(name, exc):
    return {
        "filename": name, "source_url": None, "source_page": None,
        "page_count": None, "title": None, "language": None, "tagged": False,
        "generated_at": None,
        "errors": [f"Failed to process this file: {exc}"],
        "rows": [],
        "summary": {"total": 0, "pass": 0, "fail": 0, "na": 0, "manual": 0,
                    "review": 0, "score_pct": None},
    }


if __name__ == "__main__":
    app.run(debug=True, port=5050)
