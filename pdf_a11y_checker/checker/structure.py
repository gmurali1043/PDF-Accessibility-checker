"""
Loads a PDF with pikepdf and pdfplumber, and builds a simplified, easy-to-walk
in-memory representation of its structure tree, catalog info, forms,
annotations, and outlines. All the check functions in checks.py operate on the
`PDFContext` this module produces, so the low-level PDF-object handling lives
in exactly one place.
"""
import pikepdf
from pikepdf import Name, Dictionary, Array

try:
    import pdfplumber
except Exception:  # pragma: no cover
    pdfplumber = None


class TagNode:
    __slots__ = ("tag", "attrs", "children", "alt", "actual_text", "lang", "obj", "parent", "page")

    def __init__(self, tag, attrs=None, obj=None, page=None):
        self.tag = tag
        self.attrs = attrs or {}
        self.children = []
        self.alt = attrs.get("Alt") if attrs else None
        self.actual_text = attrs.get("ActualText") if attrs else None
        self.lang = attrs.get("Lang") if attrs else None
        self.obj = obj
        self.parent = None
        self.page = page  # 1-based page number this element appears on, if known

    def add_child(self, child):
        child.parent = self
        self.children.append(child)

    def walk(self):
        yield self
        for c in self.children:
            yield from c.walk()

    def find_all(self, tag_name):
        return [n for n in self.walk() if n.tag == tag_name]

    def ancestor_tags(self):
        node = self.parent
        out = []
        while node is not None:
            out.append(node.tag)
            node = node.parent
        return out

    def has_ancestor(self, tag_name):
        return tag_name in self.ancestor_tags()

    def __repr__(self):
        return f"<{self.tag} children={len(self.children)}>"


def _safe_str(x):
    try:
        return str(x)
    except Exception:
        return None


def _pdf_str(val):
    """Best-effort decode of a pikepdf String/Name object to python str."""
    if val is None:
        return None
    try:
        return str(val)
    except Exception:
        return None


