"""Build the Master notebook + 7 individual notebooks, in Colab & offline forms."""
import nbformat as nbf
import os

NBDIR = "notebooks"
os.makedirs(NBDIR, exist_ok=True)


def md(s):   return nbf.v4.new_markdown_cell(s.strip("\n"))
def code(s): return nbf.v4.new_code_cell(s.strip("\n"))


def new_nb(cells):
    nb = nbf.v4.new_notebook()
    nb.metadata.kernelspec = {"display_name": "Python 3", "language": "python", "name": "python3"}
    nb.cells = cells
    return nb


# ---- shared setup cell variants -------------------------------------
COLAB_SETUP = '''
# === Google Colab setup ===================================================
# Installs dependencies and fetches the grainsize package + sample data.
import sys, subprocess, os

def sh(cmd):
    print("$", cmd); subprocess.run(cmd, shell=True, check=False)

# 1. Dependencies (all public PyPI packages)
sh(f"{sys.executable} -m pip install -q numpy pandas matplotlib scipy openpyxl reportlab")

# 2. Get the package. If you cloned the repo to Drive, point PROJECT_DIR there.
#    Otherwise this cell expects the `grainsize/` folder next to the notebook
#    (upload the repo folder, or clone from GitHub).
PROJECT_DIR = os.getcwd()
if not os.path.isdir(os.path.join(PROJECT_DIR, "grainsize")):
    # Try one level up (if notebook is inside notebooks/)
    up = os.path.dirname(PROJECT_DIR)
    if os.path.isdir(os.path.join(up, "grainsize")):
        PROJECT_DIR = up
sys.path.insert(0, PROJECT_DIR)
os.chdir(PROJECT_DIR)   # so sample_data/ and output/ resolve correctly
print("PROJECT_DIR =", PROJECT_DIR)

# 3. (Optional) mount Google Drive to save outputs there
try:
    from google.colab import drive
    MOUNT = False  # set True to mount
    if MOUNT:
        drive.mount("/content/drive")
except Exception:
    pass

import grainsize as gs
print("grainsize version:", gs.__version__)
'''

OFFLINE_SETUP = '''
# === Offline / local setup ================================================
# Assumes you installed requirements:  pip install -r requirements.txt
import sys, os
# Make the grainsize package importable whether the notebook is in the repo
# root or in notebooks/
here = os.getcwd()
ROOT = None
for cand in (here, os.path.dirname(here)):
    if os.path.isdir(os.path.join(cand, "grainsize")):
        ROOT = cand; break
if ROOT is None:
    raise RuntimeError("Could not locate the 'grainsize' package. "
                       "Run this notebook from inside the repository.")
sys.path.insert(0, ROOT)
os.chdir(ROOT)   # so that sample_data/ and output/ resolve correctly
print("Working directory:", os.getcwd())
import grainsize as gs
print("grainsize version:", gs.__version__)
'''

UPLOAD_CELL = '''
# === Choose your input CSV ================================================
# Option A - use a bundled example dataset:
CSV_PATH = "sample_data/river.csv"    # <-- change to any file in sample_data/

# Option B (Colab) - upload your own CSV instead:
#   from google.colab import files
#   up = files.upload()
#   CSV_PATH = list(up.keys())[0]

# Settings for YOUR data (defaults suit the bundled examples):
SIZE_UNIT  = "phi"         # "phi", "mm", or "um"
VALUE_TYPE = "frequency"   # "frequency" or "cumulative"
OUTDIR     = "output"
'''


