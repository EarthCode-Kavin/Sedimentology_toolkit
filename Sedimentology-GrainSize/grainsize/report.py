"""
grainsize.report
================
Professional HTML and PDF report generation.

HTML uses a self-contained template (images embedded as base64 so the file
is portable). PDF uses reportlab. Both include: cover page, sample info,
grain-size statistics, every analysis result, all plots, per-sample
interpretation, a final dataset interpretation, references, and the
processing date + software version.
"""
from __future__ import annotations
import os
import base64
import datetime
import html as _html
import pandas as pd

REFERENCES = [
    "Folk, R. L. (1954) The distinction between grain size and mineral composition "
    "in sedimentary-rock nomenclature. Journal of Geology 62, 344-359.",
    "Folk, R. L. & Ward, W. C. (1957) Brazos River bar: a study in the significance "
    "of grain size parameters. Journal of Sedimentary Petrology 27, 3-26.",
    "Shepard, F. P. (1954) Nomenclature based on sand-silt-clay ratios. "
    "Journal of Sedimentary Petrology 24, 151-158.",
    "Passega, R. (1964) Grain size representation by CM patterns as a geological tool. "
    "Journal of Sedimentary Petrology 34, 830-847.",
    "Visher, G. S. (1969) Grain size distributions and depositional processes. "
    "Journal of Sedimentary Petrology 39, 1074-1106.",
    "Blott, S. J. & Pye, K. (2001) GRADISTAT: a grain size distribution and statistics "
    "package for the analysis of unconsolidated sediments. "
    "Earth Surface Processes and Landforms 26, 1237-1248.",
]


# ======================================================================
# HTML
# ======================================================================
def _b64(path):
    if not path or not os.path.exists(path):
        return None
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("ascii")


def _img_tag(path, width="100%"):
    b = _b64(path)
    if not b:
        return "<p><em>[figure unavailable]</em></p>"
    return f'<img src="data:image/png;base64,{b}" style="width:{width};max-width:900px;border:1px solid #ddd;border-radius:4px;margin:8px 0;">'