class PDFContext:
    def __init__(self, path):
        self.path = path
        self.errors = []
        self.pdf = None
        self.page_count = 0
        self.title = None
        self.lang = None
        self.marked = False
        self.tagged_pdf = False
        self.struct_tree_root = None
        self.tag_root = None  # TagNode tree
        self.outlines_present = False
        self.outline_count = 0
        self.page_labels_present = False
        self.acroform_fields = []  # list of dict
        self.link_annots_per_page = []  # count
        self.media_annots = []  # list of dict (subtype, page)
        self.display_doc_title = False
        self.all_struct_types = set()
        self.role_map = {}

        self._load()

    # ------------------------------------------------------------------
    def _load(self):
        try:
            self.pdf = pikepdf.open(self.path)
        except Exception as e:
            self.errors.append(f"Could not open PDF: {e}")
            return

        self.page_count = len(self.pdf.pages)
        root = self.pdf.Root

        # ---- page objid -> 1-based page number map (used to resolve /Pg refs
        #      on structure elements into human-readable failure locations) ----
        self._page_objid_map = {}
        try:
            for pageno, page in enumerate(self.pdf.pages, start=1):
                pid = self._objid(page)
                if pid is not None:
                    self._page_objid_map[pid] = pageno
        except Exception:
            pass

        # ---- title / metadata ----
        try:
            info = self.pdf.docinfo
            if info is not None and "/Title" in info:
                self.title = _pdf_str(info["/Title"]).strip() or None
        except Exception:
            pass
        if not self.title:
            try:
                with self.pdf.open_metadata() as meta:
                    t = meta.get("dc:title")
                    if t:
                        self.title = str(t)
            except Exception:
                pass

        # ---- ViewerPreferences DisplayDocTitle ----
        try:
            vp = root.get("/ViewerPreferences")
            if vp is not None and bool(vp.get("/DisplayDocTitle", False)):
                self.display_doc_title = True
        except Exception:
            pass

        # ---- language ----
        try:
            if "/Lang" in root:
                self.lang = _pdf_str(root["/Lang"])
        except Exception:
            pass

        # ---- MarkInfo / tagged ----
        try:
            mi = root.get("/MarkInfo")
            if mi is not None:
                self.marked = bool(mi.get("/Marked", False))
        except Exception:
            pass

        # ---- structure tree ----
        try:
            st_root = root.get("/StructTreeRoot")
            if st_root is not None:
                self.tagged_pdf = True
                self.struct_tree_root = st_root
                rm = st_root.get("/RoleMap")
                if rm is not None:
                    for k in rm.keys():
                        try:
                            self.role_map[str(k)] = str(rm[k])
                        except Exception:
                            pass
                self.tag_root = self._build_tag_tree(st_root, depth=0, inherited_page=None)
        except Exception as e:
            self.errors.append(f"Error parsing structure tree: {e}")

        # ---- outlines / bookmarks ----
        try:
            outlines = root.get("/Outlines")
            if outlines is not None:
                self.outlines_present = True
                self.outline_count = self._count_outline(outlines)
        except Exception:
            pass

        # ---- page labels ----
        try:
            if "/PageLabels" in root:
                self.page_labels_present = True
        except Exception:
            pass

        # ---- AcroForm fields ----
        try:
            acro = root.get("/AcroForm")
            if acro is not None and "/Fields" in acro:
                for f in acro["/Fields"]:
                    self._collect_fields(f, prefix="")
        except Exception as e:
            self.errors.append(f"Error parsing AcroForm: {e}")

        # ---- per-page annotations: links, media, widgets, target size ----
        self.page_tabs = []
        try:
            for pageno, page in enumerate(self.pdf.pages, start=1):
                try:
                    tabs_val = str(page.get("/Tabs")) if "/Tabs" in page else None
                except Exception:
                    tabs_val = None
                self.page_tabs.append(tabs_val)
                annots = page.get("/Annots")
                link_count = 0
                if annots is not None:
                    for a in annots:
                        try:
                            subtype = str(a.get("/Subtype", ""))
                        except Exception:
                            subtype = ""
                        if subtype == "/Link":
                            link_count += 1
                        if subtype in ("/Screen", "/RichMedia", "/Movie"):
                            self.media_annots.append({
                                "page": pageno, "subtype": subtype.strip("/"),
                            })
                        if subtype == "/Widget":
                            rect = a.get("/Rect")
                            w = h = None
                            if rect is not None and len(rect) == 4:
                                try:
                                    x0, y0, x1, y1 = [float(v) for v in rect]
                                    w, h = abs(x1 - x0), abs(y1 - y0)
                                except Exception:
                                    pass
                            aid = self._objid(a)
                            for fld in self.acroform_fields:
                                if aid is not None and aid in fld.get("_objids", []):
                                    fld["width"] = w
                                    fld["height"] = h
                                    fld["page"] = pageno
                self.link_annots_per_page.append(link_count)
        except Exception as e:
            self.errors.append(f"Error parsing annotations: {e}")

        # ---- text via pdfplumber (used for heuristics only) ----
        self.plumber_pages = None
        if pdfplumber is not None:
            try:
                self.plumber = pdfplumber.open(self.path)
                self.plumber_pages = self.plumber.pages
            except Exception:
                self.plumber_pages = None

    # ------------------------------------------------------------------
    def _objid(self, obj):
        try:
            return int(obj.objgen[0])
        except Exception:
            return None

    def _collect_fields(self, f, prefix="", inherited_ft=None, depth=0):
        """Recursively flattens the /AcroForm field tree into
        self.acroform_fields, one entry per terminal (leaf) field."""
        if depth > 30:
            return
        try:
            name = _pdf_str(f.get("/T")) if "/T" in f else None
        except Exception:
            name = None
        full_name = f"{prefix}.{name}" if prefix and name else (name or prefix or "(unnamed)")

        try:
            ftype = str(f.get("/FT")) if "/FT" in f else inherited_ft
        except Exception:
            ftype = inherited_ft

        kids = f.get("/Kids") if "/Kids" in f else None
        has_widget_kids = False
        if kids is not None:
            for k in kids:
                if "/FT" not in k and "/Subtype" in k and str(k.get("/Subtype")) == "/Widget":
                    has_widget_kids = True
                    break

        if kids is not None and not has_widget_kids:
            # kids are child fields (radio group members, sub-fields)
            for k in kids:
                self._collect_fields(k, prefix=full_name, inherited_ft=ftype, depth=depth + 1)
            return

        # this is a terminal field (possibly with its own widget kids)
        try:
            tu = _pdf_str(f.get("/TU")) if "/TU" in f else None
        except Exception:
            tu = None
        try:
            ff = int(f.get("/Ff", 0))
        except Exception:
            ff = 0
        required = bool(ff & (1 << 1))  # bit 2 (value 2) = Required
        radio = bool(ff & (1 << 15))    # bit 16 (value 32768) = Radio (Btn fields)

        has_validation = False
        try:
            aa = f.get("/AA")
            if aa is not None and (("/F" in aa) or ("/V" in aa) or ("/K" in aa)):
                has_validation = True
        except Exception:
            pass

        objid = self._objid(f)
        widget_objids = [objid] if objid is not None else []
        if kids is not None:
            for k in kids:
                wid = self._objid(k)
                if wid is not None:
                    widget_objids.append(wid)

        info = {
            "name": full_name,
            "type": (ftype or "").strip("/") if ftype else "",
            "tooltip": tu,
            "required": required,
            "radio": radio,
            "has_validation": has_validation,
            "_objids": widget_objids,
            "width": None, "height": None, "page": None,
        }
        self.acroform_fields.append(info)

    def _inherited_ft(self, f):
        parent = f.get("/Parent")
        if parent is not None and "/FT" in parent:
            return str(parent["/FT"])
        return None

    def _count_outline(self, outlines):
        count = 0
        try:
            node = outlines.get("/First")
            while node is not None:
                count += 1
                if "/First" in node:
                    count += self._count_outline(node)
                node = node.get("/Next")
        except Exception:
            pass
        return count

    # ------------------------------------------------------------------
    def _build_tag_tree(self, obj, depth, seen=None, inherited_page=None):
        if seen is None:
            seen = set()
        if depth > 60:
            return TagNode("MaxDepthExceeded")
        try:
            objid = self._objid(obj) if hasattr(obj, "objgen") else None
        except Exception:
            objid = None
        if objid is not None:
            if objid in seen:
                return TagNode("Circular")
            seen = seen | {objid}

        # StructTreeRoot itself
        if "/S" not in obj and "/K" in obj and "/Type" in obj:
            tag = "StructTreeRoot"
        else:
            tag = None
            try:
                if "/S" in obj:
                    tag = str(obj["/S"]).lstrip("/")
            except Exception:
                tag = None
            tag = tag or "Unknown"

        attrs = {}
        try:
            if "/Alt" in obj:
                attrs["Alt"] = _pdf_str(obj["/Alt"])
        except Exception:
            pass
        try:
            if "/ActualText" in obj:
                attrs["ActualText"] = _pdf_str(obj["/ActualText"])
        except Exception:
            pass
        try:
            if "/Lang" in obj:
                attrs["Lang"] = _pdf_str(obj["/Lang"])
        except Exception:
            pass
        try:
            if "/T" in obj:
                attrs["T"] = _pdf_str(obj["/T"])
        except Exception:
            pass
        try:
            if "/ID" in obj:
                attrs["ID"] = _pdf_str(obj["/ID"])
        except Exception:
            pass

        page = inherited_page
        try:
            pg = obj.get("/Pg")
            if pg is not None:
                pgid = self._objid(pg)
                if pgid is not None and pgid in self._page_objid_map:
                    page = self._page_objid_map[pgid]
        except Exception:
            pass

        node = TagNode(tag, attrs, obj=obj, page=page)
        self.all_struct_types.add(tag)

        # Table cell scope / attributes live in /A (Attributes) dict(s)
        try:
            a = obj.get("/A")
            scope = None
            span = None
            headers = None
            if a is not None:
                a_list = a if isinstance(a, pikepdf.Array) else [a]
                for entry in a_list:
                    try:
                        if "/Scope" in entry:
                            scope = str(entry["/Scope"]).lstrip("/")
                        if "/RowSpan" in entry or "/ColSpan" in entry:
                            span = True
                        if "/Headers" in entry:
                            headers = True
                    except Exception:
                        continue
            if scope:
                node.attrs["Scope"] = scope
            if span:
                node.attrs["Span"] = True
            if headers:
                node.attrs["Headers"] = True
        except Exception:
            pass

        try:
            k = obj.get("/K")
        except Exception:
            k = None

        if k is None:
            return node

        kids = k if isinstance(k, pikepdf.Array) else [k]
        for kid in kids:
            try:
                if isinstance(kid, (int, float)):
                    continue  # marked-content id, not a sub-tag
                if isinstance(kid, pikepdf.Dictionary) or isinstance(kid, pikepdf.Object):
                    if "/Type" in kid and str(kid.get("/Type", "")) == "/OBJR":
                        objr_node = TagNode("OBJR")
                        try:
                            ref = kid.get("/Obj")
                            if ref is not None:
                                objr_node.attrs["RefObjId"] = self._objid(ref)
                        except Exception:
                            pass
                        node.add_child(objr_node)
                        continue
                    if "/S" in kid or "/K" in kid:
                        node.add_child(self._build_tag_tree(
                            kid, depth + 1, seen, inherited_page=page))
            except Exception:
                continue
        return node

    def close(self):
        try:
            if self.pdf is not None:
                self.pdf.close()
        except Exception:
            pass
        try:
            if getattr(self, "plumber", None) is not None:
                self.plumber.close()
        except Exception:
            pass


def load_context(path):
    return PDFContext(path)
