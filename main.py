import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from datetime import datetime, timedelta
from tkcalendar import DateEntry
from fpdf import FPDF
import os


RECOMMENDATIONS = {
    ("Solid", "Single", "<6 mm (<100 mm\u00b3)", "Low-risk"): "No routine follow-up required.",
    ("Solid", "Single", "<6 mm (<100 mm\u00b3)", "High-risk"):
        "Optional CT at 12 months (particularly with suspicious nodule morphology and/or upper lobe location).",
    ("Solid", "Multiple", "<6 mm (<100 mm\u00b3)", "Low-risk"): "No routine follow-up required.",
    ("Solid", "Multiple", "<6 mm (<100 mm\u00b3)", "High-risk"): "Optional CT at 12 months.",
    ("Solid", "Single", "6-8 mm (100-250 mm\u00b3)", "Low-risk"):
        "CT at 6-12 months, then consider CT at 18-24 months.",
    ("Solid", "Single", "6-8 mm (100-250 mm\u00b3)", "High-risk"):
        "CT at 6-12 months, then CT at 18-24 months.",
    ("Solid", "Multiple", "6-8 mm (100-250 mm\u00b3)", "Low-risk"):
        "CT at 3-6 months, then consider CT at 18-24 months.",
    ("Solid", "Multiple", "6-8 mm (100-250 mm\u00b3)", "High-risk"):
        "CT at 3-6 months, then at 18-24 months.",
    ("Solid", "Single", ">8 mm (>250 mm\u00b3)", "Low-risk"):
        "Consider CT at 3 months, PET-CT, or tissue sampling.",
    ("Solid", "Single", ">8 mm (>250 mm\u00b3)", "High-risk"):
        "Consider CT at 3 months, PET-CT, or tissue sampling.",
    ("Solid", "Multiple", ">8 mm (>250 mm\u00b3)", "Low-risk"):
        "CT at 3-6 months, then consider CT at 18-24 months.",
    ("Solid", "Multiple", ">8 mm (>250 mm\u00b3)", "High-risk"):
        "CT at 3-6 months, then at 18-24 months.",
    ("Subsolid", "Single", "Ground glass - <6 mm (<100 mm\u00b3)", None):
        "No routine follow-up required.",
    ("Subsolid", "Single", "Ground glass - \u22656 mm (\u2265100 mm\u00b3)", None):
        "CT at 6-12 months, then if persistent, CT every 2 years until 5 years.",
    ("Subsolid", "Single", "Part-solid - <6 mm (<100 mm\u00b3)", None):
        "No routine follow-up required.",
    ("Subsolid", "Single", "Part-solid - \u22656 mm (\u2265100 mm\u00b3)", None):
        "CT at 3-6 months, then if persistent and solid component remains <6 mm, annual CT until 5 years.",
    ("Subsolid", "Multiple", "<6 mm (<100 mm\u00b3)", None):
        "CT at 3-6 months, then if stable consider CT at 2 and 4 years in high-risk patients.",
    ("Subsolid", "Multiple", "\u22656 mm (\u2265100 mm\u00b3)", None):
        "CT at 3-6 months, then subsequent management based on the most suspicious nodule(s).",
}

