"""
Test suite for Sedimentology-GrainSize.
Run:  pytest -q     (from the repository root)

Covers: unit conversion, loading (wide/long/cumulative/units), every analysis,
figure generation + multi-format export, and the full workflow on all
bundled datasets.
"""
import os
import glob
import math
import numpy as np
import pandas as pd
import pytest

import grainsize as gs
from grainsize import core, analyses, plots

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SAMPLE_DIR = os.path.join(HERE, "sample_data")
ALL_CSVS = sorted(glob.glob(os.path.join(SAMPLE_DIR, "*.csv")))


# ---------------------------------------------------------------- units
def test_phi_roundtrip():
    assert core.phi_to_um(0) == pytest.approx(1000.0)
    assert core.to_phi([1.0], "mm")[0] == pytest.approx(0.0)
    assert core.to_phi([1000.0], "um")[0] == pytest.approx(0.0)
    assert core.phi_to_um(1) == pytest.approx(500.0)


def test_unit_equivalence():
    # 2 mm == -1 phi == 2000 um
    assert core.to_phi([2.0], "mm")[0] == pytest.approx(-1.0)
    assert core.to_phi([2000.0], "um")[0] == pytest.approx(-1.0)


# ---------------------------------------------------------------- loading
@pytest.fixture(scope="module")
def river_samples():
    return core.load_grainsize(os.path.join(SAMPLE_DIR, "river.csv"))


def test_load_wide(river_samples):
    assert len(river_samples) >= 1
    for sid, (phi, freq, cum) in river_samples.items():
        assert np.all(np.diff(phi) > 0)          # sorted ascending
        assert freq.sum() == pytest.approx(100.0, abs=1e-6)
        assert cum[-1] == pytest.approx(100.0, abs=1e-6)


def test_load_long_equivalence(tmp_path):
    # Build a wide file, convert to long, check identical stats
    wide = pd.read_csv(os.path.join(SAMPLE_DIR, "beach.csv"))
    size_cols = [c for c in wide.columns if c != "sample"]
    long_rows = []
    for _, row in wide.iterrows():
        for c in size_cols:
            long_rows.append({"sample": row["sample"], "size": float(c), "value": row[c]})
    long_path = tmp_path / "long.csv"
    pd.DataFrame(long_rows).to_csv(long_path, index=False)

    w = core.load_grainsize(os.path.join(SAMPLE_DIR, "beach.csv"))
    l = core.load_grainsize(str(long_path))
    assert set(w) == set(l)
    for sid in w:
        assert np.allclose(w[sid][1], l[sid][1], atol=1e-6)


def test_load_cumulative_equivalence(tmp_path):
    wide = pd.read_csv(os.path.join(SAMPLE_DIR, "river.csv"))
    size_cols = [c for c in wide.columns if c != "sample"]
    cum = wide.copy()
    cum[size_cols] = wide[size_cols].cumsum(axis=1)
    cpath = tmp_path / "cum.csv"
    cum.to_csv(cpath, index=False)

    a = core.load_grainsize(os.path.join(SAMPLE_DIR, "river.csv"))
    b = core.load_grainsize(str(cpath), value_type="cumulative")
    for sid in a:
        assert a[sid][1] == pytest.approx(b[sid][1], abs=1e-4)


# ---------------------------------------------------------------- analyses
def test_statistics(river_samples):
    for sid, (phi, freq, cum) in river_samples.items():
        st = analyses.statistics(phi, freq, cum)
        assert np.isfinite(st["mean_phi"])
        assert st["sigma_I"] >= 0
        assert st["sorting"] in (
            "very well sorted", "well sorted", "moderately well sorted",
            "moderately sorted", "poorly sorted", "very poorly sorted",
            "extremely poorly sorted")


def test_passega_cm_ordering(river_samples):
    for sid, (phi, freq, cum) in river_samples.items():
        cm = analyses.passega_cm(phi, freq, cum)
        assert cm["C_um"] >= cm["M_um"]          # C is always >= M
        assert cm["C_over_M"] >= 1.0


def test_ternary_classes(river_samples):
    for sid, (phi, freq, cum) in river_samples.items():
        fr = core.textural_fractions(phi, freq)
        folk = analyses.folk_ternary(fr)
        shep = analyses.shepard_ternary(fr)
        assert folk["folk_code"] in {"S","zS","mS","cS","sZ","sM","sC","Z","M","C"}
        assert shep["shepard_code"] in {"S","Z","C","zS","sZ","cS","sC","cZ","zC","SZC"}
        # fractions renormalised to 100
        assert folk["sand"] + folk["silt"] + folk["clay"] == pytest.approx(100, abs=1e-3)


def test_frequency_curve_modes(river_samples):
    for sid, (phi, freq, cum) in river_samples.items():
        fc = analyses.frequency_curve(phi, freq)
        assert fc["n_modes"] >= 1
        assert fc["modality"] in ("unimodal","bimodal","trimodal","polymodal","no clear mode")


def test_visher_segments(river_samples):
    for sid, (phi, freq, cum) in river_samples.items():
        v = analyses.visher_populations(phi, freq, cum)
        assert v["n_segments"] >= 1
        assert sum(s["pct"] for s in v["segments"]) == pytest.approx(100, abs=5)


def test_bimodal_detected():
    s = core.load_grainsize(os.path.join(SAMPLE_DIR, "bimodal.csv"))
    modalities = [analyses.frequency_curve(p, f)["modality"]
                  for p, f, c in s.values()]
    assert any(m == "bimodal" for m in modalities)


def test_well_sorted_is_well_sorted():
    s = core.load_grainsize(os.path.join(SAMPLE_DIR, "well_sorted.csv"))
    for p, f, c in s.values():
        st = analyses.statistics(p, f, c)
        assert "well sorted" in st["sorting"]


# ---------------------------------------------------------------- plots
def test_figures_and_export(tmp_path, river_samples):
    sid, (phi, freq, cum) = next(iter(river_samples.items()))
    st = analyses.statistics(phi, freq, cum)
    hsum = analyses.histogram_summary(phi, freq, cum)
    fig = plots.fig_histogram(sid, phi, freq, hsum)
    base = str(tmp_path / "hist")
    written = plots.save_figure(fig, base, formats=("png", "svg", "pdf"))
    assert any(w.endswith(".png") for w in written)
    assert all(os.path.exists(w) for w in written)


# ---------------------------------------------------------------- workflow
@pytest.mark.parametrize("csv", ALL_CSVS, ids=[os.path.basename(c) for c in ALL_CSVS])
def test_workflow_runs_on_every_dataset(csv, tmp_path):
    out = gs.run_workflow(csv, outdir=str(tmp_path),
                          figure_formats=("png",), make_reports=False, verbose=False)
    df = out["summary_df"]
    assert len(df) >= 1
    assert "folk_class" in df.columns
    assert df["mean_phi"].notna().all()


def test_workflow_reports(tmp_path):
    out = gs.run_workflow(os.path.join(SAMPLE_DIR, "beach.csv"),
                          outdir=str(tmp_path), figure_formats=("png",),
                          make_reports=True, verbose=False)
    dataset = out["meta"]["dataset"]
    assert os.path.exists(os.path.join(str(tmp_path), "html", f"{dataset}_report.html"))
    # PDF is best-effort; assert it exists since reportlab is a dependency
    assert os.path.exists(os.path.join(str(tmp_path), "reports", f"{dataset}_report.pdf"))
