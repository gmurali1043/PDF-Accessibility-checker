// ============================================================================
// Shared helpers used by both the Upload tab and the Crawl tab. Each tab
// keeps its own state (selected files / discovered PDFs / batch id) so a
// run in one tab never touches the other tab's results.
// ============================================================================

const STATUS_ORDER = ["fail", "review", "manual", "pass", "na"];
const STATUS_LABELS = { fail: "Fail", review: "Needs review", manual: "Manual", pass: "Pass", na: "N/A" };

function escapeHtml(s) {
  if (s === null || s === undefined) return "";
  return String(s)
    .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function computeTotals(reports) {
  const totals = { pass: 0, fail: 0, na: 0, manual: 0, review: 0 };
  reports.forEach(r => {
    for (const k in totals) totals[k] += r.summary[k] || 0;
  });
  const scored = totals.pass + totals.fail;
  totals.score_pct = scored ? Math.round((100 * totals.pass) / scored) : null;
  return totals;
}

function renderOverview(container, reports) {
  container.innerHTML = "";
  const totals = computeTotals(reports);

  const overallChip = document.createElement("div");
  overallChip.className = "chip overall-chip";
  const scoreText = totals.score_pct !== null ? `${totals.score_pct}%` : "n/a";
  overallChip.textContent = `Overall conformance score (${reports.length} PDF${reports.length === 1 ? "" : "s"}): ${scoreText}`;
  container.appendChild(overallChip);

  const chipDefs = [
    ["pass", "Pass", "var(--pass-bg)", "var(--pass)"],
    ["fail", "Fail", "var(--fail-bg)", "var(--fail)"],
    ["review", "Needs review", "var(--review-bg)", "var(--review)"],
    ["manual", "Manual", "var(--manual-bg)", "var(--manual)"],
    ["na", "N/A", "var(--na-bg)", "var(--na)"],
  ];
  chipDefs.forEach(([key, label, bg, color]) => {
    const chip = document.createElement("div");
    chip.className = "chip";
    chip.style.background = bg;
    chip.style.color = color;
    chip.textContent = `${label}: ${totals[key]}`;
    container.appendChild(chip);
  });
}

function renderResultsInto(idPrefix, data) {
  const resultsSection = document.getElementById(`${idPrefix}-results`);
  resultsSection.hidden = false;

  renderOverview(document.getElementById(`${idPrefix}-overview`), data.reports);

  const list = document.getElementById(`${idPrefix}-reportList`);
  list.innerHTML = "";
  data.reports.forEach((report, idx) => list.appendChild(renderPdfAccordion(report, idx, idPrefix)));

  resultsSection.scrollIntoView({ behavior: "smooth", block: "start" });
}

function renderPdfAccordion(report, idx, idPrefix) {
  const details = document.createElement("details");
  details.className = "pdf-accordion";
  if (idx === 0) details.open = true;

  const summary = document.createElement("summary");
  const score = report.summary.score_pct !== null && report.summary.score_pct !== undefined
    ? `${report.summary.score_pct}%` : "n/a";
  const s = report.summary;
  summary.innerHTML =
    `<span class="pdf-accordion-title">${escapeHtml(report.filename)}</span>` +
    `<span class="score-badge">Score: ${escapeHtml(score)}</span>` +
    `<span class="mini-counts">` +
    `<span class="mini-count fail">${s.fail} fail</span>` +
    `<span class="mini-count review">${s.review} review</span>` +
    `<span class="mini-count manual">${s.manual} manual</span>` +
    `<span class="mini-count pass">${s.pass} pass</span>` +
    `</span>`;
  details.appendChild(summary);

  const body = document.createElement("div");
  body.className = "pdf-accordion-body";

  const meta = document.createElement("div");
  meta.className = "pdf-meta";
  const bits = [];
  if (report.source_url) bits.push(`Source: ${escapeHtml(report.source_url)}`);
  if (report.source_page) bits.push(`Found on: ${escapeHtml(report.source_page)}`);
  if (report.page_count !== null && report.page_count !== undefined) bits.push(`${report.page_count} pages`);
  bits.push(`Tagged PDF: ${report.tagged ? "Yes" : "No"}`);
  if (report.errors && report.errors.length) bits.push(`Notes: ${report.errors.map(escapeHtml).join("; ")}`);
  meta.innerHTML = bits.join(" &middot; ");
  body.appendChild(meta);

  if (!report.rows || !report.rows.length) {
    const p = document.createElement("p");
    p.textContent = "This file could not be analyzed.";
    body.appendChild(p);
    details.appendChild(body);
    return details;
  }

  const groupId = `${idPrefix}-pdf-${idx}`;

  // filter chips
  const filterRow = document.createElement("div");
  filterRow.className = "filter-row";
  filterRow.setAttribute("role", "group");
  filterRow.setAttribute("aria-label", `Filter results for ${report.filename}`);
  const allChip = mkFilterChip("all", "All", true);
  filterRow.appendChild(allChip);
  STATUS_ORDER.forEach(st => filterRow.appendChild(mkFilterChip(st, STATUS_LABELS[st], false)));
  body.appendChild(filterRow);

  const rowsContainer = document.createElement("div");
  rowsContainer.className = "rows-container";
  rowsContainer.id = `${groupId}-rows`;
  body.appendChild(rowsContainer);

  const sortedRows = [...report.rows].sort(
    (a, b) => STATUS_ORDER.indexOf(a.status) - STATUS_ORDER.indexOf(b.status)
  );
  sortedRows.forEach(row => rowsContainer.appendChild(renderTestRow(row)));

  filterRow.querySelectorAll(".filter-chip").forEach(chip => {
    chip.addEventListener("click", () => {
      filterRow.querySelectorAll(".filter-chip").forEach(c => {
        c.classList.remove("active");
        c.setAttribute("aria-pressed", "false");
      });
      chip.classList.add("active");
      chip.setAttribute("aria-pressed", "true");
      const status = chip.dataset.status;
      rowsContainer.querySelectorAll(".test-row").forEach(rowEl => {
        rowEl.style.display = (status === "all" || rowEl.dataset.status === status) ? "" : "none";
      });
    });
  });

  details.appendChild(body);
  return details;
}

function mkFilterChip(status, label, active) {
  const chip = document.createElement("button");
  chip.type = "button";
  chip.className = "filter-chip" + (active ? " active" : "");
  chip.dataset.status = status;
  chip.setAttribute("aria-pressed", active ? "true" : "false");
  chip.textContent = label;
  return chip;
}

function renderTestRow(row) {
  const div = document.createElement("div");
  div.className = `test-row ${row.status}`;
  div.dataset.status = row.status;

  const wcagStr = (row.wcag && row.wcag.length)
    ? row.wcag.map(w => `${w.criterion} (${w.level})`).join("; ") : "-";

  let html = `<h4>${escapeHtml(row.id)} &mdash; ${escapeHtml(row.title)} <span class="badge ${row.status}">${escapeHtml(row.status_label)}</span></h4>`;
  html += `<div class="row-meta">Category: ${escapeHtml(row.category)} &middot; WCAG: ${escapeHtml(wcagStr)} &middot; PDF/UA: ${escapeHtml(row.pdfua)}</div>`;
  html += `<div class="row-finding">${escapeHtml(row.summary)}</div>`;
  if (row.pages && row.pages.length) {
    html += `<div class="row-location"><strong>Location:</strong> Page(s) ${escapeHtml(row.pages.join(", "))}</div>`;
  }
  if (row.evidence && row.evidence.length) {
    html += "<ul class='row-evidence'>" + row.evidence.map(e => `<li>${escapeHtml(e)}</li>`).join("") + "</ul>";
  }
  if (["fail", "manual", "review"].includes(row.status) && row.remediation && row.remediation.length) {
    const label = row.status === "manual" ? "How to verify manually" : "Remediation steps";
    html += `<div class="row-steps"><strong>${label}:</strong><ol>` +
      row.remediation.map(s => `<li>${escapeHtml(s)}</li>`).join("") + "</ol></div>";
  }
  div.innerHTML = html;
  return div;
}

function showStatusIn(id, msg, isError) {
  const el = document.getElementById(id);
  el.hidden = false;
  el.textContent = msg;
  el.classList.toggle("error", !!isError);
  el.setAttribute("role", isError ? "alert" : "status");
}
function hideStatusIn(id) {
  document.getElementById(id).hidden = true;
}

function wireDownloadButtons(scopeEl, getBatchId) {
  scopeEl.querySelectorAll(".dl-btn").forEach(btn => {
    btn.onclick = () => {
      const batchId = getBatchId();
      if (!batchId) return;
      window.location.href = `/api/download/${batchId}/${btn.dataset.fmt}`;
    };
  });
}

// ============================================================================
// Accessible tabs (roving tabindex, arrow-key navigation)
// ============================================================================
(function initTabs() {
  const tabs = Array.from(document.querySelectorAll(".tab-btn"));
  function activate(tab) {
    tabs.forEach(t => {
      const selected = t === tab;
      t.classList.toggle("active", selected);
      t.setAttribute("aria-selected", selected ? "true" : "false");
      t.tabIndex = selected ? 0 : -1;
      const panel = document.getElementById("tab-" + t.dataset.tab);
      panel.hidden = !selected;
      panel.classList.toggle("active", selected);
    });
    tab.focus();
  }
  tabs.forEach((tab, i) => {
    tab.addEventListener("click", () => activate(tab));
    tab.addEventListener("keydown", e => {
      if (e.key === "ArrowRight" || e.key === "ArrowLeft") {
        e.preventDefault();
        const dir = e.key === "ArrowRight" ? 1 : -1;
        const next = tabs[(i + dir + tabs.length) % tabs.length];
        activate(next);
      }
    });
  });
})();

// ============================================================================
// Upload tab
// ============================================================================
const UploadTab = (() => {
  let selectedFiles = [];
  let batchId = null;

  const dropzone = document.getElementById("dropzone");
  const fileInput = document.getElementById("fileInput");
  const fileList = document.getElementById("fileList");
  const runBtn = document.getElementById("runUploadBtn");
  const resultsEl = document.getElementById("upload-results");

  dropzone.addEventListener("click", () => fileInput.click());
  dropzone.addEventListener("keydown", e => {
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      fileInput.click();
    }
  });
  dropzone.addEventListener("dragover", e => { e.preventDefault(); dropzone.classList.add("drag"); });
  dropzone.addEventListener("dragleave", () => dropzone.classList.remove("drag"));
  dropzone.addEventListener("drop", e => {
    e.preventDefault();
    dropzone.classList.remove("drag");
    addFiles(e.dataTransfer.files);
  });
  fileInput.addEventListener("change", () => addFiles(fileInput.files));

  function addFiles(fileListObj) {
    for (const f of fileListObj) {
      if (f.name.toLowerCase().endsWith(".pdf")) selectedFiles.push(f);
    }
    renderFileList();
  }

  function renderFileList() {
    fileList.innerHTML = "";
    selectedFiles.forEach(f => {
      const li = document.createElement("li");
      li.textContent = `${f.name} (${(f.size / 1024).toFixed(0)} KB)`;
      fileList.appendChild(li);
    });
    runBtn.disabled = selectedFiles.length === 0;
  }

  runBtn.addEventListener("click", async () => {
    const fd = new FormData();
    selectedFiles.forEach(f => fd.append("pdfs", f));
    showStatusIn("upload-status", `Analyzing ${selectedFiles.length} PDF(s)... this can take a minute for large or scanned files.`);
    try {
      const resp = await fetch("/api/check-upload", { method: "POST", body: fd });
      const data = await resp.json();
      if (!resp.ok) throw new Error(data.error || "Request failed");
      hideStatusIn("upload-status");
      batchId = data.batch_id;
      renderResultsInto("upload", data);
    } catch (e) {
      showStatusIn("upload-status", "Error: " + e.message, true);
    }
  });

  wireDownloadButtons(resultsEl, () => batchId);

  return {};
})();

