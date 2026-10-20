"""
One function per test case. Every function takes a loaded PDFContext and
returns a dict:
    {
        "status": "pass" | "fail" | "na" | "manual" | "review",
        "summary": short human sentence,
        "evidence": [ list of short strings with specifics / page refs ],
    }

status meanings:
    pass    - automated check ran and found no issue
    fail    - automated check ran and found a definite issue
    na      - the feature this test covers is not present in the document
    manual  - cannot be determined by static analysis; always needs a human
    review  - an automated signal was produced but a human should confirm it
"""

STANDARD_TAGS = {
    "Document", "Part", "Art", "Sect", "Div", "BlockQuote", "Caption",
    "TOC", "TOCI", "Index", "NonStruct", "Private",
    "P", "H", "H1", "H2", "H3", "H4", "H5", "H6",
    "L", "LI", "Lbl", "LBody",
    "Table", "TR", "TH", "TD", "THead", "TBody", "TFoot",
    "Span", "Quote", "Note", "Reference", "BibEntry", "Code", "Link", "Annot",
    "Ruby", "RB", "RT", "RP", "Warichu", "WT", "WP",
    "Figure", "Formula", "Form", "Artifact",
    "OBJR", "StructTreeRoot", "MC",
}


def _r(status, summary, evidence=None, pages=None):
    return {"status": status, "summary": summary, "evidence": evidence or [],
            "pages": sorted({p for p in (pages or []) if p is not None})}


def _pagetag(page):
    """Formats a page number for inline evidence text, e.g. ' (page 5)'."""
    return f" (page {page})" if page is not None else ""


def _manual(tc):
    from .registry import get_test_case
    steps = get_test_case(tc).get("manual_steps", [])
    return _r("manual", "Requires manual verification - see remediation steps.", steps)


# --------------------------------------------------------------------- PDF-1
def check_1_1(ctx):
    # Placeholder - the report builder overwrites this with an aggregate
    # pass/fail once every other check has run.
    return _r("review", "Aggregate result computed after all other checks run.")


def check_1_2(ctx):
    has_title = bool(ctx.title and ctx.title.strip())
    if has_title and ctx.display_doc_title:
        return _r("pass", f"Document title is set (\"{ctx.title}\") and the "
                           f"viewer is configured to display it.")
    problems = []
    if not has_title:
        problems.append("no Title is set in document properties")
    if not ctx.display_doc_title:
        problems.append("ViewerPreferences is not set to display the "
                         "document title (DisplayDocTitle)")
    return _r("fail", "Document title is incomplete: " + "; ".join(problems) + ".",
               [f"Title found: {ctx.title!r}", f"DisplayDocTitle: {ctx.display_doc_title}"])


# --------------------------------------------------------------------- PDF-2
def check_2_1(ctx):
    return _manual("PDF-2-1")


def check_2_2(ctx):
    return _manual("PDF-2-2")


def check_2_3(ctx):
    return _manual("PDF-2-3")


# --------------------------------------------------------------------- PDF-3
def check_3_1(ctx):
    if not ctx.tagged_pdf:
        return _r("fail", "Document has no structure tree - it is untagged.")
    unmapped = sorted(
        t for t in ctx.all_struct_types
        if t not in STANDARD_TAGS and t not in ctx.role_map
    )
    if unmapped:
        nodes_by_tag = {}
        for n in ctx.tag_root.walk():
            if n.tag in unmapped:
                nodes_by_tag.setdefault(n.tag, []).append(n)
        evidence = []
        pages = []
        for t in unmapped:
            tag_pages = sorted({n.page for n in nodes_by_tag.get(t, []) if n.page})
            pages.extend(tag_pages)
            sample = ", ".join(str(p) for p in tag_pages[:10])
            more = f" (+{len(tag_pages) - 10} more)" if len(tag_pages) > 10 else ""
            loc = f" - found on page(s): {sample}{more}" if sample else ""
            evidence.append(f"Unmapped custom tag: <{t}>{loc}")
        return _r("fail",
                   f"{len(unmapped)} non-standard tag type(s) are not mapped "
                   f"in RoleMap to a standard tag.",
                   evidence, pages)
    return _r("review", "Document is tagged and all custom tags (if any) are "
                         "mapped in RoleMap. Manually confirm tag semantics "
                         "and reading order match the visible content.")


