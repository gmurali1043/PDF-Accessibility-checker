"""
Test case registry.

This is the single source of truth mapping every test case (PDF-1-1 ... PDF-10-4)
to its requirement text, related WCAG 2.2 success criteria, related PDF/UA-1
clause, automation level, and step-by-step remediation guidance.

automation levels:
    "auto"   - fully determined by static analysis of the PDF's structure/metadata
    "semi"   - a strong automated signal is produced, but a human should confirm
               the finding (result is prefixed "Needs review")
    "manual" - cannot be reliably determined by static analysis at all; the
               checker always returns status "manual" with numbered steps
"""

TEST_CASES = {

    # ---------------------------------------------------------------- PDF-1
    "PDF-1-1": {
        "title": "Use an automated testing tool",
        "category": "General",
        "requirement": "When run against the page, an automated PDF accessibility "
                        "validation tool MUST NOT report any errors.",
        "wcag": [{"level": "-", "criterion": "4.1 Compatible",
                   "url": "https://www.w3.org/TR/WCAG22/#compatible"}],
        "pdfua": "6 Conformance requirements / 7.1 General",
        "automation": "auto",
        "remediation": [
            "This report itself is the automated check. Review every row marked "
            "Fail below and remediate it.",
            "Once all automated Fail rows are fixed, run this checker again to "
            "confirm a clean pass, then run PAC 2024 or Adobe Acrobat Pro's "
            "Accessibility Checker as a second opinion before sign-off.",
        ],
    },
    "PDF-1-2": {
        "title": "Document title",
        "category": "General",
        "requirement": "The document has a descriptive title, and the viewer is "
                        "configured to display that title (not the file name) in "
                        "the title bar.",
        "wcag": [{"level": "A", "criterion": "2.4.2 Page Titled",
                   "url": "https://www.w3.org/TR/WCAG22/#page-titled"}],
        "pdfua": "7.1 General",
        "automation": "auto",
        "remediation": [
            "In Acrobat Pro, open File > Properties > Description and enter a "
            "clear, descriptive Title (do not leave it blank or as the file name).",
            "On the same dialog, go to the Initial View tab and set "
            "'Show: Document Title' under Window Options so viewers display the "
            "title instead of the file name.",
            "Save the file and re-run this checker to confirm.",
        ],
    },

    # ---------------------------------------------------------------- PDF-2
    "PDF-2-1": {
        "title": "Color contrast ratio",
        "category": "Document colors",
        "requirement": "Text and images of text have a contrast ratio of at "
                        "least 4.5:1 (3:1 for text 18pt+ or 14pt+ bold).",
        "wcag": [{"level": "AA", "criterion": "1.4.3 Contrast (Minimum)",
                   "url": "https://www.w3.org/TR/WCAG22/#contrast-minimum"}],
        "pdfua": "7.1 General",
        "automation": "manual",
        "manual_steps": [
            "Open the PDF and identify each distinct text/background color "
            "combination used in the document (body text, headings, callout "
            "boxes, table text, footnotes, etc.).",
            "For each combination, sample the foreground text color and the "
            "background color (use the eyedropper/color picker in Acrobat, "
            "Photoshop, or your OS color picker).",
            "Enter both hex values into the WebAIM Contrast Checker "
            "(https://webaim.org/resources/contrastchecker/).",
            "Confirm the ratio is >= 4.5:1 for normal text, or >= 3:1 for text "
            "that is 18pt+ (24px) or 14pt+ bold (18.5px).",
            "Repeat for any images of text found in the document.",
        ],
    },
    "PDF-2-2": {
        "title": "Non-text contrast ratio",
        "category": "Document colors",
        "requirement": "Significant UI elements and graphics have a contrast "
                        "ratio of at least 3:1 against adjacent colors.",
        "wcag": [{"level": "AA", "criterion": "1.4.11 Non-text Contrast",
                   "url": "https://www.w3.org/TR/WCAG22/#non-text-contrast"}],
        "pdfua": "7.1 General",
        "automation": "manual",
        "manual_steps": [
            "Identify meaningful non-text elements: icons, form field borders, "
            "chart lines/bars, buttons, dividers that convey information.",
            "Sample the element's color and the color immediately adjacent to it "
            "(background or neighboring shape).",
            "Check the ratio with the WebAIM Contrast Checker "
            "(https://webaim.org/resources/contrastchecker/) - it accepts any "
            "two hex colors, not just text.",
            "Confirm each meaningful element reaches at least 3:1.",
        ],
    },
    "PDF-2-3": {
        "title": "Not only color",
        "category": "Document colors",
        "requirement": "Color is not the only visual means of conveying "
                        "information, indicating an action, or distinguishing "
                        "an element.",
        "wcag": [{"level": "A", "criterion": "1.4.1 Use of Color",
                   "url": "https://www.w3.org/TR/WCAG22/#use-of-color"}],
        "pdfua": "7.1 General",
        "automation": "manual",
        "manual_steps": [
            "Look for places color alone carries meaning: red/green status "
            "indicators, colored text used as the only cue for links or "
            "required fields, color-coded chart legends, colored table rows.",
            "Convert the page to grayscale (Acrobat: View > accessibility "
            "preview, or print to a grayscale PDF) and check whether the "
            "meaning is still conveyed without color.",
            "If meaning is lost, confirm the document also uses a second cue "
            "(icon, label, pattern, underline, text) alongside color.",
        ],
    },

    # ---------------------------------------------------------------- PDF-3
    "PDF-3-1": {
        "title": "Semantic tagging of text",
        "category": "Tags",
        "requirement": "The most semantically appropriate tag is used for each "
                        "element, in logical reading order; non-standard tags "
                        "are mapped via RoleMap; no real content is left as "
                        "an Artifact.",
        "wcag": [{"level": "-", "criterion": "4.1 Compatible",
                   "url": "https://www.w3.org/TR/WCAG22/#compatible"}],
        "pdfua": "7.1 General / 7.2 Text",
        "automation": "semi",
        "manual_steps": [
            "Open the Tags panel in Acrobat Pro (View > Show/Hide > Navigation "
            "Panes > Tags).",
            "Read through the tag tree alongside the visible page and confirm "
            "each tag matches the content's true semantic role (e.g. a "
            "sub-heading is an <H2>/<H3>, not a bold <P>).",
            "Confirm any custom/non-standard tags are mapped to the nearest "
            "standard tag in the RoleMap (Acrobat: right-click the tag root > "
            "Edit Role Map).",
            "Use 'Reading Order' tool or the Order panel to confirm elements "
            "are tagged in logical reading order.",
        ],
    },
    "PDF-3-2": {
        "title": "Table of contents",
        "category": "Tags",
        "requirement": "A TOC's bookmarks/entries link to the correct locations "
                        "and are tagged with <TOC>, <TOCI>, <Reference>, and "
                        "<Caption> (if present).",
        "wcag": [{"level": "AA", "criterion": "2.4.5 Multiple Ways",
                   "url": "https://www.w3.org/TR/WCAG22/#multiple-ways"}],
        "pdfua": "7.18.1 General",
        "automation": "auto",
        "remediation": [
            "In Acrobat Pro, select the TOC content and tag it as a <TOC> "
            "container in the Tags panel.",
            "Tag each entry as <TOCI>, nested directly under <TOC>.",
            "Inside each <TOCI>, make sure there is a <Reference> tag wrapping "
            "the link (Link-OBJR) that points to the target section.",
            "If the TOC has a heading/caption, tag it as <Caption> and place it "
            "as the first child of <TOC>.",
            "Test every entry by clicking it in Reading mode and confirming it "
            "jumps to the right page.",
        ],
    },
    "PDF-3-3": {
        "title": "Headings",
        "category": "Tags",
        "requirement": "Heading tags (H1-H6) are used, start at H1 if used, and "
                        "descend without skipping a level.",
        "wcag": [
            {"level": "AA", "criterion": "2.4.6 Headings and Labels",
             "url": "https://www.w3.org/TR/WCAG22/#headings-and-labels"},
            {"level": "A", "criterion": "1.3.2 Meaningful Sequence",
             "url": "https://www.w3.org/TR/WCAG22/#meaningful-sequence"},
        ],
        "pdfua": "7.4.2 Numbered Headings",
        "automation": "auto",
        "remediation": [
            "In the Tags panel, locate any heading-like text that is tagged as "
            "<P> and retag it as the correct <H1>-<H6> level.",
            "Walk the tag tree top to bottom and fix any level that skips a "
            "number on the way down (e.g. H1 straight to H3) - insert the "
            "missing intermediate level or adjust the level used.",
            "Note: going back up and starting a new branch at a higher level "
            "(e.g. H4 back to H2) is fine; only skipped *descending* levels are "
            "a failure.",
        ],
    },
    "PDF-3-4": {
        "title": "Lists",
        "category": "Tags",
        "requirement": "Lists use <L>, items use <LI> (with <Lbl>/<LBody> as "
                        "appropriate), and are only used for true list content.",
        "wcag": [{"level": "A", "criterion": "1.3.1 Info and Relationships",
                   "url": "https://www.w3.org/TR/WCAG22/#info-and-relationships"}],
        "pdfua": "7.6 Lists",
        "automation": "auto",
        "remediation": [
            "Select the list content in Acrobat and use Tags panel > right "
            "click > 'Create tag from selection' with List (<L>) as the type, "
            "or restructure manually in the Tags panel.",
            "Confirm each item is a direct child <LI> of the <L> tag.",
            "Confirm the bullet/number is tagged <Lbl> and the item text is "
            "tagged <LBody>, both nested inside each <LI>.",
            "If the list has a caption/title, tag it <Caption> as the first "
            "child of <L>.",
        ],
    },
    "PDF-3-5": {
        "title": "Footnotes and endnotes",
        "category": "Tags",
        "requirement": "Footnotes, endnotes, labels and references are tagged "
                        "<Note> with a unique ID, nested in a block tag, and "
                        "footnotes appear immediately after the referencing "
                        "content.",
        "wcag": [],
        "pdfua": "7.9 Notes and References",
        "automation": "semi",
        "manual_steps": [
            "Confirm in the Tags panel that footnote/endnote markers and their "
            "text are tagged <Note>.",
            "Open each <Note> tag's Properties and confirm it has a unique "
            "value in the ID field.",
            "For footnotes specifically, confirm the <Note> appears in the tag "
            "tree immediately after the block that references it (endnotes are "
            "exempt from this ordering requirement).",
        ],
    },
    "PDF-3-6": {
        "title": "Mathematical expressions",
        "category": "Tags",
        "requirement": "Math expressions are enclosed in a <Formula> tag with "
                        "an Alt attribute describing the equation in words.",
        "wcag": [],
        "pdfua": "7 Mathematical Expressions",
        "automation": "semi",
        "manual_steps": [
            "Scan the document visually for any mathematical equations or "
            "formulas (this cannot be reliably auto-detected from structure "
            "alone).",
            "For each one, confirm in the Tags panel it is wrapped in a "
            "<Formula> tag.",
            "Open the tag's Properties and confirm an Alt Text field is filled "
            "in with a plain-language description of the equation (e.g. "
            "'x squared plus 2x minus 3 equals 0').",
        ],
    },

    # ---------------------------------------------------------------- PDF-4
    "PDF-4-1": {
        "title": "Text alternatives",
        "category": "Graphics",
        "requirement": "Meaningful images have an accurate, descriptive /Alt "
                        "entry under 150 characters; complex images have a "
                        "nearby elaborated text description instead.",
        "wcag": [{"level": "A", "criterion": "1.1.1 Non-text Content",
                   "url": "https://www.w3.org/TR/WCAG22/#non-text-content"}],
        "pdfua": "7.3 Graphics",
        "automation": "auto",
        "remediation": [
            "In Acrobat Pro, open the Tags panel, select each <Figure> tag and "
            "open Properties (right-click > Properties, or Object > Alternate "
            "Text) to add a concise, descriptive Alt Text (under 150 "
            "characters).",
            "For complex images such as charts or infographics, instead add a "
            "visible text description near the image in the body content, and "
            "keep the Alt text short (e.g. 'Bar chart, described below').",
            "Never leave Alt text as a filename, 'image', or empty for a "
            "meaningful image.",
        ],
    },
    "PDF-4-2": {
        "title": "Decorative images",
        "category": "Graphics",
        "requirement": "Purely decorative images are marked as an Artifact so "
                        "assistive technology ignores them.",
        "wcag": [{"level": "A", "criterion": "1.1.1 Non-text Content",
                   "url": "https://www.w3.org/TR/WCAG22/#non-text-content"}],
        "pdfua": "7.3 Graphics",
        "automation": "semi",
        "manual_steps": [
            "For every image this report flags as 'tagged Figure with no Alt "
            "text', open it in Acrobat and judge whether it is purely "
            "decorative (adds no information) or meaningful (needs Alt text - "
            "see PDF-4-1 instead).",
            "If decorative: select the image in the Tags panel, right-click, "
            "and choose 'Change Tag to Artifact', or use Reading Order / "
            "Touch-Up Reading Order tool to mark it as background.",
        ],
    },
    "PDF-4-3": {
        "title": "Images with captions",
        "category": "Graphics",
        "requirement": "A caption accompanying a figure is tagged <Caption> as "
                        "a child of the enclosing <Figure> tag.",
        "wcag": [{"level": "A", "criterion": "1.1.1 Non-text Content",
                   "url": "https://www.w3.org/TR/WCAG22/#non-text-content"}],
        "pdfua": "7.3 Graphics",
        "automation": "auto",
        "remediation": [
            "In the Tags panel, confirm the image and its caption text sit "
            "inside the same parent <Figure> tag.",
            "Tag the caption text specifically as <Caption> (not <P>).",
            "If the caption currently sits outside the <Figure> tag, drag it "
            "in the Tags panel tree so it becomes a child of the <Figure>.",
        ],
    },
    "PDF-4-4": {
        "title": "No images of text",
        "category": "Graphics",
        "requirement": "Information is conveyed with real text, not images of "
                        "text (except logos, or text unavoidably embedded in a "
                        "graph/screenshot).",
        "wcag": [{"level": "A", "criterion": "1.1.1 Non-text Content",
                   "url": "https://www.w3.org/TR/WCAG22/#non-text-content"}],
        "pdfua": "7.3 Graphics",
        "automation": "manual",
        "manual_steps": [
            "Visually scan every page for text that is actually a picture of "
            "text (common in scanned pages, screenshots used as body content, "
            "or graphics with baked-in labels).",
            "Try selecting the text with the normal Select tool - if you can't "
            "select it character by character, it is likely an image.",
            "Confirm it isn't a logo, or text that is genuinely unavoidable "
            "inside a chart/screenshot (those are exempt).",
            "If it fails, replace the image with real, selectable text, or add "
            "an OCR text layer plus an elaborated description if it must stay "
            "an image.",
        ],
    },

    # ---------------------------------------------------------------- PDF-5
    "PDF-5-1": {
        "title": "Language of document",
        "category": "Text",
        "requirement": "The document has a language property that matches the "
                        "actual language of its content.",
        "wcag": [{"level": "A", "criterion": "3.1.1 Language of Page",
                   "url": "https://www.w3.org/TR/WCAG22/#language-of-page"}],
        "pdfua": "7.2 Text",
        "automation": "auto",
        "remediation": [
            "In Acrobat Pro, go to File > Properties > Advanced, and set the "
            "'Language' dropdown to match the document's actual language.",
            "Save the file and re-open it to confirm the setting persisted.",
        ],
    },
    "PDF-5-2": {
        "title": "Tab and reading order",
        "category": "Text",
        "requirement": "Content and interactive elements can be navigated in a "
                        "logical order consistent with the visual/reading "
                        "order.",
        "wcag": [{"level": "A", "criterion": "1.3.2 Meaningful Sequence",
                   "url": "https://www.w3.org/TR/WCAG22/#meaningful-sequence"}],
        "pdfua": "7.2 Text",
        "automation": "semi",
        "manual_steps": [
            "Use Acrobat's Reading Order tool (Tools > Accessibility > Reading "
            "Order) to visually confirm the numbered reading order regions "
            "match the intended sequence.",
            "Tab through every interactive element (links, form fields) on "
            "each page with the keyboard and confirm focus moves in a logical "
            "order that matches the visual layout.",
            "If the page's /Tabs entry is not already set to structure order "
            "(flagged below if so), set each page's tab order to 'Use "
            "Document Structure' in Page Properties.",
        ],
    },
    "PDF-5-3": {
        "title": "Headings and footers",
        "category": "Text",
        "requirement": "Running headers/footers are consistent across pages, "
                        "and redundant repeated content is marked as a "
                        "pagination Artifact.",
        "wcag": [{"level": "AA", "criterion": "3.2.3 Consistent Navigation",
                   "url": "https://www.w3.org/TR/WCAG22/#consistent-navigation"}],
        "pdfua": "7.8 Page Headers and Footers",
        "automation": "semi",
        "manual_steps": [
            "Compare the header/footer area across several pages and confirm "
            "wording, page numbers, and layout are applied consistently.",
            "Confirm repeated/redundant header and footer content (running "
            "titles, page numbers, decorative rules) is marked as an Artifact "
            "rather than real tagged content, so a screen reader does not read "
            "it out on every page.",
        ],
    },
    "PDF-5-4": {
        "title": "Language of parts",
        "category": "Text",
        "requirement": "A lang attribute is set on any word/phrase written in a "
                        "different language than the document's main "
                        "language.",
        "wcag": [{"level": "AA", "criterion": "3.1.2 Language of Parts",
                   "url": "https://www.w3.org/TR/WCAG22/#language-of-parts"}],
        "pdfua": "7.2 Text",
        "automation": "semi",
        "manual_steps": [
            "Find any words or passages written in a language other than the "
            "document's main language (e.g. a Latin phrase, a foreign-language "
            "quote).",
            "Select that text in the Tags panel content, open its Properties, "
            "and set the correct Language code for just that span.",
        ],
    },

    # ---------------------------------------------------------------- PDF-6
    "PDF-6-1": {
        "title": "Page numbers",
        "category": "Navigation",
        "requirement": "The page number shown in the PDF viewer's page "
                        "controls matches the printed page number on the page "
                        "itself.",
        "wcag": [{"level": "AA", "criterion": "2.4.5 Multiple Ways",
                   "url": "https://www.w3.org/TR/WCAG22/#multiple-ways"}],
        "pdfua": "7.17 Navigation",
        "automation": "semi",
        "manual_steps": [
            "Open the document and use Ctrl/Cmd+Shift+N (Go To Page) to jump "
            "to a page shown in the middle of the document.",
            "Compare the number you typed to the printed page number visible "
            "on that page (in its header/footer).",
            "Repeat for a page near the front matter (e.g. table of contents, "
            "preface) where printed numbering commonly diverges from PDF page "
            "count.",
            "If they don't match, set custom Page Labels in Acrobat "
            "(Page Thumbnails panel > Page Properties > Numbering) so the "
            "viewer's page count matches the printed numbers.",
        ],
    },
    "PDF-6-2": {
        "title": "Bookmarks",
        "category": "Navigation",
        "requirement": "Documents 21+ pages long provide bookmarks (an Outline "
                        "dictionary) so users can locate content.",
        "wcag": [{"level": "AA", "criterion": "2.4.5 Multiple Ways",
                   "url": "https://www.w3.org/TR/WCAG22/#multiple-ways"}],
        "pdfua": "7.17 Navigation",
        "automation": "auto",
        "remediation": [
            "In Acrobat Pro, the fastest path is Tags panel > Options menu > "
            "'Generate bookmarks from tags', using your Heading tags.",
            "Open the Bookmarks panel and confirm every important section has "
            "an entry, in the right order and nesting.",
            "Test a few bookmarks by clicking them to confirm they jump to the "
            "correct page.",
        ],
    },

    # ---------------------------------------------------------------- PDF-7
    "PDF-7-1": {
        "title": "Tables",
        "category": "Tables",
        "requirement": "Tables are tagged with Table/TR/TH/TD; header cells "
                        "have a Scope (and Span if applicable); captions are "
                        "tagged <Caption>.",
        "wcag": [{"level": "A", "criterion": "1.3.1 Info and Relationships",
                   "url": "https://www.w3.org/TR/WCAG22/#info-and-relationships"}],
        "pdfua": "7.5 Tables",
        "automation": "auto",
        "remediation": [
            "Select the table in Acrobat and use 'Create tag from selection' "
            "with Table, or fix the existing tag tree so it uses <Table>, "
            "<TR>, <TH> and <TD> tags matching the visual grid.",
            "Select each header cell's <TH> tag, open Properties > Table Cell "
            "Properties, and set Scope to Row, Column, or Both as appropriate "
            "(plus Span if a header covers multiple rows/columns).",
            "If the table has a caption/title, tag it <Caption> as the first "
            "or last child of <Table>.",
            "For complex tables where headers/IDs can't express the "
            "relationship through Scope alone, use the Headers/IDs attributes "
            "on each <TD> instead.",
        ],
    },
    "PDF-7-2": {
        "title": "No layout tables",
        "category": "Tables",
        "requirement": "Table tags are used only for genuine tabular data, "
                        "never purely to position content on the page.",
        "wcag": [{"level": "AA", "criterion": "2.4.5 Multiple Ways",
                   "url": "https://www.w3.org/TR/WCAG22/#multiple-ways"}],
        "pdfua": "7.17 Navigation",
        "automation": "manual",
        "manual_steps": [
            "For every Table tag this report finds, open it in the Tags panel "
            "and judge whether the content actually has row/column data "
            "relationships, or whether it's really just two columns of text "
            "or images positioned side by side.",
            "If it's layout-only, retag the content as plain paragraphs "
            "(<P>) instead of a Table.",
        ],
    },

    # ---------------------------------------------------------------- PDF-8
    "PDF-8-1": {
        "title": "Links and link text",
        "category": "Annotations",
        "requirement": "Links are tagged <Link> with a nested Link-OBJR "
                        "reference, and the link text clearly states the "
                        "link's purpose.",
        "wcag": [{"level": "A", "criterion": "2.4.4 Link Purpose (In Context)",
                   "url": "https://www.w3.org/TR/WCAG22/#link-purpose-in-context"}],
        "pdfua": "7.18.5 Links",
        "automation": "auto",
        "remediation": [
            "In the Tags panel, confirm every hyperlink is wrapped in a "
            "<Link> tag that contains an OBJR object reference to the actual "
            "link annotation.",
            "Where link text just says 'click here' or shows a bare URL, "
            "rewrite the visible text (or add Alt text on the Link tag) so it "
            "describes the destination, e.g. 'Download the 2026 accessibility "
            "report (PDF)'.",
            "Tab to each link with the keyboard and press Enter to confirm it "
            "activates and goes to the correct destination.",
        ],
    },

    # ---------------------------------------------------------------- PDF-9
    "PDF-9-1": {
        "title": "Form controls",
        "category": "Forms",
        "requirement": "Each form Widget annotation is nested inside a <Form> "
                        "tag, positioned after its visible label at the same "
                        "level.",
        "wcag": [],
        "pdfua": "7.18.4 Forms",
        "automation": "auto",
        "remediation": [
            "In the Tags panel, confirm every form field's Widget annotation "
            "sits inside a <Form> tag (it should show as 'Field name-OBJR').",
            "Move each <Form> tag so it appears immediately after, and at the "
            "same tree level as, the tag containing that field's visible text "
            "label.",
        ],
    },
    "PDF-9-2": {
        "title": "Form tooltips",
        "category": "Forms",
        "requirement": "Every form field exposes an accurate, descriptive, and "
                        "unique name/role/state/value via its tooltip.",
        "wcag": [{"level": "A", "criterion": "4.1.2 Name, Role, Value",
                   "url": "https://www.w3.org/TR/WCAG22/#name-role-value"}],
        "pdfua": "7.18.4 Forms",
        "automation": "auto",
        "remediation": [
            "Open Tools > Prepare Form, right-click each field, choose "
            "Properties, and fill in the 'Tooltip' field on the General tab "
            "with a clear, unique description of that field's purpose.",
            "Avoid generic tooltips like 'Text Field' - describe what should "
            "be entered, e.g. 'Enter your billing ZIP code'.",
        ],
    },
    "PDF-9-3": {
        "title": "Form radio buttons",
        "category": "Forms",
        "requirement": "Visually grouped radio buttons share the same field "
                        "Name so they operate as one group, with correct "
                        "export/choice values per option.",
        "wcag": [{"level": "A", "criterion": "4.1.2 Name, Role, Value",
                   "url": "https://www.w3.org/TR/WCAG22/#name-role-value"}],
        "pdfua": "7.18.4 Forms",
        "automation": "semi",
        "manual_steps": [
            "Open Prepare Form, select each radio button in a visual group, "
            "and confirm they all share the same field Name so only one can "
            "be selected at a time.",
            "For each button in the group, check its 'Button Value' under "
            "Options is the correct, distinct choice it represents.",
        ],
    },
    "PDF-9-4": {
        "title": "Required form controls",
        "category": "Forms",
        "requirement": "Required fields say 'required' in both their visible "
                        "label and tooltip, and have the Required checkbox "
                        "checked in field properties.",
        "wcag": [
            {"level": "A", "criterion": "3.3.1 Error Identification",
             "url": "https://www.w3.org/TR/WCAG22/#error-identification"},
            {"level": "A", "criterion": "3.3.2 Labels or Instructions",
             "url": "https://www.w3.org/TR/WCAG22/#labels-or-instructions"},
        ],
        "pdfua": "7.18.4 Forms",
        "automation": "semi",
        "manual_steps": [
            "For each field this report flags as marked Required in its "
            "properties, confirm the visible on-page label also includes the "
            "word 'required' (e.g. an asterisk alone is not sufficient).",
            "Confirm the field's tooltip text (Prepare Form > field Properties "
            "> General) also includes the word 'required'.",
            "For fields that look required on the page but are NOT flagged "
            "Required below, open Properties > General and check the "
            "'Required field' checkbox.",
        ],
    },
    "PDF-9-5": {
        "title": "Form input validation",
        "category": "Forms",
        "requirement": "Users are notified, in an accessible way, when input "
                        "doesn't match a field's required format (e.g. a date "
                        "field).",
        "wcag": [
            {"level": "A", "criterion": "3.3.1 Error Identification",
             "url": "https://www.w3.org/TR/WCAG22/#error-identification"},
            {"level": "A", "criterion": "3.3.2 Labels or Instructions",
             "url": "https://www.w3.org/TR/WCAG22/#labels-or-instructions"},
        ],
        "pdfua": "7.18.4 Forms",
        "automation": "semi",
        "manual_steps": [
            "For each field flagged below with a format/validation script, "
            "enter deliberately invalid data and confirm a clear, accurate "
            "error message appears.",
            "Confirm the error message is exposed in a way a screen reader "
            "user would also receive it (a plain JS alert() is announced by "
            "most readers, but confirm with NVDA/VoiceOver if possible).",
            "Confirm the field's tooltip or visible label already states the "
            "expected format (e.g. 'MM/DD/YYYY') so users can avoid the error.",
        ],
    },
    "PDF-9-6": {
        "title": "Target size",
        "category": "Forms",
        "requirement": "Actionable components are at least 24x24 CSS px, "
                        "unless they have 24px of offset from the next target "
                        "or sit inline within a sentence.",
        "wcag": [{"level": "AA", "criterion": "2.5.8 Target Size (Minimum)",
                   "url": "https://www.w3.org/TR/WCAG22/#target-size-minimum"}],
        "pdfua": "7.18.4 Forms",
        "automation": "auto",
        "remediation": [
            "Open Prepare Form, select the flagged field, and resize it (drag "
            "a corner handle, or set exact Width/Height in Properties) so "
            "both dimensions are at least 24px (~0.25in / 0.33cm).",
            "If the control must stay small, instead move it so its center is "
            "at least 24px away from the next actionable control.",
            "Fields that are links/buttons inline within a sentence of body "
            "text are exempt - leave those as-is.",
        ],
    },

    # --------------------------------------------------------------- PDF-10
    "PDF-10-1": {
        "title": "No blinking or flashing content",
        "category": "Media",
        "requirement": "Content that blinks or flashes (JavaScript effects or "
                        "embedded video) must never be used.",
        "wcag": [{"level": "A", "criterion": "2.3.1 Three Flashes or Below Threshold",
                   "url": "https://www.w3.org/TR/WCAG22/#three-flashes-or-below-threshold"}],
        "pdfua": "7.1 General",
        "automation": "manual",
        "manual_steps": [
            "Open the document in Adobe Acrobat Pro and page through it "
            "visually, watching for any flickering, blinking, or flashing "
            "effect.",
            "If any embedded video is present, play it fully and confirm it "
            "contains no flash sequences (more than 3 flashes per second).",
            "If any page-level JavaScript animations are present, trigger them "
            "and confirm they don't flash.",
        ],
    },
    "PDF-10-2": {
        "title": "Captions for video",
        "category": "Media",
        "requirement": "All video content (live and prerecorded) includes "
                        "accurate captions.",
        "wcag": [{"level": "A", "criterion": "1.2.2 Captions (Prerecorded)",
                   "url": "https://www.w3.org/TR/WCAG22/#captions-prerecorded"}],
        "pdfua": "7.18.6 Media",
        "automation": "manual",
        "manual_steps": [
            "Play every embedded video in the document (this report will list "
            "any video/rich-media annotations it detected below).",
            "Turn on captions if there is a toggle, or confirm open captions "
            "are burned into the video.",
            "Confirm the captions are accurate and synchronized with the "
            "audio.",
        ],
    },
    "PDF-10-3": {
        "title": "Audio description for video",
        "category": "Media",
        "requirement": "If a video shows information visually that its audio "
                        "track doesn't describe, an Audio Description track "
                        "must fully explain it.",
        "wcag": [{"level": "AA", "criterion": "1.2.5 Audio Description (Prerecorded)",
                   "url": "https://www.w3.org/TR/WCAG22/#audio-description-prerecorded"}],
        "pdfua": "7.18.6 Media",
        "automation": "manual",
        "manual_steps": [
            "Watch each embedded video with your eyes closed, listening only.",
            "Note any moments where something important happens visually but "
            "is never mentioned by the audio/dialogue.",
            "If such moments exist, confirm an Audio Description track (or "
            "extended/described version) is provided that explains them; if "
            "not, this fails.",
        ],
    },
    "PDF-10-4": {
        "title": "Transcripts for audio-only/video-only",
        "category": "Media",
        "requirement": "Audio-only and video-only media provide a transcript "
                        "with the same information as the media.",
        "wcag": [{"level": "A", "criterion": "1.2.1 Audio-only and Video-only (Prerecorded)",
                   "url": "https://www.w3.org/TR/WCAG22/#audio-only-and-video-only-prerecorded"}],
        "pdfua": "7.18.6 Media",
        "automation": "manual",
        "manual_steps": [
            "Identify any audio-only (e.g. embedded podcast/sound clip) or "
            "silent video-only content in the document.",
            "Confirm a text transcript is provided nearby (or linked) that "
            "conveys the same information as the media.",
        ],
    },
}

CATEGORY_ORDER = [
    "General", "Document colors", "Tags", "Graphics", "Text",
    "Navigation", "Tables", "Annotations", "Forms", "Media",
]


def get_test_case(tc_id):
    return TEST_CASES[tc_id]


def all_ids_in_order():
    ids = list(TEST_CASES.keys())
    ids.sort(key=lambda i: (CATEGORY_ORDER.index(TEST_CASES[i]["category"]),
                             [int(x) for x in i.split("-")[1:]]))
    return ids