FOLLOW_UP_MONTHS = {
    ("Solid", "Single", "<6 mm (<100 mm\u00b3)", "Low-risk"): [],
    ("Solid", "Single", "<6 mm (<100 mm\u00b3)", "High-risk"): [12],
    ("Solid", "Multiple", "<6 mm (<100 mm\u00b3)", "Low-risk"): [],
    ("Solid", "Multiple", "<6 mm (<100 mm\u00b3)", "High-risk"): [12],
    ("Solid", "Single", "6-8 mm (100-250 mm\u00b3)", "Low-risk"): [6, 12, 18, 24],
    ("Solid", "Single", "6-8 mm (100-250 mm\u00b3)", "High-risk"): [6, 12, 18, 24],
    ("Solid", "Multiple", "6-8 mm (100-250 mm\u00b3)", "Low-risk"): [3, 6, 18, 24],
    ("Solid", "Multiple", "6-8 mm (100-250 mm\u00b3)", "High-risk"): [3, 6, 18, 24],
    ("Solid", "Single", ">8 mm (>250 mm\u00b3)", "Low-risk"): [3],
    ("Solid", "Single", ">8 mm (>250 mm\u00b3)", "High-risk"): [3],
    ("Solid", "Multiple", ">8 mm (>250 mm\u00b3)", "Low-risk"): [3, 6, 18, 24],
    ("Solid", "Multiple", ">8 mm (>250 mm\u00b3)", "High-risk"): [3, 6, 18, 24],
    ("Subsolid", "Single", "Ground glass - <6 mm (<100 mm\u00b3)", None): [],
    ("Subsolid", "Single", "Ground glass - \u22656 mm (\u2265100 mm\u00b3)", None): [6, 12, 24, 36, 48, 60],
    ("Subsolid", "Single", "Part-solid - <6 mm (<100 mm\u00b3)", None): [],
    ("Subsolid", "Single", "Part-solid - \u22656 mm (\u2265100 mm\u00b3)", None): [3, 6, 12, 24, 36, 48, 60],
    ("Subsolid", "Multiple", "<6 mm (<100 mm\u00b3)", None): [3, 6, 24, 48],
    ("Subsolid", "Multiple", "\u22656 mm (\u2265100 mm\u00b3)", None): [3, 6],
}

SOLID_SIZES = ["<6 mm (<100 mm\u00b3)", "6-8 mm (100-250 mm\u00b3)", ">8 mm (>250 mm\u00b3)"]
SUBSOLID_SINGLE_SIZES = [
    "Ground glass - <6 mm (<100 mm\u00b3)", "Ground glass - \u22656 mm (\u2265100 mm\u00b3)",
    "Part-solid - <6 mm (<100 mm\u00b3)", "Part-solid - \u22656 mm (\u2265100 mm\u00b3)",
]
SUBSOLID_MULTI_SIZES = ["<6 mm (<100 mm\u00b3)", "\u22656 mm (\u2265100 mm\u00b3)"]

BG = "#eaf0f7"
CARD_BG = "#ffffff"
ACCENT = "#2b5797"
ACCENT_LIGHT = "#d6e4f5"
DATE_FMT = "%d.%m.%y"


def sanitize(text):
    """Replace special unicode chars with ASCII equivalents for PDF."""
    return (text
            .replace("\u00b3", "3")
            .replace("\u2265", ">=")
            .replace("\u2192", "->"))


class NoduleApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Pulmonary Nodule Follow-Up Guidelines")
        self.root.configure(bg=BG)
        self.root.minsize(760, 820)

        style = ttk.Style()
        style.theme_use("clam")

        style.configure("TFrame", background=BG)
        style.configure("Card.TFrame", background=CARD_BG)
        style.configure("TLabel", background=BG, font=("Segoe UI", 10))
        style.configure("Card.TLabel", background=CARD_BG, font=("Segoe UI", 10))
        style.configure("Header.TLabel", background=ACCENT, foreground="white",
                        font=("Segoe UI", 16, "bold"), padding=12)
        style.configure("SubHeader.TLabel", background=ACCENT, foreground="#ccdcef",
                        font=("Segoe UI", 9, "italic"), padding=(12, 0, 12, 10))
        style.configure("Section.TLabel", background=CARD_BG,
                        font=("Segoe UI", 11, "bold"), foreground=ACCENT)
        style.configure("Desc.TLabel", background=CARD_BG,
                        font=("Segoe UI", 8), foreground="#5a6a7a")
        style.configure("TRadiobutton", background=CARD_BG, font=("Segoe UI", 10))
        style.configure("TLabelframe", background=CARD_BG, foreground=ACCENT,
                        font=("Segoe UI", 10, "bold"))
        style.configure("TLabelframe.Label", background=BG, foreground=ACCENT,
                        font=("Segoe UI", 10, "bold"))
        style.configure("Accent.TButton", font=("Segoe UI", 11, "bold"), padding=10,
                        background=ACCENT, foreground="white")
        style.map("Accent.TButton",
                  background=[("active", "#1d3f6f"), ("pressed", "#162f54")])
        style.configure("TEntry", padding=4)

        # --- Header banner ---
        header_bar = ttk.Frame(root, style="TFrame")
        header_bar.pack(fill="x")
        header_inner = tk.Frame(header_bar, bg=ACCENT)
        header_inner.pack(fill="x")
        title_lbl = tk.Label(header_inner, text="Pulmonary Nodule Follow-Up Guidelines",
                             bg=ACCENT, fg="white", font=("Segoe UI", 16, "bold"),
                             anchor="w", padx=20)
        title_lbl.pack(fill="x", pady=(12, 0))
        sub_lbl = tk.Label(header_inner, text="Based on Fleischner Society Recommendations",
                           bg=ACCENT, fg="#b0c8e8", font=("Segoe UI", 9, "italic"),
                           anchor="w", padx=20)
        sub_lbl.pack(fill="x", pady=(0, 10))

        # --- Scrollable content ---
        canvas = tk.Canvas(root, bg=BG, highlightthickness=0)
        scrollbar = ttk.Scrollbar(root, orient="vertical", command=canvas.yview)
        self.scroll_frame = ttk.Frame(canvas, padding=20)
        self.scroll_frame.bind("<Configure>",
                               lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        self._canvas_window = canvas.create_window((0, 0), window=self.scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        # Keep scroll_frame width in sync with canvas width
        def _on_canvas_resize(event):
            canvas.itemconfig(self._canvas_window, width=event.width)
        canvas.bind("<Configure>", _on_canvas_resize)

        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)

        main = self.scroll_frame

        # --- Patient Info Card ---
        info_card = self._card(main, "Patient Information")

        row1 = ttk.Frame(info_card, style="Card.TFrame")
        row1.pack(fill="x", pady=(0, 6))
        ttk.Label(row1, text="Patient Name:", style="Card.TLabel").pack(side="left")
        self.patient_name = ttk.Entry(row1, width=30, font=("Segoe UI", 10))
        self.patient_name.pack(side="left", padx=(10, 0))

        row2 = ttk.Frame(info_card, style="Card.TFrame")
        row2.pack(fill="x")
        ttk.Label(row2, text="Imaging Date:", style="Card.TLabel").pack(side="left")
        self.imaging_date = DateEntry(row2, width=12, date_pattern="dd.MM.yy",
                                      font=("Segoe UI", 10))
        self.imaging_date.pack(side="left", padx=(10, 0))

        # --- Nodule Classification Card ---
        class_card = self._card(main, "Nodule Classification")

        self.nodule_type = tk.StringVar()
        self.count = tk.StringVar()

        ttk.Label(class_card, text="Type", style="Section.TLabel").pack(anchor="w")
        type_row = ttk.Frame(class_card, style="Card.TFrame")
        type_row.pack(fill="x", pady=(2, 10), padx=10)
        for val in ["Solid", "Subsolid"]:
            ttk.Radiobutton(type_row, text=val, variable=self.nodule_type, value=val,
                            command=self.on_type_change).pack(side="left", padx=(0, 20))

        ttk.Label(class_card, text="Count", style="Section.TLabel").pack(anchor="w")
        count_row = ttk.Frame(class_card, style="Card.TFrame")
        count_row.pack(fill="x", pady=(2, 4), padx=10)
        for val in ["Single", "Multiple"]:
            ttk.Radiobutton(count_row, text=val, variable=self.count, value=val,
                            command=self.on_type_change).pack(side="left", padx=(0, 20))

        # --- Size Card (custom, with info button) ---
        self.size_wrapper = ttk.Frame(main)
        self.size_wrapper.pack(fill="x", pady=(0, 12))
        size_card_frame = tk.Frame(self.size_wrapper, bg=CARD_BG, bd=0,
                                   highlightthickness=1, highlightbackground="#d0d8e4")
        size_card_frame.pack(fill="x", ipady=12, ipadx=14)

        size_title_row = tk.Frame(size_card_frame, bg=CARD_BG)
        size_title_row.pack(fill="x", padx=14, pady=(10, 6))
        ttk.Label(size_title_row, text="Nodule Size",
                  style="Section.TLabel").pack(side="left")
        info_btn = tk.Button(size_title_row, text="i", font=("Segoe UI", 9, "bold"),
                             bg=ACCENT, fg="white", bd=0, padx=6, pady=0,
                             activebackground="#1d3f6f", activeforeground="white",
                             cursor="hand2", command=self.show_measurement_info)
        info_btn.pack(side="left", padx=(8, 0))

        self.size_card = tk.Frame(size_card_frame, bg=CARD_BG)
        self.size_card.pack(fill="x", padx=14, pady=(0, 6))
        self.size = tk.StringVar()
        self.size_inner = ttk.Frame(self.size_card, style="Card.TFrame")
        self.size_inner.pack(fill="x", padx=10)
        self.size_buttons = []

        # --- Risk Card ---
        self.risk_card_wrapper = ttk.Frame(main)
        self.risk_card_wrapper.pack(fill="x", pady=(0, 12))
        self.risk_card_inner = tk.Frame(self.risk_card_wrapper, bg=CARD_BG, bd=0,
                                         highlightthickness=1, highlightbackground="#d0d8e4")
        self.risk_card_inner.pack(fill="x", ipady=12, ipadx=14)

        ttk.Label(self.risk_card_inner, text="Risk Level",
                  style="Section.TLabel").pack(anchor="w", padx=14, pady=(10, 4))

        self.risk = tk.StringVar()
        risk_row = tk.Frame(self.risk_card_inner, bg=CARD_BG)
        risk_row.pack(fill="x", padx=24, pady=(0, 6))
        for val in ["Low-risk", "High-risk"]:
            ttk.Radiobutton(risk_row, text=val, variable=self.risk, value=val).pack(
                side="left", padx=(0, 20))

        sep = ttk.Separator(self.risk_card_inner, orient="horizontal")
        sep.pack(fill="x", padx=14, pady=(2, 6))

        desc_frame = tk.Frame(self.risk_card_inner, bg=CARD_BG)
        desc_frame.pack(fill="x", padx=14, pady=(0, 4))

        high_lbl = tk.Label(desc_frame, bg=CARD_BG, fg="#5a6a7a", font=("Segoe UI", 8),
                            justify="left", anchor="w", wraplength=680,
                            text="High risk: Current or former smoker, family history of lung cancer, "
                                 "personal cancer history, exposure to asbestos/radon, age >50, "
                                 "COPD, pulmonary fibrosis")
        high_lbl.pack(fill="x", pady=(0, 2))

        low_lbl = tk.Label(desc_frame, bg=CARD_BG, fg="#5a6a7a", font=("Segoe UI", 8),
                           justify="left", anchor="w", wraplength=680,
                           text="Low risk: Minimal or no smoking history, age <40, "
                                "no other risk factors")
        low_lbl.pack(fill="x", pady=(0, 2))

        note_lbl = tk.Label(desc_frame, bg=CARD_BG, fg="#7a8a9a", font=("Segoe UI", 8, "italic"),
                            justify="left", anchor="w", wraplength=680,
                            text="Note: High-risk threshold is generally considered "
                                 ">5% estimated cancer risk")
        note_lbl.pack(fill="x")

        # --- Result display (non-scrollable label) ---
        result_wrapper = ttk.Frame(main)
        result_wrapper.pack(fill="x", pady=(0, 12))
        result_card = tk.Frame(result_wrapper, bg=CARD_BG, bd=0,
                               highlightthickness=1, highlightbackground="#d0d8e4")
        result_card.pack(fill="x", ipady=12, ipadx=14)
        ttk.Label(result_card, text="Recommendation",
                  style="Section.TLabel").pack(anchor="w", padx=14, pady=(10, 6))
        self.result_label = tk.Label(result_card, bg=CARD_BG, fg="#1a2a3a",
                                     font=("Segoe UI", 10), justify="left", anchor="nw",
                                     wraplength=660)
        self.result_label.pack(fill="x", padx=14, pady=(0, 10))

        # --- Create Report Button ---
        btn_frame = ttk.Frame(main)
        btn_frame.pack(fill="x", pady=(0, 12))
        ttk.Button(btn_frame, text="Create Report (PDF)", style="Accent.TButton",
                   command=self.create_report).pack(fill="x")

        self.on_type_change()

        # Auto-update: recalculate on any change
        for var in (self.nodule_type, self.count, self.size, self.risk):
            var.trace_add("write", lambda *_: self.auto_generate())
        self.patient_name.bind("<KeyRelease>", lambda _: self.auto_generate())
        self.imaging_date.bind("<<DateEntrySelected>>", lambda _: self.auto_generate())

    def show_measurement_info(self):
        popup = tk.Toplevel(self.root)
        popup.title("Nodule Measurement Guidelines")
        popup.configure(bg=BG)
        popup.geometry("620x700")
        popup.resizable(True, True)

        # Header
        hdr = tk.Frame(popup, bg=ACCENT)
        hdr.pack(fill="x")
        tk.Label(hdr, text="Nodule Measurement Guidelines", bg=ACCENT, fg="white",
                 font=("Segoe UI", 14, "bold"), anchor="w", padx=16).pack(
                     fill="x", pady=(10, 8))

        # Scrollable body
        canvas = tk.Canvas(popup, bg=BG, highlightthickness=0)
        sb = ttk.Scrollbar(popup, orient="vertical", command=canvas.yview)
        body = tk.Frame(canvas, bg=BG)
        body.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=body, anchor="nw")
        canvas.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        def _mw(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        canvas.bind_all("<MouseWheel>", _mw)

        pad = {"padx": 16, "pady": (0, 2)}

        def section(title):
            tk.Label(body, text=title, bg=BG, fg=ACCENT,
                     font=("Segoe UI", 11, "bold"), anchor="w").pack(
                         fill="x", padx=16, pady=(14, 4))
            ttk.Separator(body, orient="horizontal").pack(fill="x", padx=16, pady=(0, 6))

        def bullet(text):
            f = tk.Frame(body, bg=BG)
            f.pack(fill="x", **pad)
            tk.Label(f, text="\u2022", bg=BG, fg="#444", font=("Segoe UI", 10),
                     anchor="n").pack(side="left", padx=(0, 6))
            tk.Label(f, text=text, bg=BG, fg="#333", font=("Segoe UI", 9),
                     wraplength=540, justify="left", anchor="nw").pack(
                         side="left", fill="x", expand=True)

        # --- Image Production & Viewing ---
        section("Image Production and Viewing")
        bullet("Images should be acquired in full inspiration.")
        bullet("Nodules should usually be measured in the axial (transverse) plane, "
               "although the coronal or sagittal plane may be used if the greatest "
               "dimensions lie in those planes.")
        bullet("Nodules should be measured in lung windows, although soft tissue windows "
               "can help evaluate changes in nodule density over time.")
        bullet("Small nodules (<10 mm) should be viewed and measured on images "
               "reconstructed in thin slices (\u22641.5 mm, ideally 1 mm) using a "
               "high-spatial frequency (sharp) algorithm, in order to avoid partial "
               "volume averaging, and identify fat or calcified components.")
        bullet("If automated or semi-automated volumetry is performed it should be done "
               "using the same software for the initial and follow-up studies.")

        # --- Nodule Description - By Size ---
        section("Nodule Description and Assessment - By Size")
        bullet("Small nodules 3-10 mm should be expressed, for risk estimation purposes, "
               "as the average of the short-axis and long-axis diameters (measured on the "
               "same slice).")
        bullet("Small nodules <3 mm should not be measured and should be described as "
               "micronodules.")
        bullet("Larger nodules >10 mm and masses, for descriptive purposes, should be "
               "described in both short- and long-axis measurements.")
        bullet("Measurements should be rounded to the nearest whole millimeter.")

        # --- Part-Solid Nodules ---
        section("Part-Solid Nodules")
        bullet("Solid components >3 mm should have the maximal diameter reported.")
        bullet("Part-solid nodules cannot be discerned as such when <6 mm.")

        # --- General Assessment ---
        section("General Assessment")
        bullet("When multiple nodules are present, only the largest or morphologically "
               "most suspicious need to be measured and have their location(s) reported.")
        bullet("The dominant nodule refers to the morphologically most suspicious lesion, "
               "which is not necessarily the largest.")
        bullet("An increase in nodule dimension by \u22652 mm is required to identify "
               "significant growth.")
        bullet("Volume doubling time can be used as an ancillary feature to characterize "
               "nodule behavior.")
        bullet("Perifissural nodules that demonstrate characteristic morphology (triangular "
               "or oval shape in the axial plane, and a flat or lentiform morphology in the "
               "sagittal and coronal planes) do not necessarily require follow-up even if "
               ">6 mm.")

        # Close button
        tk.Frame(body, bg=BG, height=10).pack()
        close_btn = tk.Button(body, text="Close", font=("Segoe UI", 10, "bold"),
                              bg=ACCENT, fg="white", bd=0, padx=20, pady=6,
                              activebackground="#1d3f6f", activeforeground="white",
                              cursor="hand2", command=popup.destroy)
        close_btn.pack(pady=(6, 16))

        popup.transient(self.root)
        popup.grab_set()

    def auto_generate(self):
        name = self.patient_name.get().strip()
        ntype = self.nodule_type.get()
        count = self.count.get()
        size = self.size.get()
        risk = self.risk.get() if ntype == "Solid" else None

        if not ntype or not count or not size:
            self.result_label.config(text="")
            return
        if ntype == "Solid" and not risk:
            self.result_label.config(text="")
            return
        if not name:
            self.result_label.config(text="")
            return
        self.generate()

    def _card(self, parent, title):
        wrapper = ttk.Frame(parent)
        wrapper.pack(fill="x", pady=(0, 12))
        card = tk.Frame(wrapper, bg=CARD_BG, bd=0,
                        highlightthickness=1, highlightbackground="#d0d8e4")
        card.pack(fill="x", ipady=12, ipadx=14)
        ttk.Label(card, text=title, style="Section.TLabel").pack(
            anchor="w", padx=14, pady=(10, 6))
        content = tk.Frame(card, bg=CARD_BG)
        content.pack(fill="x", padx=14, pady=(0, 6))
        return content

    def on_type_change(self):
        for btn in self.size_buttons:
            btn.destroy()
        self.size_buttons.clear()
        self.size.set("")

        ntype = self.nodule_type.get()
        count = self.count.get()

        if ntype == "Solid":
            sizes = SOLID_SIZES
        elif ntype == "Subsolid" and count == "Single":
            sizes = SUBSOLID_SINGLE_SIZES
        elif ntype == "Subsolid" and count == "Multiple":
            sizes = SUBSOLID_MULTI_SIZES
        else:
            sizes = []

        for val in sizes:
            btn = ttk.Radiobutton(self.size_inner, text=val, variable=self.size, value=val)
            btn.pack(anchor="w", pady=2)
            self.size_buttons.append(btn)

        if ntype == "Subsolid":
            self.risk_card_wrapper.pack_forget()
        else:
            self.risk_card_wrapper.pack(fill="x", pady=(0, 12),
                                         after=self.size_wrapper)

        self.auto_generate()

    def _get_report_data(self):
        """Gather all current form data and compute recommendation. Returns dict or None."""
        name = self.patient_name.get().strip()
        img_date_str = self.imaging_date.get()
        ntype = self.nodule_type.get()
        count = self.count.get()
        size = self.size.get()
        risk = self.risk.get() if ntype == "Solid" else None

        if not name or not ntype or not count or not size:
            return None
        if ntype == "Solid" and not risk:
            return None

        key = (ntype, count, size, risk)
        rec = RECOMMENDATIONS.get(key)
        months = FOLLOW_UP_MONTHS.get(key, [])
        if rec is None:
            return None

        try:
            img_date = datetime.strptime(img_date_str, "%d.%m.%y")
        except ValueError:
            img_date = datetime.today()

        follow_ups = []
        for m in months:
            fu_date = img_date + timedelta(days=30 * m)
            follow_ups.append((m, fu_date.strftime(DATE_FMT)))

        return {
            "name": name,
            "imaging_date": img_date.strftime(DATE_FMT),
            "nodule_type": ntype,
            "count": count,
            "size": size,
            "risk": risk,
            "recommendation": rec,
            "is_multiple": count == "Multiple",
            "follow_ups": follow_ups,
        }

    def generate(self):
        data = self._get_report_data()
        if data is None:
            self.result_label.config(text="")
            return

        lines = []
        lines.append(f"PATIENT SUMMARY")
        lines.append(f"  Name:             {data['name']}")
        lines.append(f"  Imaging Date:   {data['imaging_date']}")
        lines.append(f"  Nodule:            {data['nodule_type']}  |  {data['count']}  |  {data['size']}")
        if data["risk"]:
            lines.append(f"  Risk:               {data['risk']}")

        lines.append(f"\nRECOMMENDATION")
        lines.append(f"  {data['recommendation']}")

        if data["is_multiple"]:
            lines.append(f"\n  Note: When multiple nodules are present, the most suspicious")
            lines.append(f"  nodule should guide further individualized management.")

        lines.append(f"\nFOLLOW-UP SCHEDULE")
        if data["follow_ups"]:
            for m, d in data["follow_ups"]:
                lines.append(f"    {m:>2} months  \u2192  {d}")
        else:
            lines.append("  No scheduled follow-up dates.")

        self.result_label.config(text="\n".join(lines))

    def create_report(self):
        data = self._get_report_data()
        if data is None:
            messagebox.showwarning("Incomplete", "Please fill in all fields before creating a report.")
            return

        default_name = f"Nodule_Report_{data['name'].replace(' ', '_')}_{datetime.now().strftime('%d%m%y')}.pdf"
        file_path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf")],
            initialfile=default_name,
            title="Save Report As",
        )
        if not file_path:
            return

        pdf = FPDF()
        pdf.add_page()
        pw = pdf.w - pdf.l_margin - pdf.r_margin  # printable width

        # Title bar
        pdf.set_fill_color(43, 87, 151)
        pdf.set_text_color(255, 255, 255)
        pdf.set_font("Helvetica", "B", 18)
        pdf.cell(pw, 14, "Pulmonary Nodule Follow-Up Report", align="C", fill=True, new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "I", 9)
        pdf.cell(pw, 8, "Based on Fleischner Society Recommendations", align="C", fill=True, new_x="LMARGIN", new_y="NEXT")
        pdf.ln(4)

        # Report date
        pdf.set_text_color(100, 100, 100)
        pdf.set_font("Helvetica", "I", 9)
        pdf.cell(pw, 6, f"Report generated: {datetime.now().strftime(DATE_FMT)}", align="R", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(4)

        # Patient summary section
        pdf.set_fill_color(214, 228, 245)
        pdf.set_text_color(43, 87, 151)
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(pw, 9, "  Patient Summary", fill=True, new_x="LMARGIN", new_y="NEXT")
        pdf.ln(3)

        pdf.set_text_color(30, 30, 30)
        pdf.set_font("Helvetica", "", 11)
        fields = [
            ("Patient Name", data["name"]),
            ("Imaging Date", data["imaging_date"]),
            ("Nodule Type", data["nodule_type"]),
            ("Count", data["count"]),
            ("Size", sanitize(data["size"])),
        ]
        if data["risk"]:
            fields.append(("Risk Level", data["risk"]))

        for label, value in fields:
            pdf.set_font("Helvetica", "B", 10)
            pdf.cell(45, 7, f"  {label}:", new_x="END")
            pdf.set_font("Helvetica", "", 10)
            pdf.cell(0, 7, f"  {value}", new_x="LMARGIN", new_y="NEXT")

        pdf.ln(6)

        # Recommendation section
        pdf.set_fill_color(214, 228, 245)
        pdf.set_text_color(43, 87, 151)
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(pw, 9, "  Recommendation", fill=True, new_x="LMARGIN", new_y="NEXT")
        pdf.ln(3)

        pdf.set_text_color(30, 30, 30)
        pdf.set_font("Helvetica", "", 11)
        pdf.multi_cell(pw, 7, f"  {sanitize(data['recommendation'])}")

        if data["is_multiple"]:
            pdf.ln(2)
            pdf.set_text_color(184, 92, 0)
            pdf.set_font("Helvetica", "I", 9)
            pdf.multi_cell(pw, 6,
                "  Note: When multiple nodules are present, the most suspicious nodule "
                "should guide further individualized management.")

        pdf.ln(6)

        # Follow-up schedule section
        pdf.set_fill_color(214, 228, 245)
        pdf.set_text_color(43, 87, 151)
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(pw, 9, "  Follow-Up Schedule", fill=True, new_x="LMARGIN", new_y="NEXT")
        pdf.ln(3)

        pdf.set_text_color(30, 30, 30)
        if data["follow_ups"]:
            # Table header
            pdf.set_font("Helvetica", "B", 10)
            pdf.set_fill_color(240, 244, 248)
            pdf.cell(pw / 2, 8, "    Timeframe", fill=True, new_x="END")
            pdf.cell(pw / 2, 8, "  Suggested Date", fill=True, new_x="LMARGIN", new_y="NEXT")

            pdf.set_font("Helvetica", "", 10)
            for i, (m, d) in enumerate(data["follow_ups"]):
                if i % 2 == 0:
                    pdf.set_fill_color(250, 250, 252)
                else:
                    pdf.set_fill_color(240, 244, 248)
                pdf.cell(pw / 2, 7, f"    {m} months", fill=True, new_x="END")
                pdf.cell(pw / 2, 7, f"  {d}", fill=True, new_x="LMARGIN", new_y="NEXT")
        else:
            pdf.set_font("Helvetica", "", 11)
            pdf.cell(pw, 7, "  No scheduled follow-up dates.", new_x="LMARGIN", new_y="NEXT")

        # Footer line
        pdf.ln(12)
        pdf.set_draw_color(200, 200, 200)
        pdf.line(pdf.l_margin, pdf.get_y(), pdf.l_margin + pw, pdf.get_y())
        pdf.ln(3)
        pdf.set_text_color(150, 150, 150)
        pdf.set_font("Helvetica", "I", 8)
        pdf.cell(pw, 5, "This report is for clinical reference only. "
                 "Clinical judgement should always be applied.", align="C")

        pdf.output(file_path)
        messagebox.showinfo("Report Saved", f"Report saved to:\n{file_path}")
        os.startfile(file_path)


if __name__ == "__main__":
    root = tk.Tk()
    NoduleApp(root)
    root.mainloop()