def check_3_2(ctx):
    if not ctx.tagged_pdf:
        return _r("na", "Document is untagged; table of contents structure "
                         "cannot be evaluated.")
    tocs = ctx.tag_root.find_all("TOC") if ctx.tag_root else []
    if not tocs:
        return _r("na", "No <TOC> tag found in the document.")
    issues = []
    pages = []
    for i, toc in enumerate(tocs, start=1):
        tocis = [c for c in toc.children if c.tag == "TOCI"]
        if not tocis:
            issues.append(f"TOC #{i} has no <TOCI> children.{_pagetag(toc.page)}")
            pages.append(toc.page)
        for j, toci in enumerate(tocis, start=1):
            has_ref = any(
                n.tag in ("Reference",) and any(g.tag == "OBJR" for g in n.children)
                for n in toci.walk()
            ) or any(n.tag == "OBJR" for n in toci.walk())
            if not has_ref:
                issues.append(f"TOC #{i}, entry #{j}: <TOCI> has no link "
                               f"reference (Reference/OBJR).{_pagetag(toci.page)}")
                pages.append(toci.page)
    if issues:
        return _r("fail", f"{len(issues)} issue(s) found across {len(tocs)} "
                           f"table(s) of contents.", issues, pages)
    return _r("pass", f"{len(tocs)} table(s) of contents correctly tagged "
                       f"with <TOC>/<TOCI> and link references.")


def check_3_3(ctx):
    if not ctx.tagged_pdf:
        return _r("na", "Document is untagged; headings cannot be evaluated.")
    headings = []
    for n in ctx.tag_root.walk():
        if n.tag == "H":
            headings.append((n, 1))  # generic H, treat as level 1 nominally
        elif len(n.tag) == 2 and n.tag[0] == "H" and n.tag[1].isdigit():
            headings.append((n, int(n.tag[1])))
    if not headings:
        return _r("na", "No heading tags (<H1>-<H6>) are used in this document.")

    issues = []
    pages = []
    seq = [lvl for _, lvl in headings]
    if seq[0] != 1:
        issues.append(f"The first heading in the document is <H{seq[0]}>, "
                       f"but <H1> should come first.{_pagetag(headings[0][0].page)}")
        pages.append(headings[0][0].page)
    for i in range(1, len(seq)):
        prev, cur = seq[i - 1], seq[i]
        if cur > prev + 1:
            issues.append(f"Heading level jumps from <H{prev}> to <H{cur}> "
                           f"(heading #{i + 1}) without an intervening "
                           f"<H{prev + 1}>.{_pagetag(headings[i][0].page)}")
            pages.append(headings[i][0].page)
    if issues:
        return _r("fail", f"{len(issues)} heading-order issue(s) found among "
                           f"{len(headings)} headings.", issues, pages)
    return _r("pass", f"{len(headings)} headings found and correctly "
                       f"ordered without skipped levels.")


