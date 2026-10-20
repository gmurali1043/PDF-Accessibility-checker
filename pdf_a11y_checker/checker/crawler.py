"""
Given one or more webpage URLs, find every linked PDF and download it to a
local folder so it can be run through the same checks.py pipeline used for
directly-uploaded files.
"""
import os
import re
import hashlib
import requests
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; PDFAccessibilityChecker/1.0; "
                  "+local-tool)"
}
TIMEOUT = 20


def _safe_filename(url):
    parsed = urlparse(url)
    base = os.path.basename(parsed.path) or "document.pdf"
    base = re.sub(r"[^A-Za-z0-9._-]", "_", base)
    if not base.lower().endswith(".pdf"):
        base += ".pdf"
    h = hashlib.md5(url.encode("utf-8")).hexdigest()[:8]
    name, ext = os.path.splitext(base)
    return f"{name}_{h}{ext}"


def find_pdf_links(page_url):
    """Returns a sorted list of absolute PDF URLs found on page_url."""
    resp = requests.get(page_url, headers=HEADERS, timeout=TIMEOUT)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    links = set()
    for a in soup.find_all("a", href=True):
        href = a["href"]
        abs_url = urljoin(page_url, href)
        if abs_url.lower().split("?")[0].split("#")[0].endswith(".pdf"):
            links.add(abs_url)
    # also catch embedded <iframe>/<embed>/<object> pointing at PDFs
    for tag, attr in (("iframe", "src"), ("embed", "src"), ("object", "data")):
        for el in soup.find_all(tag):
            src = el.get(attr)
            if not src:
                continue
            abs_url = urljoin(page_url, src)
            if abs_url.lower().split("?")[0].split("#")[0].endswith(".pdf"):
                links.add(abs_url)
    return sorted(links)


def download_pdf(pdf_url, dest_dir):
    os.makedirs(dest_dir, exist_ok=True)
    filename = _safe_filename(pdf_url)
    dest_path = os.path.join(dest_dir, filename)
    resp = requests.get(pdf_url, headers=HEADERS, timeout=TIMEOUT, stream=True)
    resp.raise_for_status()
    ctype = resp.headers.get("Content-Type", "")
    with open(dest_path, "wb") as f:
        for chunk in resp.iter_content(chunk_size=65536):
            if chunk:
                f.write(chunk)
    return dest_path


def discover_pdf_links(page_urls):
    """
    Crawls each page URL and finds linked PDFs WITHOUT downloading them, so
    the user can pick which ones to actually test.
    Returns: {
      "pdfs": [{"pdf_url":..., "source_page":...}, ...] (deduplicated by URL),
      "errors": [{"url":..., "error":...}, ...]
    }
    """
    pdfs = []
    seen = set()
    errors = []
    for page_url in page_urls:
        page_url = page_url.strip()
        if not page_url:
            continue
        try:
            pdf_urls = find_pdf_links(page_url)
        except Exception as e:
            errors.append({"url": page_url, "error": f"Could not crawl page: {e}"})
            continue
        if not pdf_urls:
            errors.append({"url": page_url, "error": "No PDF links found on this page."})
            continue
        for pdf_url in pdf_urls:
            if pdf_url in seen:
                continue
            seen.add(pdf_url)
            pdfs.append({"pdf_url": pdf_url, "source_page": page_url})
    return {"pdfs": pdfs, "errors": errors}


def download_selected(pdfs, dest_dir):
    """
    Downloads a caller-chosen subset of previously-discovered PDFs.
    pdfs: [{"pdf_url":..., "source_page":...}, ...]
    Returns: {
      "downloaded": [{"pdf_url":..., "source_page":..., "path":...}, ...],
      "errors": [{"url":..., "error":...}, ...]
    }
    """
    downloaded = []
    errors = []
    for item in pdfs:
        pdf_url = (item.get("pdf_url") or "").strip()
        source_page = item.get("source_page")
        if not pdf_url:
            continue
        try:
            path = download_pdf(pdf_url, dest_dir)
            downloaded.append({
                "pdf_url": pdf_url, "source_page": source_page, "path": path,
            })
        except Exception as e:
            errors.append({"url": pdf_url, "error": f"Could not download: {e}"})
    return {"downloaded": downloaded, "errors": errors}
