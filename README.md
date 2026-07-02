# Sedimentology-GrainSize

A complete, tested toolkit for **grain-size analysis of clastic sediments**.
From a single CSV it runs **seven standard analyses** on every sample and
produces publication-quality figures, summary tables, and professional
**PDF + HTML reports**.

Works both in **Google Colab** (zero install) and **offline Jupyter /
JupyterLab** on Windows, macOS, and Linux.

---

## Table of contents

1. [Overview](#overview)
2. [Features](#features)
3. [The seven analyses](#the-seven-analyses)
4. [Installation](#installation)
5. [Google Colab usage](#google-colab-usage)
6. [Offline Jupyter usage](#offline-jupyter-usage)
7. [Required packages](#required-packages)
8. [Input CSV format](#input-csv-format)
9. [Output descriptions](#output-descriptions)
10. [Folder structure](#folder-structure)
11. [Example workflow](#example-workflow)
12. [Screenshots](#screenshots)
13. [Example datasets](#example-datasets)
14. [Testing](#testing)
15. [Citation](#citation)
16. [License](#license)
17. [Troubleshooting](#troubleshooting)
18. [FAQ](#faq)
19. [References](#references)

---

## Overview

Grain-size analysis is the foundation of clastic sedimentology. This
repository packages the standard descriptive, statistical, and hydrodynamic
methods into a single reproducible workflow. Give it a table of sieve /
settling / laser-diffraction results and it returns everything you need for
a facies interpretation or a methods figure in a paper.

The code is organised as an importable Python package (`grainsize/`) with a
thin notebook layer on top, so the same tested functions run whether you use
the master notebook, an individual analysis notebook, or plain Python.

## Features

- **One CSV in, everything out** - a single `run_workflow()` call produces all
  figures, tables, and reports.
- **Seven analyses per sample** (see below).
- **Publication-quality figures** exported in **PNG (300 dpi), TIFF (300 dpi),
  SVG (vector), and PDF (vector)** with consistent fonts, labels, and sizing.
- **Professional reports** - PDF (reportlab) and self-contained HTML, each with
  a cover page, sample information, statistics, every analysis, all plots,
  per-sample interpretation, a final dataset interpretation, references, and
  the processing date + software version.
- **Master workflow** that runs all seven analyses sequentially, **plus seven
  standalone notebooks** for users who need only one method.
- **17 realistic example datasets** spanning the main sedimentary environments.
- **Full pytest suite** - 31 tests including an end-to-end run on every dataset.
- **Cross-platform** and dependency-light (all public PyPI / conda packages).

## The seven analyses

| # | Analysis | Notebook | What it yields |
|---|----------|----------|----------------|
| 1 | Grain-size **histogram** | `01_Histogram.ipynb` | Modal class, mean/median, Wentworth fractions |
| 2 | **Frequency distribution curve** | `02_Frequency_Curve.ipynb` | Smooth curve, modality (uni/bi/polymodal) |
| 3 | Cumulative curve + **Folk & Ward statistics** | `03_Statistics.ipynb` | Mean, sorting, skewness, kurtosis (+ verbal) |
| 4 | **Passega C-M** | `04_Passega_CM.ipynb` | C, M, C/M, transport mechanism |
| 5 | **Folk (1954) ternary** | `05_Folk_Ternary.ipynb` | 10-class textural name (ratio-based) |
| 6 | **Shepard (1954) ternary** | `06_Shepard_Ternary.ipynb` | 10-class textural name (descriptive) |
| 7 | **Visher (1969) log-probability** | `07_Visher_Probability.ipynb` | Traction/saltation/suspension populations |

The **Master_Workflow** notebook runs all seven at once.

## Installation

### Offline (Anaconda recommended)

```bash
git clone https://github.com/<your-user>/Sedimentology-GrainSize.git
cd Sedimentology-GrainSize

# Option A - conda
conda env create -f environment.yml
conda activate sedimentology-grainsize

# Option B - pip
pip install -r requirements.txt
```

### Google Colab

Nothing to install locally - open a notebook in Colab and run the first cell
(it pip-installs everything). See below.

## Google Colab usage

1. Upload the repository folder to Google Drive, **or** clone it in the first
   cell from GitHub.
2. Open **`notebooks/Master_Workflow_Colab.ipynb`** in Colab
   (File -> Open notebook -> GitHub / Upload).
3. Run the **Setup** cell - it installs dependencies, locates the `grainsize`
   package, and (optionally) mounts Google Drive.
4. In the **Choose input** cell, either keep a bundled example
   (`sample_data/river.csv`) or uncomment the `files.upload()` block to upload
   your own CSV.
5. Run the rest of the cells. Download the reports with `files.download(...)`.

## Offline Jupyter usage

```bash
conda activate sedimentology-grainsize   # or your venv
jupyter lab                              # or: jupyter notebook
```

Open **`notebooks/Master_Workflow.ipynb`** and run all cells. The setup cell
automatically finds the repository root, so relative paths to `sample_data/`
and `output/` work whether the notebook lives in the repo root or in
`notebooks/`.

You can also skip the notebooks entirely:

```python
import grainsize as gs
out = gs.run_workflow("sample_data/turbidite.csv", outdir="output")
print(out["summary_df"])
```

## Required packages

All are public and available on PyPI and conda-forge:

`numpy`, `pandas`, `matplotlib`, `scipy`, `openpyxl`, `reportlab`
(+ `jupyter`/`notebook` to run the notebooks; `pytest` to run the tests).

## Input CSV format

Two layouts are accepted and **auto-detected**.

### Wide (recommended) - one row per sample

The first column is the sample name; every other column header is a
grain-size class value; each cell is the **weight %** in that class.

```csv
sample,-1,-0.5,0,0.5,1,1.5,2,2.5,3,3.5,4,4.5,5,6,7,8
RIV-01,0.0,0.2,1.1,3.5,8.2,14.1,18.6,19.0,15.3,9.8,5.1,2.6,1.3,0.7,0.3,0.1
```

- Column headers may be in **phi** (default), **mm**, or **um** -> set
  `size_unit="phi"|"mm"|"um"`.
- Rows need **not** sum to 100 (auto-normalised).
- Column order does not matter.

Phi reminder: `phi = -log2(d_mm)`. -1 phi = 2 mm, 0 phi = 1 mm,
4 phi = 63 um (silt boundary), 8 phi ≈ 4 um (clay).

### Long (tidy) - one row per sample × class

```csv
sample,size,value
RIV-01,-1,0.0
RIV-01,-0.5,0.2
RIV-01,0,1.1
```

### Cumulative input

If your cells hold cumulative % finer (an ogive, 0->100), set
`value_type="cumulative"`.

### Excel

`.xlsx` files with the same structure work identically (first sheet is read).

## Output descriptions

Running the workflow creates, under `outdir/`:

```
figures/<dataset>/   Per-sample figures (histogram, frequency_curve,
                     cumulative, probability) + dataset diagrams
                     (passega_cm, folk_ternary, shepard_ternary),
                     each as PNG / TIFF / SVG / PDF.
csv/                 <dataset>_summary.csv        (one row per sample: mean,
                                                   sorting, skewness, kurtosis,
                                                   C/M, fractions, classes, env)
                     <dataset>_visher_segments.csv (one row per Visher segment)
reports/             <dataset>_report.pdf         (professional PDF report)
html/                <dataset>_report.html        (self-contained HTML report)
```

Each report contains: cover page, dataset summary, dataset-level diagrams,
per-sample statistics + all four figures + interpretation, a final
sedimentological interpretation, references, and the processing date +
software version.

## Folder structure

```
Sedimentology-GrainSize/
|
|-- grainsize/                 # the tested Python package
|   |-- __init__.py
|   |-- core.py                # I/O, units, Folk & Ward statistics
|   |-- analyses.py            # the seven analyses
|   |-- plots.py               # figures + multi-format export
|   |-- report.py              # PDF + HTML report generation
|   |-- workflow.py            # master orchestrator (run_workflow)
|
|-- notebooks/
|   |-- Master_Workflow.ipynb          # all 7 analyses (offline)
|   |-- Master_Workflow_Colab.ipynb    # all 7 analyses (Colab)
|   |-- 01_Histogram.ipynb
|   |-- 02_Frequency_Curve.ipynb
|   |-- 03_Statistics.ipynb
|   |-- 04_Passega_CM.ipynb
|   |-- 05_Folk_Ternary.ipynb
|   |-- 06_Shepard_Ternary.ipynb
|   |-- 07_Visher_Probability.ipynb
|
|-- sample_data/               # 17 example datasets (see below)
|-- example_outputs/           # ready-made figures, CSVs, reports, screenshots
|   |-- reports/  csv/  html/  figures/  screenshots/
|-- docs/
|   |-- tutorial.pdf           # step-by-step tutorial with images
|   |-- quick_start.pdf        # one-page quick start
|   |-- images/                # screenshots used in docs & README
|
|-- tests/test_grainsize.py    # pytest suite (31 tests)
|-- make_sample_data.py        # regenerates sample_data/
|-- build_notebooks.py         # regenerates the notebooks
|-- build_docs.py              # regenerates the doc PDFs
|-- requirements.txt
|-- environment.yml
|-- LICENSE
|-- README.md
```

## Example workflow

```python
import grainsize as gs

# 1. Run everything on one dataset
out = gs.run_workflow(
    "sample_data/beach.csv",
    outdir="output",
    size_unit="phi",
    value_type="frequency",
    figure_formats=("png", "tiff", "svg", "pdf"),
    make_reports=True,
)

# 2. Inspect the summary
print(out["summary_df"][["sample", "mean_phi", "sorting",
                         "folk_class", "transport"]])

# 3. Batch-process the whole example library
import glob
for f in sorted(glob.glob("sample_data/*.csv")):
    gs.run_workflow(f, outdir="output", figure_formats=("png",))
```

## Screenshots

Grain-size histogram (Wentworth-coloured, mean/median/mode marked):

![histogram](docs/images/screenshot_histogram.png)

Visher log-probability transport-population plot:

![probability](docs/images/screenshot_probability.png)

Folk ternary classification and Passega C-M diagram:

![folk](docs/images/screenshot_folk_ternary.png)
![cm](docs/images/screenshot_passega_cm.png)

PDF report cover and a per-sample page:

![report cover](docs/images/screenshot_report_cover.png)
![report sample](docs/images/screenshot_report_sample.png)

## Example datasets

`sample_data/` contains 17 datasets, each with several samples and a distinct
textural signature:

| File | Environment | File | Environment |
|------|-------------|------|-------------|
| `river.csv` | River channel sand | `glacial.csv` | Glacial diamict |
| `floodplain.csv` | Floodplain deposits | `alluvial_fan.csv` | Alluvial fan |
| `beach.csv` | Beach sand | `desert.csv` | Desert / aeolian |
| `dune.csv` | Coastal dune sand | `bimodal.csv` | Mixed bimodal |
| `delta.csv` | Delta sediments | `poorly_sorted.csv` | Poorly sorted |
| `estuary.csv` | Estuarine sediments | `well_sorted.csv` | Very well sorted |
| `shelf.csv` | Shelf sediments | `mud_rich.csv` | Fine mud-rich |
| `deep_marine.csv` | Deep marine mud | `gravel_rich.csv` | Coarse gravel-rich |
| `turbidite.csv` | Turbidites | | |

## Testing

```bash
pytest -q          # from the repository root
```

The suite (31 tests) covers unit conversions, all input layouts
(wide/long/cumulative, phi/mm/um), every analysis, figure generation and
multi-format export, report generation, and a **full end-to-end workflow run
on all 17 datasets**. All notebooks are also verified to execute start to
finish.

## Citation

If you use this toolkit in published work, please cite it and the original
methods:

```bibtex
@software{sedimentology_grainsize,
  title  = {Sedimentology-GrainSize: a reproducible grain-size analysis toolkit},
  year   = {2026},
  note   = {Version 1.0.0},
  url    = {https://github.com/<your-user>/Sedimentology-GrainSize}
}
```

Please also cite the underlying methods (Folk & Ward 1957; Folk 1954;
Shepard 1954; Passega 1964; Visher 1969) - see [References](#references).

## License

Released under the **MIT License** - see [`LICENSE`](LICENSE).

## Troubleshooting

**`ModuleNotFoundError: grainsize`** - run the notebook from inside the
repository (the setup cell locates the package and sets the working
directory). If importing from your own script, add the repo root to
`sys.path` or `pip install -e .`.

**`FileNotFoundError: sample_data/...`** - you are not in the repo root. In a
notebook, re-run the setup cell (it calls `os.chdir` to the repo root). In a
script, pass an absolute path.

**PDF report not generated** - `reportlab` is missing. Install it
(`pip install reportlab`). The HTML report is always generated regardless.

**TIFF export fails** - your matplotlib/Pillow build lacks TIFF support.
Other formats still export; install a full Pillow (`pip install -U pillow`).

**Fonts look different across machines** - figures use `DejaVu Sans` (bundled
with matplotlib) for reproducibility. This is expected and intentional.

**Colab: Drive files not found** - set `MOUNT = True` in the setup cell and
point `PROJECT_DIR` at your repo folder in Drive.

## FAQ

**Q. Do my grain-size classes have to be in phi?**
No. Set `size_unit="mm"` or `"um"`. Everything is converted to phi internally.

**Q. My percentages don't add to 100 - is that a problem?**
No, each sample is normalised to 100 % automatically.

**Q. Can I analyse just one sample, or just one method?**
Yes. Use the individual notebooks in `notebooks/`, or call the specific
function, e.g. `grainsize.analyses.passega_cm(phi, freq, cum)`.

**Q. What if my sediment contains gravel?**
The histogram, statistics, C-M, and Visher analyses handle gravel directly.
The Folk and Shepard **ternaries** are sand-silt-clay diagrams: the toolkit
renormalises the < 2 mm fraction and classifies that. For strongly gravelly
samples, interpret the ternary class as applying to the sand-mud fraction.

**Q. How many size classes do I need?**
More is better. Folk & Ward statistics need the curve to reach the 5th and
95th percentiles; Visher segmentation is most reliable with >= 15 classes at
0.25-0.5 phi spacing.

**Q. Are the environmental interpretations definitive?**
No - they are indicative, first-pass aids. Always integrate them with field
observations, sedimentary structures, and stratigraphic context.

**Q. Can I change figure styling / DPI / formats?**
Yes. `figure_formats=(...)` controls which formats are written; DPI is 300 for
raster formats. Edit `grainsize/plots.py` `apply_style()` for global styling.

**Q. How do I regenerate the sample data / notebooks / docs?**
Run `python make_sample_data.py`, `python build_notebooks.py`, or
`python build_docs.py` from the repo root.

## References

- Folk, R. L. (1954) The distinction between grain size and mineral
  composition in sedimentary-rock nomenclature. *Journal of Geology* 62,
  344-359.
- Folk, R. L. & Ward, W. C. (1957) Brazos River bar: a study in the
  significance of grain size parameters. *Journal of Sedimentary Petrology*
  27, 3-26.
- Shepard, F. P. (1954) Nomenclature based on sand-silt-clay ratios.
  *Journal of Sedimentary Petrology* 24, 151-158.
- Passega, R. (1964) Grain size representation by CM patterns as a geological
  tool. *Journal of Sedimentary Petrology* 34, 830-847.
- Visher, G. S. (1969) Grain size distributions and depositional processes.
  *Journal of Sedimentary Petrology* 39, 1074-1106.
- Blott, S. J. & Pye, K. (2001) GRADISTAT: a grain size distribution and
  statistics package for the analysis of unconsolidated sediments. *Earth
  Surface Processes and Landforms* 26, 1237-1248.