def check_3_4(ctx):
    if not ctx.tagged_pdf:
        return _r("na", "Document is untagged; lists cannot be evaluated.")
    lists = ctx.tag_root.find_all("L")
    if not lists:
        return _r("na", "No <L> (list) tags found in this document.")
    issues = []
    pages = []
    for i, l in enumerate(lists, start=1):
        real_children = [c for c in l.children if c.tag not in ("Artifact",)]
        li_children = [c for c in real_children if c.tag == "LI"]
        stray = [c for c in real_children if c.tag not in ("LI", "Caption")]
        if not li_children:
            issues.append(f"List #{i}: <L> has no <LI> child items.{_pagetag(l.page)}")
            pages.append(l.page)
        if stray:
            issues.append(f"List #{i}: <L> has {len(stray)} child element(s) "
                           f"that are neither <LI> nor <Caption> "
                           f"({', '.join(sorted(set(c.tag for c in stray)))})."
                           f"{_pagetag(l.page)}")
            pages.append(l.page)
        for j, li in enumerate(li_children, start=1):
            if not any(c.tag == "LBody" for c in li.children) and not li.children:
                issues.append(f"List #{i}, item #{j}: <LI> has no <LBody> "
                               f"and no content.{_pagetag(li.page)}")
                pages.append(li.page)
    if issues:
        return _r("fail", f"{len(issues)} issue(s) found across {len(lists)} "
                           f"list(s).", issues, pages)
    return _r("pass", f"{len(lists)} list(s) correctly tagged with <L>/<LI>.")


def check_3_5(ctx):
    if not ctx.tagged_pdf:
        return _r("na", "Document is untagged; notes cannot be evaluated.")
    notes = ctx.tag_root.find_all("Note")
    if not notes:
        return _r("na", "No <Note> tags (footnotes/endnotes) found.")
    issues = []
    pages = []
    ids_seen = {}
    for i, n in enumerate(notes, start=1):
        nid = n.attrs.get("ID")
        if not nid:
            issues.append(f"Note #{i}: missing an ID entry.{_pagetag(n.page)}")
            pages.append(n.page)
        elif nid in ids_seen:
            issues.append(f"Note #{i}: ID {nid!r} duplicates note #{ids_seen[nid]}."
                           f"{_pagetag(n.page)}")
            pages.append(n.page)
        else:
            ids_seen[nid] = i
    if issues:
        return _r("fail", f"{len(issues)} issue(s) found across {len(notes)} "
                           f"note(s).", issues, pages)
    return _r("review", f"{len(notes)} note(s) found, each tagged <Note> "
                         f"with a unique ID. Manually confirm footnotes are "
                         f"positioned immediately after the referencing text.")


def check_3_6(ctx):
    if not ctx.tagged_pdf:
        return _r("na", "Document is untagged; formulas cannot be evaluated.")
    formulas = ctx.tag_root.find_all("Formula")
    if not formulas:
        return _r("manual", "No <Formula> tags were detected. If this "
                             "document contains mathematical expressions, "
                             "they must be tagged manually - static analysis "
                             "cannot detect un-tagged math.",
                   ["Visually confirm whether the document contains any "
                    "equations or formulas that are not wrapped in a "
                    "<Formula> tag with Alt text."])
    missing_alt = [(i, f) for i, f in enumerate(formulas, start=1) if not f.alt]
    if missing_alt:
        return _r("fail", f"{len(missing_alt)} of {len(formulas)} <Formula> "
                           f"tag(s) are missing Alt text.",
                   [f"Formula #{i} has no Alt text.{_pagetag(f.page)}"
                    for i, f in missing_alt],
                   [f.page for _, f in missing_alt])
    return _r("review", f"{len(formulas)} <Formula> tag(s) found, each with "
                         f"Alt text. Manually confirm the Alt text "
                         f"accurately describes each equation.")


# --------------------------------------------------------------------- PDF-4
def check_4_1(ctx):
    if not ctx.tagged_pdf:
        return _r("na", "Document is untagged; images cannot be evaluated.")
    figures = ctx.tag_root.find_all("Figure")
    if not figures:
        return _r("na", "No <Figure> tags (images) found in this document.")
    issues = []
    pages = []
    for i, f in enumerate(figures, start=1):
        alt = (f.alt or "").strip()
        if not alt:
            issues.append(f"Figure #{i}: no Alt text set.{_pagetag(f.page)}")
            pages.append(f.page)
        elif len(alt) > 150:
            issues.append(f"Figure #{i}: Alt text is {len(alt)} characters "
                           f"(over the 150-character limit) - use a shorter "
                           f"Alt text plus a nearby elaborated description "
                           f"instead.{_pagetag(f.page)}")
            pages.append(f.page)
        elif alt.lower() in ("image", "picture", "graphic", "photo", ".jpg", ".png"):
            issues.append(f"Figure #{i}: Alt text ({alt!r}) is generic and "
                           f"not descriptive.{_pagetag(f.page)}")
            pages.append(f.page)
    if issues:
        return _r("fail", f"{len(issues)} of {len(figures)} image(s) have "
                           f"Alt text problems.", issues, pages)
    return _r("pass", f"All {len(figures)} tagged image(s) have descriptive "
                       f"Alt text under 150 characters.")