// ============================================================================
// Crawl tab: discover PDFs -> user selects -> run checks on selection only
// ============================================================================
const CrawlTab = (() => {
  let discovered = []; // [{pdf_url, source_page}]
  let batchId = null;

  const discoverBtn = document.getElementById("runDiscoverBtn");
  const urlInput = document.getElementById("urlInput");
  const pickerSection = document.getElementById("crawl-picker");
  const checklist = document.getElementById("pdfCheckList");
  const selectAll = document.getElementById("selectAllPdfs");
  const countLabel = document.getElementById("pdf-selected-count");
  const runCheckBtn = document.getElementById("runCrawlCheckBtn");
  const resultsEl = document.getElementById("crawl-results");

  discoverBtn.addEventListener("click", async () => {
    const urls = urlInput.value.split("\n").map(s => s.trim()).filter(Boolean);
    if (!urls.length) { showStatusIn("crawl-discover-status", "Enter at least one URL.", true); return; }

    pickerSection.hidden = true;
    document.getElementById("crawl-results").hidden = true;
    showStatusIn("crawl-discover-status", `Scanning ${urls.length} page(s) for PDF links...`);
    try {
      const resp = await fetch("/api/crawl-discover", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ urls }),
      });
      const data = await resp.json();
      if (!resp.ok) throw new Error(data.error || "Request failed");

      discovered = data.pdfs || [];
      if (data.errors && data.errors.length) {
        const msgs = data.errors.map(e => `${e.url}: ${e.error}`).join(" | ");
        showStatusIn("crawl-discover-status", "Some pages had issues: " + msgs, discovered.length === 0);
      } else {
        hideStatusIn("crawl-discover-status");
      }
      renderChecklist();
    } catch (e) {
      showStatusIn("crawl-discover-status", "Error: " + e.message, true);
    }
  });

  function renderChecklist() {
    checklist.innerHTML = "";
    if (!discovered.length) {
      pickerSection.hidden = true;
      return;
    }
    discovered.forEach((item, i) => {
      const li = document.createElement("li");
      const id = `pdfcb-${i}`;
      const filename = item.pdf_url.split("/").pop().split("?")[0] || item.pdf_url;
      li.innerHTML =
        `<label for="${id}">` +
        `<input type="checkbox" id="${id}" class="pdf-cb" data-idx="${i}">` +
        `<span class="pdf-cb-name">${escapeHtml(filename)}</span>` +
        `<span class="pdf-cb-meta">${escapeHtml(item.pdf_url)} &middot; found on ${escapeHtml(item.source_page)}</span>` +
        `</label>`;
      checklist.appendChild(li);
    });
    pickerSection.hidden = false;
    selectAll.checked = false;
    selectAll.indeterminate = false;
    checklist.querySelectorAll(".pdf-cb").forEach(cb => cb.addEventListener("change", updateSelectionState));
    updateSelectionState();
    pickerSection.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  selectAll.addEventListener("change", () => {
    checklist.querySelectorAll(".pdf-cb").forEach(cb => { cb.checked = selectAll.checked; });
    updateSelectionState();
  });

  function getCheckboxes() {
    return Array.from(checklist.querySelectorAll(".pdf-cb"));
  }

  function updateSelectionState() {
    const boxes = getCheckboxes();
    const checked = boxes.filter(cb => cb.checked);
    countLabel.textContent = `${checked.length} of ${boxes.length} selected`;
    runCheckBtn.disabled = checked.length === 0;
    selectAll.checked = boxes.length > 0 && checked.length === boxes.length;
    selectAll.indeterminate = checked.length > 0 && checked.length < boxes.length;
  }

  runCheckBtn.addEventListener("click", async () => {
    const boxes = getCheckboxes().filter(cb => cb.checked);
    const pdfs = boxes.map(cb => discovered[Number(cb.dataset.idx)]);
    if (!pdfs.length) return;

    document.getElementById("crawl-results").hidden = true;
    showStatusIn("crawl-status", `Downloading and analyzing ${pdfs.length} PDF(s)... this can take a minute for large or scanned files.`);
    try {
      const resp = await fetch("/api/crawl-check", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ pdfs }),
      });
      const data = await resp.json();
      if (!resp.ok) throw new Error(data.error || "Request failed");

      if (data.download_errors && data.download_errors.length) {
        const msgs = data.download_errors.map(e => `${e.url}: ${e.error}`).join(" | ");
        showStatusIn("crawl-status", "Some PDFs could not be downloaded: " + msgs, (data.reports || []).length === 0);
      } else {
        hideStatusIn("crawl-status");
      }
      batchId = data.batch_id;
      if (data.reports && data.reports.length) renderResultsInto("crawl", data);
    } catch (e) {
      showStatusIn("crawl-status", "Error: " + e.message, true);
    }
  });

  wireDownloadButtons(resultsEl, () => batchId);

  return {};
})();
