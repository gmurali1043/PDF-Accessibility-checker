# PDF Accessibility Checker

A local, browser-based tool that tests PDFs against your **34 custom PDF-1
through PDF-10 test cases**, mapped to the matching **WCAG 2.2 success
criterion** and **PDF/UA-1 clause**, with numbered, plain-language
remediation steps for every failure - including tests that can only be
verified by a human, which are clearly labeled and explained.

Runs entirely on your machine. No PDF content is ever sent anywhere except
to your own local Flask server.

## Why this instead of PAC 2024 / Adobe Acrobat Pro's checker?

Those tools are excellent generic PDF/UA validators, but they:

- Report against generic PDF/UA rule IDs, not **your organization's test
  case IDs** (PDF-8-1, etc.), so failures don't map cleanly back to your
  documented test suite.
- Don't tell you, item by item, whether a failing test **can** be automated
  or genuinely **needs a human** - PAC lumps a lot of "needs manual check"
  items in with hard fails, and Acrobat's checker only partially separates
  them.
- Don't batch-test a folder of PDFs and give you one grouped report.
- Can't crawl a website, find every linked PDF, and test the whole batch in
  one run.
- Don't export to Markdown/HTML/XLSX in one click for sharing with
  non-technical stakeholders or filing as evidence.

This tool is built specifically to close those four gaps on top of your own
test case definitions. It is **not** a replacement for a full manual audit -
roughly a third of the 34 test cases (color contrast, video captions, "not
images of text", etc.) cannot be determined from a PDF's file structure
alone under any tool, PAC and Acrobat included, and this tool is explicit
about that rather than guessing.

## What it actually checks (automation levels)

Every test case in `checker/registry.py` is tagged with an automation
level, and the live result always shows one of five statuses:

| Status | Meaning |
|---|---|
| **Pass** | Automated structural analysis found no issue |
| **Fail** | Automated structural analysis found a definite issue |
| **N/A** | The feature this test covers isn't present in the document (e.g. no tables) |
| **Needs review** | An automated signal was produced, but a human should confirm it (e.g. "notes are tagged with unique IDs - confirm they sit right after the reference") |
| **Manual check needed** | Cannot be determined by static analysis at all (color contrast, blinking content, video captions, etc.) - always includes numbered steps explaining exactly how to check it by hand |

Roughly 15 of the 34 test cases are fully automated (title, headings,
lists, tables, alt text, links, language, bookmarks, form structure...),
~10 are semi-automated ("review"), and the remainder are true manual checks
per WCAG/PDF-UA's own design (contrast, media captions/audio-description,
images-of-text, etc.) - these simply cannot be derived from a PDF's
internal structure by *any* automated tool.

The full test case -> WCAG -> PDF/UA -> remediation mapping lives in
`checker/registry.py`, sourced directly from your uploaded test case
documents (`PDF-1` through `PDF-10`).

## Running it locally

Requires Python 3.10+.

```bash
cd pdf_a11y_checker
pip install -r requirements.txt
python app.py
```

Then open **http://127.0.0.1:5050** in your browser.

- **Tab 1 - Upload PDFs**: drag & drop one or many PDF files, click "Run
  accessibility checks".
- **Tab 2 - Crawl Web Pages**: paste one URL per line; the tool fetches
  each page, finds every linked/embedded PDF (`<a href>`, `<iframe>`,
  `<embed>`, `<object>`), downloads them locally, and runs the same checks.

Results are grouped by PDF, with a filter bar per PDF (All / Fail / Needs
review / Manual / Pass / N/A) and an overall summary chip bar. Use the
**.html / .md / .xlsx** buttons to download the full report - each format
keeps results grouped by PDF (the XLSX gives each PDF its own sheet, plus a
Summary sheet).

## Project structure

```
app.py                     Flask app: routes for upload, crawl, download
checker/
  registry.py               The 34 test cases: WCAG ref, PDF/UA ref,
                             automation level, remediation/manual steps
  structure.py               Loads a PDF with pikepdf, builds a simplified
                             structure-tree (tag tree), AcroForm field list,
                             annotations, outlines, page labels, etc.
  checks.py                   One function per test case; operates on the
                             parsed PDF context, returns pass/fail/na/
                             manual/review + evidence
  report.py                   Combines registry + live check results into
                             one report object per PDF
  exporters.py                Markdown / HTML / XLSX generation, grouped
                             by PDF
  crawler.py                  Given webpage URL(s), finds and downloads
                             linked PDFs
templates/index.html        Two-tab single page UI
static/style.css, app.js    Frontend styling and logic
```

## Known limitations (be aware of these)

- **Color/contrast checks (PDF-2-1, 2-2, 2-3)** are always manual - accurately
  sampling rendered colors requires full page rasterization plus knowing
  which pixels are "meaningful" text vs. decoration, which is unreliable to
  automate safely. Follow the given WebAIM-based steps instead.
- **"Images of text" (PDF-4-4) and layout-table detection (PDF-7-2)**
  require visual/semantic judgment a script can't reliably make.
- **Video/audio checks (PDF-10-2 to 10-4)** only detect *whether* a
  `/Screen`, `/RichMedia`, or `/Movie` annotation exists; verifying the
  actual captions/audio description/transcript content is always manual.
- The **reading-order** and **tab-order** checks (PDF-5-2) verify the
  `/Tabs` page attribute structurally, but a full "does this feel right
  when tabbing through with a keyboard" pass is still recommended.
- The web crawler only follows links found directly on the given page (no
  recursive crawling of the whole site) - point it at each index/listing
  page that links to your PDFs.
- Very large or heavily scanned PDFs may take a while to parse; there's no
  hard timeout in the current version.

## Extending it

- Add/adjust test cases and remediation text in `checker/registry.py`.
- Add a new automated check by writing a `check_X_Y(ctx)` function in
  `checker/checks.py` and registering it in `CHECK_FUNCS`.
- `ctx` (a `PDFContext` from `structure.py`) already exposes: `tag_root`
  (walkable tag tree with `.find_all()`, `.walk()`, `.parent`), `lang`,
  `title`, `display_doc_title`, `outlines_present`, `page_labels_present`,
  `acroform_fields`, `media_annots`, `page_tabs`, and more - most new checks
  can be built entirely from these without touching `structure.py`.