def check_4_2(ctx):
    if not ctx.tagged_pdf:
        return _r("na", "Document is untagged; cannot evaluate decorative "
                         "image marking.")
    figures = ctx.tag_root.find_all("Figure")
    candidates = [(i, f) for i, f in enumerate(figures, start=1)
                  if not (f.alt or "").strip()]
    image_count_hint = None
    try:
        if ctx.plumber_pages is not None:
            image_count_hint = sum(len(p.images) for p in ctx.plumber_pages)
    except Exception:
        pass
    evidence = [f"Figure #{i} has no Alt text - confirm whether it is "
                f"decorative (mark as Artifact) or meaningful (add Alt "
                f"text, see PDF-4-1).{_pagetag(f.page)}" for i, f in candidates]
    if image_count_hint is not None and ctx.tagged_pdf:
        evidence.append(f"Raw image objects detected on pages: "
                         f"{image_count_hint}; tagged <Figure> elements: "
                         f"{len(figures)}. A large gap can mean images were "
                         f"left untagged instead of properly marked as "
                         f"Artifact.")
    if not candidates and (image_count_hint or 0) <= len(figures):
        return _r("pass", "No untagged/alt-less figures found that would "
                           "need decorative review.")
    return _r("review", f"{len(candidates)} figure(s) with empty Alt text "
                         f"need manual review to confirm decorative status.",
               evidence, [f.page for _, f in candidates])


def check_4_3(ctx):
    if not ctx.tagged_pdf:
        return _r("na", "Document is untagged; captions cannot be evaluated.")
    captions = ctx.tag_root.find_all("Caption")
    if not captions:
        return _r("na", "No <Caption> tags found in this document.")
    fig_captions = [c for c in captions if c.parent and c.parent.tag == "Figure"]
    other_captions = [c for c in captions if not (c.parent and c.parent.tag == "Figure")]
    issues = []
    pages = []
    for c in other_captions:
        parent_tag = c.parent.tag if c.parent else "root"
        if parent_tag not in ("Table", "L", "TOC"):
            issues.append(f"A <Caption> tag's parent is <{parent_tag}>, not "
                           f"a <Figure> (or other valid container)."
                           f"{_pagetag(c.page)}")
            pages.append(c.page)
    if issues:
        return _r("fail", f"{len(issues)} caption(s) are not correctly "
                           f"nested under a <Figure> tag.", issues, pages)
    return _r("pass", f"{len(fig_captions)} image caption(s) correctly "
                       f"tagged <Caption> under <Figure>.")


def check_4_4(ctx):
    return _manual("PDF-4-4")


# --------------------------------------------------------------------- PDF-5
def check_5_1(ctx):
    if not ctx.lang:
        return _r("fail", "No document-level Lang property is set.")
    lang = ctx.lang.strip()
    ok = 2 <= len(lang.split("-")[0]) <= 3
    if ok:
        return _r("pass", f"Document language is set to {lang!r}.")
    return _r("fail", f"Document Lang value {lang!r} does not look like a "
                       f"valid language code.")


