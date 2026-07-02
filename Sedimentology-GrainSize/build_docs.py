"""Generate docs/tutorial.pdf and docs/quick_start.pdf with embedded screenshots."""
import os
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Image,
                                PageBreak, ListFlowable, ListItem)
from reportlab.lib.utils import ImageReader

IMG = "docs/images"
os.makedirs("docs", exist_ok=True)

st = getSampleStyleSheet()
st.add(ParagraphStyle("H1c", parent=st["Title"], textColor=colors.HexColor("#1F4E79")))
st.add(ParagraphStyle("H2c", parent=st["Heading2"], textColor=colors.HexColor("#1F4E79")))
st.add(ParagraphStyle("H3c", parent=st["Heading3"], textColor=colors.HexColor("#2E75B6")))
st.add(ParagraphStyle("CodeBox", parent=st["Code"], backColor=colors.HexColor("#f0f2f5"),
                      borderPadding=6, leftIndent=6, fontSize=8.5))
body = st["BodyText"]


def img(name, width=15 * cm):
    p = os.path.join(IMG, name)
    if not os.path.exists(p):
        return Spacer(1, 0.2 * cm)
    ir = ImageReader(p); iw, ih = ir.getSize()
    return Image(p, width=width, height=width * ih / iw)


def build_quickstart():
    doc = SimpleDocTemplate("docs/quick_start.pdf", pagesize=A4,
                            topMargin=1.6 * cm, bottomMargin=1.6 * cm)
    s = []
    s += [Paragraph("Quick Start Guide", st["H1c"]),
          Paragraph("Sedimentology-GrainSize toolkit", st["H3c"]),
          Spacer(1, 0.5 * cm)]
    s += [Paragraph("1. Install", st["H2c"]),
          Paragraph("Offline (Anaconda or pip):", body),
          Paragraph("pip install -r requirements.txt", st["CodeBox"]),
          Spacer(1, 0.3 * cm),
          Paragraph("Google Colab: open <b>notebooks/Master_Workflow_Colab.ipynb</b> "
                    "and run the first cell - it installs everything automatically.", body),
          Spacer(1, 0.4 * cm)]
    s += [Paragraph("2. Run the master workflow", st["H2c"]),
          Paragraph("The fastest path is three lines of Python:", body),
          Paragraph("import grainsize as gs<br/>"
                    "out = gs.run_workflow('sample_data/river.csv', outdir='output')<br/>"
                    "out['summary_df']", st["CodeBox"]),
          Spacer(1, 0.3 * cm),
          Paragraph("This produces, for every sample: histogram, frequency curve, "
                    "cumulative curve, Passega C-M, Folk &amp; Shepard ternary "
                    "classification, and a Visher log-probability analysis - plus "
                    "figures (PNG/TIFF/SVG/PDF), summary CSVs, and PDF + HTML reports.", body),
          Spacer(1, 0.4 * cm)]
    s += [Paragraph("3. Use your own data", st["H2c"]),
          Paragraph("Prepare a CSV with a <b>sample</b> column and one column per "
                    "grain-size class (headers in phi, mm, or um; cells = weight %). "
                    "Then:", body),
          Paragraph("out = gs.run_workflow('mydata.csv', size_unit='phi',<br/>"
                    "&nbsp;&nbsp;&nbsp;&nbsp;value_type='frequency', outdir='output')", st["CodeBox"]),
          Spacer(1, 0.4 * cm)]
    s += [Paragraph("4. Where to find outputs", st["H2c"]),
          Paragraph("output/figures/  - all figures (per sample + dataset diagrams)<br/>"
                    "output/csv/      - summary and segment tables<br/>"
                    "output/reports/  - PDF report<br/>"
                    "output/html/     - HTML report (open in any browser)", st["CodeBox"]),
          Spacer(1, 0.4 * cm),
          Paragraph("Example output - histogram:", st["H3c"]),
          img("screenshot_histogram.png", 13 * cm)]
    doc.build(s)
    print("wrote docs/quick_start.pdf")