# ====================================================================
# MASTER notebook
# ====================================================================
def master_notebook(colab: bool):
    setup = COLAB_SETUP if colab else OFFLINE_SETUP
    env = "Google Colab" if colab else "offline Jupyter"
    cells = [
        md(f"""
# Master Workflow - Grain-Size Analysis ({env})

Runs **all seven analyses** on a single grain-size CSV and generates every output:

1. Histogram (grain-size frequency)
2. Frequency distribution curve (modality)
3. Cumulative curve + Folk & Ward statistics
4. Passega C-M (transport mechanism)
5. Folk (1954) ternary classification
6. Shepard (1954) ternary classification
7. Visher (1969) log-probability transport-population analysis

**Outputs:** per-sample figures (PNG 300dpi / TIFF / SVG / PDF), summary CSVs,
and professional PDF + HTML reports.
"""),
        md("## Step 1 - Setup"),
        code(setup),
        md("## Step 2 - Choose input"),
        code(UPLOAD_CELL),
        md("## Step 3 - Run the full workflow"),
        code('''
out = gs.run_workflow(
    CSV_PATH,
    outdir=OUTDIR,
    size_unit=SIZE_UNIT,
    value_type=VALUE_TYPE,
    figure_formats=("png", "tiff", "svg", "pdf"),
    make_reports=True,
)

print("\\nSamples analysed:", out["meta"]["n_samples"])
print("Files written    :", len(out["paths"]))
'''),
        md("## Step 4 - Inspect the summary table"),
        code('out["summary_df"]'),
        md("## Step 5 - View the dataset-level diagrams inline"),
        code('''
from IPython.display import Image, display
for kind in ("passega_cm", "folk_ternary", "shepard_ternary"):
    p = out["dataset_figures"].get(kind)
    if p:
        print(kind)
        display(Image(filename=p))
'''),
        md("## Step 6 - Open the reports\nThe PDF and HTML reports are in `output/reports/` and `output/html/`."),
        code('''
import os
dataset = out["meta"]["dataset"]
print("PDF :", os.path.join(OUTDIR, "reports", dataset + "_report.pdf"))
print("HTML:", os.path.join(OUTDIR, "html", dataset + "_report.html"))
print("CSV :", os.path.join(OUTDIR, "csv", dataset + "_summary.csv"))

# In Colab you can download them:
# from google.colab import files
# files.download(os.path.join(OUTDIR, "reports", dataset + "_report.pdf"))
'''),
        md("""
## Batch mode - process every dataset in `sample_data/`

Uncomment to run the whole example library at once.
"""),
        code('''
# import glob
# for f in sorted(glob.glob("sample_data/*.csv")):
#     gs.run_workflow(f, outdir=OUTDIR, figure_formats=("png",), make_reports=True)
'''),
    ]
    return new_nb(cells)