def check_5_2(ctx):
    tabs = getattr(ctx, "page_tabs", [])
    if not tabs:
        return _r("manual", "Could not read page /Tabs entries.",
                   ["Manually confirm reading order using Acrobat's Reading "
                    "Order tool."])
    bad_pages = [i + 1 for i, t in enumerate(tabs) if t != "/S"]
    if bad_pages:
        sample = bad_pages[:15]
        more = f" (+{len(bad_pages) - 15} more)" if len(bad_pages) > 15 else ""
        return _r("fail", f"{len(bad_pages)} of {len(tabs)} page(s) do not "
                           f"use structure order (/Tabs /S) for tab "
                           f"navigation.",
                   [f"Pages without structure tab order: "
                    f"{', '.join(map(str, sample))}{more}"],
                   bad_pages)
    return _r("review", "All pages use document-structure tab order "
                         "(/Tabs /S). Manually confirm the visual reading "
                         "order and keyboard tab order still make sense.")


def check_5_3(ctx):
    if not ctx.tagged_pdf:
        return _manual("PDF-5-3")
    artifacts = ctx.tag_root.find_all("Artifact")
    pagination_hint = any(
        a.obj is not None and _has_pagination_type(a.obj) for a in artifacts
    )
    steps = []
    from .registry import get_test_case
    steps.extend(get_test_case("PDF-5-3")["manual_steps"])
    if pagination_hint:
        return _r("review", "Artifacts marked with a Pagination subtype were "
                             "found (a good sign headers/footers are "
                             "artifacted). Manually confirm consistency "
                             "across pages.", steps)
    return _r("manual", "No explicit Pagination-type artifacts were "
                         "detected. Manually confirm headers/footers are "
                         "consistent and, if repeated on every page, marked "
                         "as artifacts.", steps)


def _has_pagination_type(obj):
    try:
        a = obj.get("/A")
        if a is None:
            return False
        entries = a if hasattr(a, "__iter__") and not isinstance(a, dict) else [a]
        for e in entries:
            try:
                if str(e.get("/Type", "")) == "/Pagination":
                    return True
            except Exception:
                continue
    except Exception:
        pass
    return False


def check_5_4(ctx):
    if not ctx.tagged_pdf:
        return _r("na", "Document is untagged; language of parts cannot be "
                         "evaluated.")
    if not ctx.lang:
        return _r("manual", "No document language is set, so language-of-"
                             "parts cannot be compared automatically.",
                   ["Set the document language first (see PDF-5-1), then "
                    "re-check this item."])
    doc_lang = ctx.lang.split("-")[0].lower()
    overrides = [n for n in ctx.tag_root.walk()
                 if n.lang and n.lang.split("-")[0].lower() != doc_lang]
    if overrides:
        return _r("review", f"{len(overrides)} tag(s) declare a different "
                             f"language than the document default "
                             f"({ctx.lang}). Manually confirm these are "
                             f"correctly placed and no other foreign-"
                             f"language passages are missing a Lang "
                             f"override.",
                   [f"<{n.tag}> tagged Lang={n.lang!r}" for n in overrides[:20]])
    return _r("manual", "No language overrides were found in the tag tree. "
                         "Manually confirm the document genuinely contains "
                         "no foreign-language words or phrases.")


# --------------------------------------------------------------------- PDF-6
def check_6_1(ctx):
    steps = []
    from .registry import get_test_case
    steps.extend(get_test_case("PDF-6-1")["manual_steps"])
    if ctx.page_labels_present:
        return _r("review", "Custom Page Labels are defined in this "
                             "document. Manually confirm the labels match "
                             "the printed page numbers.", steps)
    return _r("manual", "No custom Page Labels are defined (viewer will "
                         "show plain PDF page counts 1, 2, 3...). Manually "
                         "confirm this matches the document's printed page "
                         "numbers.", steps)


def check_6_2(ctx):
    if ctx.page_count < 21:
        return _r("na", f"Document is {ctx.page_count} page(s) long "
                         f"(under the 21-page threshold).")
    if ctx.outlines_present and ctx.outline_count > 0:
        return _r("pass", f"Document is {ctx.page_count} pages and has "
                           f"{ctx.outline_count} bookmark(s).")
    return _r("fail", f"Document is {ctx.page_count} pages but has no "
                       f"bookmarks.")


