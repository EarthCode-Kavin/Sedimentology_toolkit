"""
Sedimentology-GrainSize
=======================
A complete, tested toolkit for grain-size analysis of clastic sediments.

Seven analyses (histogram, frequency curve, Folk & Ward statistics, Passega
C-M, Folk ternary, Shepard ternary, Visher log-probability) run from a single
CSV, with publication-quality figures and PDF / HTML reports.

Quick start
-----------
>>> import grainsize as gs
>>> out = gs.run_workflow("sample_data/river.csv", outdir="output")
>>> out["summary_df"].head()
"""
from .core import (
    load_grainsize, to_phi, phi_to_um, phi_to_mm, folk_ward_stats,
    wentworth_class, textural_fractions, textural_character,
)
from . import analyses, plots, report, core
from .workflow import run_workflow, analyse_sample, __version__

__all__ = [
    "run_workflow", "analyse_sample", "load_grainsize",
    "to_phi", "phi_to_um", "phi_to_mm", "folk_ward_stats",
    "wentworth_class", "textural_fractions", "textural_character",
    "analyses", "plots", "report", "core", "__version__",
]