def build_tutorial():
    doc = SimpleDocTemplate("docs/tutorial.pdf", pagesize=A4,
                            topMargin=1.6 * cm, bottomMargin=1.6 * cm)
    s = []
    # Cover
    s += [Spacer(1, 3 * cm),
          Paragraph("Step-by-Step Tutorial", st["H1c"]),
          Spacer(1, 0.3 * cm),
          Paragraph("Grain-Size Analysis with the Sedimentology-GrainSize toolkit",
                    st["H3c"]),
          PageBreak()]

    # Section 1
    s += [Paragraph("1. What this toolkit does", st["H2c"]),
          Paragraph("Given a table of grain-size measurements, the toolkit runs seven "
                    "standard sedimentological analyses and assembles the results into "
                    "publication-ready figures and reports. The seven analyses are:", body),
          ListFlowable([
              ListItem(Paragraph("Grain-size histogram (frequency per class)", body)),
              ListItem(Paragraph("Smooth frequency distribution curve with mode detection", body)),
              ListItem(Paragraph("Cumulative curve and Folk &amp; Ward (1957) statistics", body)),
              ListItem(Paragraph("Passega C-M transport analysis", body)),
              ListItem(Paragraph("Folk (1954) ternary classification", body)),
              ListItem(Paragraph("Shepard (1954) ternary classification", body)),
              ListItem(Paragraph("Visher (1969) log-probability transport-population analysis", body)),
          ], bulletType="1"),
          Spacer(1, 0.4 * cm)]

    # Section 2
    s += [Paragraph("2. Preparing your input CSV", st["H2c"]),
          Paragraph("The WIDE format (recommended): the first column is the sample "
                    "name; every other column header is a grain-size class value; each "
                    "cell is the weight percent in that class.", body),
          Paragraph("sample,-1,-0.5,0,0.5,1,1.5,2,2.5,3,...<br/>"
                    "RIV-01,0.0,0.2,1.1,3.5,8.2,14.1,18.6,19.0,15.3,...", st["CodeBox"]),
          Paragraph("Column headers may be in phi, mm, or micrometres - set "
                    "<b>size_unit</b> accordingly. Rows need not sum to 100; they are "
                    "normalised automatically. A LONG (tidy) layout with sample/size/value "
                    "columns is also accepted and auto-detected.", body),
          Spacer(1, 0.4 * cm)]

    # Section 3
    s += [Paragraph("3. Running the analysis", st["H2c"]),
          Paragraph("Open <b>notebooks/Master_Workflow.ipynb</b> (offline) or "
                    "<b>Master_Workflow_Colab.ipynb</b> (Colab), then run the cells "
                    "top to bottom. Or from a Python session:", body),
          Paragraph("import grainsize as gs<br/>"
                    "out = gs.run_workflow('sample_data/beach.csv', outdir='output')",
                    st["CodeBox"]),
          PageBreak()]

    # Section 4 - reading outputs, with images
    s += [Paragraph("4. Reading the outputs", st["H2c"]),
          Paragraph("<b>Histogram</b> - bars coloured by Wentworth fraction, with mean, "
                    "median and modal class marked:", body),
          img("screenshot_histogram.png", 13 * cm),
          Spacer(1, 0.3 * cm),
          Paragraph("<b>Frequency curve</b> - smooth envelope revealing modality:", body),
          img("screenshot_frequency_curve.png", 13 * cm),
          PageBreak(),
          Paragraph("<b>Passega C-M diagram</b> - transport mechanism from the coarsest "
                    "(C) and median (M) grain sizes:", body),
          img("screenshot_passega_cm.png", 10 * cm),
          Spacer(1, 0.3 * cm),
          Paragraph("<b>Folk ternary</b> - textural class from sand-silt-clay ratios:", body),
          img("screenshot_folk_ternary.png", 11 * cm),
          PageBreak(),
          Paragraph("<b>Visher log-probability plot</b> - traction/saltation/suspension "
                    "sub-populations detected automatically:", body),
          img("screenshot_probability.png", 13 * cm),
          Spacer(1, 0.4 * cm)]

    # Section 5 - reports
    s += [Paragraph("5. The generated reports", st["H2c"]),
          Paragraph("Every run produces a professional PDF and a self-contained HTML "
                    "report with a cover page, per-sample results, all figures, "
                    "interpretations, and references.", body),
          img("screenshot_report_cover.png", 10 * cm),
          Spacer(1, 0.3 * cm),
          Paragraph("A per-sample page from the PDF report:", body),
          img("screenshot_report_sample.png", 12 * cm),
          Spacer(1, 0.4 * cm)]

    # Section 6 - individual analyses
    s += [Paragraph("6. Running a single analysis", st["H2c"]),
          Paragraph("If you only need one analysis, open the matching notebook in "
                    "<b>notebooks/</b> (01_Histogram through 07_Visher_Probability). "
                    "Each is self-contained and follows the same load-analyse-plot "
                    "pattern.", body),
          Spacer(1, 0.4 * cm),
          Paragraph("7. Troubleshooting", st["H2c"]),
          Paragraph("If a notebook cannot find the <b>grainsize</b> package or "
                    "<b>sample_data/</b>, make sure you run it from within the "
                    "repository - the setup cell changes the working directory to the "
                    "repo root automatically. See the README FAQ for more.", body)]

    doc.build(s)
    print("wrote docs/tutorial.pdf")


if __name__ == "__main__":
    build_quickstart()
    build_tutorial()