# --------------------------------------------------------------------- PDF-7
def check_7_1(ctx):
    if not ctx.tagged_pdf:
        return _r("na", "Document is untagged; tables cannot be evaluated.")
    tables = ctx.tag_root.find_all("Table")
    if not tables:
        return _r("na", "No <Table> tags found in this document.")
    issues = []
    pages = []
    for i, t in enumerate(tables, start=1):
        trs = [n for n in t.walk() if n.tag == "TR"]
        ths = [n for n in t.walk() if n.tag == "TH"]
        tds = [n for n in t.walk() if n.tag == "TD"]
        if not trs:
            issues.append(f"Table #{i}: no <TR> row tags found.{_pagetag(t.page)}")
            pages.append(t.page)
        if not ths and not tds:
            issues.append(f"Table #{i}: no <TH>/<TD> cell tags found.{_pagetag(t.page)}")
            pages.append(t.page)
        for j, th in enumerate(ths, start=1):
            if not th.attrs.get("Scope") and not th.attrs.get("Headers"):
                issues.append(f"Table #{i}, header cell #{j}: <TH> has no "
                               f"Scope attribute (and no Headers/IDs "
                               f"association).{_pagetag(th.page)}")
                pages.append(th.page)
    if issues:
        return _r("fail", f"{len(issues)} issue(s) found across {len(tables)} "
                           f"table(s).", issues, pages)
    return _r("pass", f"{len(tables)} table(s) correctly tagged with "
                       f"<Table>/<TR>/<TH scope>/<TD>.")


def check_7_2(ctx):
    return _manual("PDF-7-2")


# --------------------------------------------------------------------- PDF-8
def check_8_1(ctx):
    if not ctx.tagged_pdf:
        return _r("na", "Document is untagged; links cannot be evaluated.")
    links = ctx.tag_root.find_all("Link")
    if not links:
        total_link_annots = sum(ctx.link_annots_per_page)
        if total_link_annots:
            pages_with_links = [i + 1 for i, c in
                                 enumerate(ctx.link_annots_per_page) if c]
            return _r("fail", f"{total_link_annots} Link annotation(s) exist "
                               f"on the page(s) but none are wrapped in a "
                               f"<Link> structure tag.",
                       [f"Link annotations found on page(s): "
                        f"{', '.join(map(str, pages_with_links))}"],
                       pages_with_links)
        return _r("na", "No links found in this document.")
    issues = []
    pages = []
    for i, l in enumerate(links, start=1):
        has_objr = any(n.tag == "OBJR" for n in l.walk())
        if not has_objr:
            issues.append(f"Link #{i}: <Link> tag has no OBJR reference to "
                           f"the link annotation.{_pagetag(l.page)}")
            pages.append(l.page)
    if issues:
        return _r("fail", f"{len(issues)} of {len(links)} link(s) are "
                           f"missing a structural OBJR reference.", issues, pages)
    return _r("review", f"{len(links)} link(s) correctly tagged with "
                         f"<Link>/OBJR. Manually confirm each link's visible "
                         f"text clearly describes its destination (avoid "
                         f"'click here' / bare URLs).")


# --------------------------------------------------------------------- PDF-9
def check_9_1(ctx):
    if not ctx.acroform_fields:
        return _r("na", "No form fields found in this document.")
    if not ctx.tagged_pdf:
        return _r("fail", "Document has form fields but no structure tree, "
                           "so none of them can be tagged with <Form>.")
    form_nodes = ctx.tag_root.find_all("Form")
    tagged_objids = set()
    for fnode in form_nodes:
        for n in fnode.walk():
            if n.tag == "OBJR" and n.attrs.get("RefObjId") is not None:
                tagged_objids.add(n.attrs["RefObjId"])
    issues = []
    pages = []
    for f in ctx.acroform_fields:
        widget_ids = set(f.get("_objids", []))
        if not widget_ids or not (widget_ids & tagged_objids):
            issues.append(f"Field {f['name']!r} (page {f.get('page') or '?'}) "
                           f"is not nested inside a <Form> tag.")
            pages.append(f.get("page"))
    if issues:
        return _r("fail", f"{len(issues)} of {len(ctx.acroform_fields)} "
                           f"field(s) are not correctly tagged.", issues, pages)
    return _r("pass", f"All {len(ctx.acroform_fields)} form field(s) are "
                       f"nested inside a <Form> tag.")