# ====================================================================
# INDIVIDUAL notebooks
# ====================================================================
INDIVIDUAL = [
    ("01_Histogram", "Histogram - Grain-Size Frequency", "histogram", '''
for sid, (phi, freq, cum) in samples.items():
    res = gs.analyses.histogram_summary(phi, freq, cum)
    fig = gs.plots.fig_histogram(sid, phi, freq, res)
    gs.plots.save_figure(fig, f"{OUTDIR}/figures/{sid}_histogram", formats=FIGURE_FORMATS)
    display(fig); plt.close(fig)
    print(sid, "->", res["mode_class"], "| texture:", res["texture"])
'''),
    ("02_Frequency_Curve", "Frequency Distribution Curve", "frequency_curve", '''
for sid, (phi, freq, cum) in samples.items():
    res = gs.analyses.frequency_curve(phi, freq)
    fig = gs.plots.fig_frequency_curve(sid, phi, freq, res)
    gs.plots.save_figure(fig, f"{OUTDIR}/figures/{sid}_frequency_curve", formats=FIGURE_FORMATS)
    display(fig); plt.close(fig)
    print(sid, "->", res["modality"], "| modes (phi):", res["modes_phi"])
'''),
    ("03_Statistics", "Folk & Ward Grain-Size Statistics", "statistics", '''
rows = []
for sid, (phi, freq, cum) in samples.items():
    st = gs.analyses.statistics(phi, freq, cum)
    fig = gs.plots.fig_cumulative(sid, phi, cum, st)
    gs.plots.save_figure(fig, f"{OUTDIR}/figures/{sid}_cumulative", formats=FIGURE_FORMATS)
    display(fig); plt.close(fig)
    rows.append({"sample": sid, "mean_phi": round(st["mean_phi"],2),
                 "sorting": st["sorting"], "skewness": st["skewness"],
                 "kurtosis": st["kurtosis"]})
import pandas as pd; pd.DataFrame(rows)
'''),
    ("04_Passega_CM", "Passega C-M Transport Analysis", "passega_cm", '''
cm_by_sample = {}
for sid, (phi, freq, cum) in samples.items():
    cm = gs.analyses.passega_cm(phi, freq, cum)
    cm_by_sample[sid] = cm
    print(f"{sid}: C={cm['C_um']:.0f} um  M={cm['M_um']:.0f} um  C/M={cm['C_over_M']:.1f}  -> {cm['mechanism']}")
fig = gs.plots.fig_passega_cm(cm_by_sample)
gs.plots.save_figure(fig, f"{OUTDIR}/figures/passega_cm", formats=FIGURE_FORMATS)
display(fig); plt.close(fig)
'''),
    ("05_Folk_Ternary", "Folk (1954) Ternary Classification", "folk", '''
points = []
for sid, (phi, freq, cum) in samples.items():
    fr = gs.textural_fractions(phi, freq)
    folk = gs.analyses.folk_ternary(fr)
    points.append({"sample": sid, **folk})
    print(f"{sid}: {folk['folk_class']} ({folk['folk_code']})")
fig = gs.plots.fig_folk_ternary(points)
gs.plots.save_figure(fig, f"{OUTDIR}/figures/folk_ternary", formats=FIGURE_FORMATS)
display(fig); plt.close(fig)
'''),
    ("06_Shepard_Ternary", "Shepard (1954) Ternary Classification", "shepard", '''
points = []
for sid, (phi, freq, cum) in samples.items():
    fr = gs.textural_fractions(phi, freq)
    shep = gs.analyses.shepard_ternary(fr)
    points.append({"sample": sid, **shep})
    print(f"{sid}: {shep['shepard_class']} ({shep['shepard_code']})")
fig = gs.plots.fig_shepard_ternary(points)
gs.plots.save_figure(fig, f"{OUTDIR}/figures/shepard_ternary", formats=FIGURE_FORMATS)
display(fig); plt.close(fig)
'''),
    ("07_Visher_Probability", "Visher (1969) Log-Probability Analysis", "visher", '''
for sid, (phi, freq, cum) in samples.items():
    v = gs.analyses.visher_populations(phi, freq, cum)
    fig = gs.plots.fig_probability(sid, phi, cum, v)
    gs.plots.save_figure(fig, f"{OUTDIR}/figures/{sid}_probability", formats=FIGURE_FORMATS)
    display(fig); plt.close(fig)
    print(f"{sid}: {v['n_segments']} populations -> {v['environment']}")
'''),
]


def individual_notebook(title, run_code, colab: bool):
    setup = COLAB_SETUP if colab else OFFLINE_SETUP
    cells = [
        md(f"# {title}\n\nOne of seven analyses in the Sedimentology-GrainSize toolkit. "
           f"For the full pipeline see `Master_Workflow.ipynb`."),
        md("## Step 1 - Setup"),
        code(setup),
        md("## Step 2 - Load data"),
        code('''
CSV_PATH   = "sample_data/river.csv"   # change to your file / any sample_data/*.csv
SIZE_UNIT  = "phi"                       # "phi", "mm", "um"
VALUE_TYPE = "frequency"                 # "frequency" or "cumulative"
OUTDIR     = "output"
FIGURE_FORMATS = ("png", "svg")          # add "tiff","pdf" for publication export

import os, matplotlib.pyplot as plt
os.makedirs(f"{OUTDIR}/figures", exist_ok=True)
samples = gs.load_grainsize(CSV_PATH, size_unit=SIZE_UNIT, value_type=VALUE_TYPE)
print(len(samples), "samples loaded")
'''),
        md("## Step 3 - Run analysis and plot"),
        code(run_code),
    ]
    return new_nb(cells)


def main():
    # Master notebooks (Colab + offline)
    nbf.write(master_notebook(colab=False), f"{NBDIR}/Master_Workflow.ipynb")
    nbf.write(master_notebook(colab=True),  f"{NBDIR}/Master_Workflow_Colab.ipynb")
    print("wrote Master_Workflow.ipynb + Colab")

    for fname, title, _key, run_code in INDIVIDUAL:
        nbf.write(individual_notebook(title, run_code, colab=False), f"{NBDIR}/{fname}.ipynb")
    print(f"wrote {len(INDIVIDUAL)} individual notebooks")


if __name__ == "__main__":
    main()