def write_html(path, dataset, results, summary_df, dataset_figs, meta):
    esc = _html.escape
    parts = []
    parts.append(f"""<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Grain-Size Report - {esc(dataset)}</title>
<style>
 body{{font-family:'Segoe UI',Roboto,Helvetica,Arial,sans-serif;margin:0;color:#1a1a1a;line-height:1.55;background:#f7f7f8;}}
 .wrap{{max-width:980px;margin:0 auto;padding:0 22px 60px;}}
 .cover{{background:linear-gradient(135deg,#1F4E79,#2E75B6);color:#fff;padding:60px 40px;border-radius:0 0 14px 14px;margin-bottom:30px;}}
 .cover h1{{margin:0 0 8px;font-size:2.1em;}}
 .cover p{{margin:2px 0;opacity:.92;}}
 h2{{color:#1F4E79;border-bottom:2px solid #2E75B6;padding-bottom:5px;margin-top:38px;}}
 h3{{color:#2E75B6;margin-top:26px;}}
 table{{border-collapse:collapse;width:100%;font-size:.9em;margin:12px 0;background:#fff;}}
 th,td{{border:1px solid #dfe3e8;padding:6px 9px;text-align:left;}}
 th{{background:#eef4fb;color:#1F4E79;}}
 tr:nth-child(even) td{{background:#fafbfc;}}
 .card{{background:#fff;border:1px solid #e4e7eb;border-radius:8px;padding:18px 22px;margin:16px 0;box-shadow:0 1px 3px rgba(0,0,0,.05);}}
 .interp{{background:#FFF9E6;border-left:4px solid #E0A800;padding:12px 16px;border-radius:4px;margin:12px 0;}}
 .fractions{{display:flex;gap:8px;flex-wrap:wrap;margin:10px 0;}}
 .frac{{padding:4px 10px;border-radius:14px;font-size:.85em;}}
 .refs{{font-size:.85em;color:#444;}}
 .foot{{margin-top:40px;font-size:.8em;color:#777;border-top:1px solid #ddd;padding-top:14px;}}
 code{{background:#eef;padding:1px 5px;border-radius:3px;}}
</style></head><body>
<div class="cover">
 <h1>Grain-Size Analysis Report</h1>
 <p style="font-size:1.3em;font-weight:600;">Dataset: {esc(dataset)}</p>
 <p>{meta['n_samples']} samples &bull; 7 analyses per sample</p>
 <p>Generated {esc(meta['date'])} &bull; Sedimentology-GrainSize v{esc(meta['version'])}</p>
</div>
<div class="wrap">
""")

    # Overview / summary table
    parts.append('<h2>1. Dataset summary</h2>')
    parts.append('<div class="card">')
    parts.append(summary_df.to_html(index=False, border=0))
    parts.append('</div>')

    # Dataset-level figures
    parts.append('<h2>2. Dataset-level diagrams</h2>')
    for kind, title in [("passega_cm", "Passega C-M diagram"),
                        ("folk_ternary", "Folk ternary classification"),
                        ("shepard_ternary", "Shepard ternary classification")]:
        parts.append(f'<h3>{esc(title)}</h3>')
        parts.append(_img_tag(dataset_figs.get(kind)))

    # Per-sample sections
    parts.append('<h2>3. Per-sample analyses</h2>')
    for sid, res in results.items():
        st, h, cm = res["stats"], res["histogram"], res["passega_cm"]
        fr = res["fractions"]
        parts.append(f'<div class="card"><h3>{esc(str(sid))}</h3>')
        # fraction chips
        chips = "".join(
            f'<span class="frac" style="background:{col};">{name}: {fr[name]:.1f}%</span>'
            for name, col in [("gravel", "#E8D3B8"), ("sand", "#FBE9AE"),
                              ("silt", "#CFE8C4"), ("clay", "#C4D9EE")])
        parts.append(f'<div class="fractions">{chips}</div>')
        # stats table
        stat_tbl = pd.DataFrame([{
            "Mean (phi)": f"{st['mean_phi']:.2f}", "Mean (um)": f"{st['mean_um']:.0f}",
            "Class": st["mean_class"], "Sorting": st["sorting"],
            "Skewness": st["skewness"], "Kurtosis": st["kurtosis"],
            "Modality": res["frequency_curve"]["modality"],
            "Folk": res["folk"]["folk_class"], "Shepard": res["shepard"]["shepard_class"],
            "C/M": f"{cm['C_over_M']:.1f}", "Transport": cm["mechanism"],
        }]).T.reset_index()
        stat_tbl.columns = ["Property", "Value"]
        parts.append(stat_tbl.to_html(index=False, border=0))
        # figures 2x2
        for kind in ("histogram", "frequency_curve", "cumulative", "probability"):
            parts.append(_img_tag(res["_figures"].get(kind), width="49%"))
        # interpretation
        parts.append(f'<div class="interp"><strong>Interpretation:</strong> '
                     f'{esc(res["interpretation"])}</div>')
        parts.append('</div>')

    # Final interpretation
    parts.append('<h2>4. Final sedimentological interpretation</h2>')
    parts.append(f'<div class="card">{_dataset_interpretation(results, summary_df)}</div>')

    # References
    parts.append('<h2>5. References</h2><div class="card refs"><ol>')
    for r in REFERENCES:
        parts.append(f'<li>{esc(r)}</li>')
    parts.append('</ol></div>')

    parts.append(f'<div class="foot">Processing date: {esc(meta["date"])} &bull; '
                 f'Software: Sedimentology-GrainSize v{esc(meta["version"])} &bull; '
                 f'Runtime: {meta.get("elapsed_s","?")} s</div>')
    parts.append('</div></body></html>')

    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(parts))
    return path