def check_9_2(ctx):
    if not ctx.acroform_fields:
        return _r("na", "No form fields found in this document.")
    issues = []
    tooltip_map = {}
    for f in ctx.acroform_fields:
        tt = (f.get("tooltip") or "").strip()
        if not tt:
            issues.append(f"Field {f['name']!r}: no tooltip set.")
            continue
        if tt in tooltip_map:
            issues.append(f"Field {f['name']!r}: tooltip {tt!r} duplicates "
                           f"field {tooltip_map[tt]!r} - tooltips should be "
                           f"unique and specific.")
        tooltip_map[tt] = f["name"]
    if issues:
        return _r("fail", f"{len(issues)} of {len(ctx.acroform_fields)} "
                           f"field(s) have tooltip problems.", issues)
    return _r("pass", f"All {len(ctx.acroform_fields)} form field(s) have "
                       f"tooltips set.")


def check_9_3(ctx):
    radios = [f for f in ctx.acroform_fields if f.get("radio")]
    if not radios:
        return _r("na", "No radio-button fields found in this document.")
    return _r("review", f"{len(radios)} radio-button field(s)/group(s) "
                         f"found. Manually confirm each visual group shares "
                         f"one field name and each option's choice value is "
                         f"correct.",
               [f"Radio field: {f['name']!r}" for f in radios])


def check_9_4(ctx):
    required = [f for f in ctx.acroform_fields if f.get("required")]
    if not ctx.acroform_fields:
        return _r("na", "No form fields found in this document.")
    if not required:
        return _r("review", "No fields are flagged Required in their "
                             "properties. If any field should be mandatory, "
                             "confirm the Required checkbox, visible label, "
                             "and tooltip all say so.")
    return _r("review", f"{len(required)} field(s) are marked Required. "
                         f"Manually confirm their visible labels and "
                         f"tooltips also include the word 'required'.",
               [f"Required field: {f['name']!r}" for f in required])


def check_9_5(ctx):
    validated = [f for f in ctx.acroform_fields if f.get("has_validation")]
    if not ctx.acroform_fields:
        return _r("na", "No form fields found in this document.")
    if not validated:
        return _r("na", "No fields have format/validation scripts attached.")
    return _r("review", f"{len(validated)} field(s) have format/validation "
                         f"actions attached. Manually confirm invalid input "
                         f"produces a clear, accessible error message.",
               [f"Field with validation: {f['name']!r}" for f in validated])


def check_9_6(ctx):
    fields_with_size = [f for f in ctx.acroform_fields
                         if f.get("width") and f.get("height")]
    if not fields_with_size:
        return _r("na", "No sized form field widgets found in this document.")
    THRESHOLD = 18.0  # ~24 CSS px at 96dpi converted to PDF pt (1pt=1/72in)
    small = [f for f in fields_with_size
             if f["width"] < THRESHOLD or f["height"] < THRESHOLD]
    if not small:
        return _r("pass", f"All {len(fields_with_size)} sized field(s) meet "
                           f"the minimum target size.")
    evidence = [f"Field {f['name']!r} on page {f.get('page')}: "
                f"{f['width']:.0f}x{f['height']:.0f}pt "
                f"(~{f['width']*96/72:.0f}x{f['height']*96/72:.0f}px)"
                for f in small]
    evidence.append("Note: fields with >=24px offset from neighboring "
                     "targets, or inline within a text sentence, are exempt "
                     "- confirm that manually before treating these as a "
                     "hard fail.")
    return _r("review", f"{len(small)} of {len(fields_with_size)} field(s) "
                         f"are under the 24px minimum target size.", evidence,
               [f.get("page") for f in small])


# -------------------------------------------------------------------- PDF-10
def check_10_1(ctx):
    return _manual("PDF-10-1")


def check_10_2(ctx):
    if not ctx.media_annots:
        return _r("na", "No embedded video/rich-media annotations detected.")
    return _r("manual", f"{len(ctx.media_annots)} media annotation(s) "
                         f"detected - manually verify captions.",
               [f"{m['subtype']} media on page {m['page']}" for m in ctx.media_annots],
               [m["page"] for m in ctx.media_annots])


def check_10_3(ctx):
    if not ctx.media_annots:
        return _r("na", "No embedded video/rich-media annotations detected.")
    return _r("manual", f"{len(ctx.media_annots)} media annotation(s) "
                         f"detected - manually verify audio description.",
               [f"{m['subtype']} media on page {m['page']}" for m in ctx.media_annots],
               [m["page"] for m in ctx.media_annots])


def check_10_4(ctx):
    if not ctx.media_annots:
        return _r("na", "No embedded audio/video annotations detected.")
    return _r("manual", f"{len(ctx.media_annots)} media annotation(s) "
                         f"detected - manually verify transcripts.",
               [f"{m['subtype']} media on page {m['page']}" for m in ctx.media_annots],
               [m["page"] for m in ctx.media_annots])


CHECK_FUNCS = {
    "PDF-1-1": check_1_1, "PDF-1-2": check_1_2,
    "PDF-2-1": check_2_1, "PDF-2-2": check_2_2, "PDF-2-3": check_2_3,
    "PDF-3-1": check_3_1, "PDF-3-2": check_3_2, "PDF-3-3": check_3_3,
    "PDF-3-4": check_3_4, "PDF-3-5": check_3_5, "PDF-3-6": check_3_6,
    "PDF-4-1": check_4_1, "PDF-4-2": check_4_2, "PDF-4-3": check_4_3,
    "PDF-4-4": check_4_4,
    "PDF-5-1": check_5_1, "PDF-5-2": check_5_2, "PDF-5-3": check_5_3,
    "PDF-5-4": check_5_4,
    "PDF-6-1": check_6_1, "PDF-6-2": check_6_2,
    "PDF-7-1": check_7_1, "PDF-7-2": check_7_2,
    "PDF-8-1": check_8_1,
    "PDF-9-1": check_9_1, "PDF-9-2": check_9_2, "PDF-9-3": check_9_3,
    "PDF-9-4": check_9_4, "PDF-9-5": check_9_5, "PDF-9-6": check_9_6,
    "PDF-10-1": check_10_1, "PDF-10-2": check_10_2, "PDF-10-3": check_10_3,
    "PDF-10-4": check_10_4,
}


def run_all_checks(ctx):
    """Runs every test case against ctx and returns {tc_id: result_dict}."""
    from .registry import all_ids_in_order
    results = {}
    for tc_id in all_ids_in_order():
        fn = CHECK_FUNCS.get(tc_id)
        if fn is None:
            continue
        try:
            results[tc_id] = fn(ctx)
        except Exception as e:
            results[tc_id] = _r("manual", f"Automated check crashed ({e}); "
                                           f"please verify manually.")

    # PDF-1-1 aggregate: fail if any other automated check failed.
    hard_fails = [tid for tid, res in results.items()
                  if tid != "PDF-1-1" and res["status"] == "fail"]
    if hard_fails:
        results["PDF-1-1"] = _r(
            "fail",
            f"{len(hard_fails)} test case(s) failed automated checks - see "
            f"below.", [f"{tid} failed" for tid in hard_fails])
    else:
        results["PDF-1-1"] = _r(
            "review",
            "No automated Fail results were found. Confirm the 'review' and "
            "'manual' items below, then run a second tool (PAC / Acrobat "
            "Pro) for full sign-off.")
    return results