def _dataset_interpretation(results, summary_df):
    n = len(summary_df)
    sortings = summary_df["sorting"].value_counts()
    folk = summary_df["folk_class"].value_counts()
    envs = summary_df["visher_environment"].value_counts()
    dominant_sort = sortings.index[0] if len(sortings) else "-"
    dominant_folk = folk.index[0] if len(folk) else "-"
    lines = [
        f"The dataset comprises {n} samples. The most common textural class is "
        f"<strong>{_html.escape(str(dominant_folk))}</strong> (Folk 1954), and the "
        f"prevailing sorting character is <strong>{_html.escape(str(dominant_sort))}</strong>. ",
        f"Mean grain size ranges from {summary_df['mean_phi'].min():.2f} to "
        f"{summary_df['mean_phi'].max():.2f} phi "
        f"({summary_df['mean_um'].min():.0f}-{summary_df['mean_um'].max():.0f} um). ",
        "Transport-population analysis (Visher 1969) indicates the following "
        "depositional signatures across the dataset: "
        + "; ".join(f"{_html.escape(str(k))} (n={v})" for k, v in envs.items()) + ". ",
        "These textural and hydrodynamic characteristics together constrain the "
        "likely depositional environment(s); they should be integrated with field "
        "observations, sedimentary structures, and stratigraphic context before "
        "final facies assignment.",
    ]
    return "".join(lines)


# ======================================================================
# PDF (reportlab)
# ======================================================================
def write_pdf(path, dataset, results, summary_df, dataset_figs, meta):
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import cm as CM
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table,
                                    TableStyle, Image, PageBreak)
    from reportlab.lib.enums import TA_CENTER

    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle("CoverTitle", parent=styles["Title"], fontSize=26,
                              textColor=colors.HexColor("#1F4E79"), spaceAfter=10))
    styles.add(ParagraphStyle("CoverSub", parent=styles["Normal"], fontSize=13,
                              alignment=TA_CENTER, textColor=colors.HexColor("#2E75B6")))
    styles.add(ParagraphStyle("H2c", parent=styles["Heading2"],
                              textColor=colors.HexColor("#1F4E79")))
    styles.add(ParagraphStyle("H3c", parent=styles["Heading3"],
                              textColor=colors.HexColor("#2E75B6")))
    styles.add(ParagraphStyle("Interp", parent=styles["Normal"], fontSize=9,
                              backColor=colors.HexColor("#FFF9E6"),
                              borderColor=colors.HexColor("#E0A800"), borderWidth=0.5,
                              borderPadding=6, spaceBefore=6, spaceAfter=6))
    small = ParagraphStyle("small", parent=styles["Normal"], fontSize=8)

    doc = SimpleDocTemplate(path, pagesize=A4, topMargin=1.6 * CM,
                            bottomMargin=1.6 * CM, leftMargin=1.7 * CM, rightMargin=1.7 * CM)
    story = []

    # --- Cover ---
    story += [Spacer(1, 4 * CM),
              Paragraph("Grain-Size Analysis Report", styles["CoverTitle"]),
              Spacer(1, 0.4 * CM),
              Paragraph(f"Dataset: <b>{dataset}</b>", styles["CoverSub"]),
              Spacer(1, 0.2 * CM),
              Paragraph(f"{meta['n_samples']} samples &bull; 7 analyses per sample",
                        styles["CoverSub"]),
              Spacer(1, 2 * CM),
              Paragraph(f"Generated {meta['date']}", styles["CoverSub"]),
              Paragraph(f"Sedimentology-GrainSize v{meta['version']}", styles["CoverSub"]),
              PageBreak()]

    # --- Summary table ---
    story.append(Paragraph("1. Dataset summary", styles["H2c"]))
    cols = ["sample", "mean_phi", "sorting", "folk_class", "shepard_class",
            "C_over_M", "transport"]
    tbl_data = [cols] + summary_df[cols].astype(str).values.tolist()
    t = Table(tbl_data, repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1F4E79")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTSIZE", (0, 0), (-1, -1), 7),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#cccccc")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f3f6fa")]),
    ]))
    story += [t, Spacer(1, 0.4 * CM)]

    # --- dataset figures ---
    story.append(Paragraph("2. Dataset-level diagrams", styles["H2c"]))
    for kind, title in [("passega_cm", "Passega C-M diagram"),
                        ("folk_ternary", "Folk ternary"),
                        ("shepard_ternary", "Shepard ternary")]:
        p = dataset_figs.get(kind)
        if p and os.path.exists(p):
            story.append(Paragraph(title, styles["H3c"]))
            story.append(_fit_image(Image, p, 13 * CM))
            story.append(Spacer(1, 0.3 * CM))
    story.append(PageBreak())

    # --- per sample ---
    story.append(Paragraph("3. Per-sample analyses", styles["H2c"]))
    for sid, res in results.items():
        st, cm = res["stats"], res["passega_cm"]
        story.append(Paragraph(str(sid), styles["H3c"]))
        info = [
            ["Mean", f"{st['mean_phi']:.2f} phi ({st['mean_um']:.0f} um) - {st['mean_class']}"],
            ["Sorting", f"{st['sigma_I']:.2f} - {st['sorting']}"],
            ["Skewness", f"{st['Sk_I']:.2f} - {st['skewness']}"],
            ["Kurtosis", f"{st['K_G']:.2f} - {st['kurtosis']}"],
            ["Modality", res["frequency_curve"]["modality"]],
            ["Folk / Shepard", f"{res['folk']['folk_class']} / {res['shepard']['shepard_class']}"],
            ["Passega C-M", f"C={cm['C_um']:.0f} um, M={cm['M_um']:.0f} um, C/M={cm['C_over_M']:.1f}"],
            ["Transport", cm["mechanism"]],
            ["Visher env.", res["visher"]["environment"]],
        ]
        it = Table(info, colWidths=[3.2 * CM, 12.5 * CM])
        it.setStyle(TableStyle([
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#dddddd")),
            ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#eef4fb")),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ]))
        story.append(it)
        # figures 2x2 grid
        imgs = []
        for kind in ("histogram", "frequency_curve", "cumulative", "probability"):
            p = res["_figures"].get(kind)
            if p and os.path.exists(p):
                imgs.append(_fit_image(Image, p, 7.6 * CM))
        if imgs:
            rows = [imgs[i:i + 2] for i in range(0, len(imgs), 2)]
            for r in rows:
                while len(r) < 2:
                    r.append("")
            gt = Table(rows, colWidths=[8 * CM, 8 * CM])
            gt.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))
            story.append(gt)
        story.append(Paragraph("<b>Interpretation:</b> " + res["interpretation"],
                               styles["Interp"]))
        story.append(PageBreak())

    # --- final interpretation ---
    story.append(Paragraph("4. Final sedimentological interpretation", styles["H2c"]))
    final = _dataset_interpretation(results, summary_df).replace("<strong>", "<b>").replace("</strong>", "</b>")
    story.append(Paragraph(final, styles["Normal"]))
    story.append(Spacer(1, 0.5 * CM))

    # --- references ---
    story.append(Paragraph("5. References", styles["H2c"]))
    for i, r in enumerate(REFERENCES, 1):
        story.append(Paragraph(f"{i}. {r}", small))

    story.append(Spacer(1, 0.8 * CM))
    story.append(Paragraph(
        f"Processing date: {meta['date']} &bull; "
        f"Software: Sedimentology-GrainSize v{meta['version']} &bull; "
        f"Runtime: {meta.get('elapsed_s','?')} s", small))

    doc.build(story)
    return path


def _fit_image(Image, path, width):
    """Load an image scaled to `width`, preserving aspect ratio."""
    from reportlab.lib.utils import ImageReader
    ir = ImageReader(path)
    iw, ih = ir.getSize()
    h = width * ih / iw
    return Image(path, width=width, height=h)
