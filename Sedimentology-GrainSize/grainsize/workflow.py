"""
grainsize.workflow
==================
The master orchestrator. `run_workflow(csv)` loads a grain-size file, runs
all seven analyses on every sample, writes figures (multi-format), summary
CSVs, and PDF + HTML reports.
"""
from __future__ import annotations
import os
import datetime
import numpy as np
import pandas as pd

from . import core, analyses, plots, report

__version__ = "1.0.0"

ANALYSIS_ORDER = [
    "histogram", "frequency_curve", "statistics",
    "passega_cm", "folk_ternary", "shepard_ternary", "visher",
]


def analyse_sample(phi, freq, cum) -> dict:
    """Run all seven analyses on a single sample -> nested result dict."""
    stats = analyses.statistics(phi, freq, cum)
    hist = analyses.histogram_summary(phi, freq, cum)
    fc = analyses.frequency_curve(phi, freq)
    cm = analyses.passega_cm(phi, freq, cum)
    fr = hist["fractions"]
    folk = analyses.folk_ternary(fr)
    shep = analyses.shepard_ternary(fr)
    vish = analyses.visher_populations(phi, freq, cum)
    return {"stats": stats, "histogram": hist, "frequency_curve": fc,
            "passega_cm": cm, "folk": folk, "shepard": shep, "visher": vish,
            "fractions": fr}


def _interpret(res: dict) -> str:
    """One-paragraph sedimentological interpretation from the results."""
    s = res["stats"]; h = res["histogram"]; cm = res["passega_cm"]
    folk = res["folk"]; vish = res["visher"]; fc = res["frequency_curve"]
    return (
        f"The sample is a {folk['folk_class'].lower()} "
        f"(Folk 1954; Shepard: {res['shepard']['shepard_class'].lower()}), "
        f"with a graphic mean of {s['mean_phi']:.2f} phi ({s['mean_um']:.0f} um, "
        f"{s['mean_class']}) and is {s['sorting']}, {s['skewness']}, and "
        f"{s['kurtosis']}. The distribution is {fc['modality']} with a primary "
        f"mode at {fc['primary_mode_phi']:.2f} phi. On the Passega C-M diagram "
        f"the sample plots with C = {cm['C_um']:.0f} um and M = {cm['M_um']:.0f} um "
        f"(C/M = {cm['C_over_M']:.1f}), indicating {cm['mechanism'].lower()}. "
        f"Log-probability segmentation suggests: {vish['environment']}."
    )


def run_workflow(csv_path: str, outdir: str = "output",
                 size_unit: str = "phi", value_type: str = "frequency",
                 layout: str = "auto", figure_formats=("png", "tiff", "svg", "pdf"),
                 make_reports: bool = True, verbose: bool = True) -> dict:
    """
    Full pipeline. Returns a dict with 'results' (per-sample), 'summary_df',
    and 'paths' (written files).
    """
    t0 = datetime.datetime.now()
    dataset = os.path.splitext(os.path.basename(csv_path))[0]

    fig_dir = os.path.join(outdir, "figures", dataset)
    csv_dir = os.path.join(outdir, "csv")
    rep_dir = os.path.join(outdir, "reports")
    html_dir = os.path.join(outdir, "html")
    for d in (fig_dir, csv_dir, rep_dir, html_dir):
        os.makedirs(d, exist_ok=True)

    samples = core.load_grainsize(csv_path, layout, None, size_unit, value_type)
    if verbose:
        print(f"[{dataset}] {len(samples)} samples loaded")

    results = {}
    summary_rows = []
    written = []
    cm_by_sample = {}
    folk_points, shep_points = [], []

    import matplotlib.pyplot as plt

    for sid, (phi, freq, cum) in samples.items():
        res = analyse_sample(phi, freq, cum)
        res["interpretation"] = _interpret(res)
        results[sid] = res
        cm_by_sample[sid] = res["passega_cm"]
        folk_points.append({"sample": sid, **res["folk"]})
        shep_points.append({"sample": sid, **res["shepard"]})

        # --- per-sample figures ---
        safe = sid.replace("/", "_").replace(" ", "_")
        figmap = {
            "histogram": plots.fig_histogram(sid, phi, freq, res["histogram"]),
            "frequency_curve": plots.fig_frequency_curve(sid, phi, freq, res["frequency_curve"]),
            "cumulative": plots.fig_cumulative(sid, phi, cum, res["stats"]),
            "probability": plots.fig_probability(sid, phi, cum, res["visher"]),
        }
        res["_figures"] = {}
        for kind, fig in figmap.items():
            base = os.path.join(fig_dir, f"{safe}_{kind}")
            paths = plots.save_figure(fig, base, formats=figure_formats)
            written += paths
            # remember the PNG for report embedding
            png = next((p for p in paths if p.endswith(".png")), None)
            res["_figures"][kind] = png
            plt.close(fig)

        # --- summary row ---
        st, h, cm = res["stats"], res["histogram"], res["passega_cm"]
        fr = res["fractions"]
        summary_rows.append({
            "sample": sid,
            "mean_phi": round(st["mean_phi"], 2), "mean_um": round(st["mean_um"]),
            "mean_class": st["mean_class"],
            "median_phi": round(st["median_phi"], 2),
            "sorting_sigma": round(st["sigma_I"], 2), "sorting": st["sorting"],
            "skewness_Sk": round(st["Sk_I"], 2), "skewness": st["skewness"],
            "kurtosis_KG": round(st["K_G"], 2), "kurtosis": st["kurtosis"],
            "modality": res["frequency_curve"]["modality"],
            "C_um": round(cm["C_um"]), "M_um": round(cm["M_um"]),
            "C_over_M": round(cm["C_over_M"], 1),
            "transport": cm["mechanism"],
            "gravel_pct": round(fr["gravel"], 1), "sand_pct": round(fr["sand"], 1),
            "silt_pct": round(fr["silt"], 1), "clay_pct": round(fr["clay"], 1),
            "folk_class": res["folk"]["folk_class"],
            "shepard_class": res["shepard"]["shepard_class"],
            "visher_environment": res["visher"]["environment"],
        })

    # --- dataset-level figures (ternaries + C-M) ---
    ds_figs = {
        "passega_cm": plots.fig_passega_cm(cm_by_sample),
        "folk_ternary": plots.fig_folk_ternary(folk_points),
        "shepard_ternary": plots.fig_shepard_ternary(shep_points),
    }
    dataset_figure_paths = {}
    for kind, fig in ds_figs.items():
        base = os.path.join(fig_dir, f"_{dataset}_{kind}")
        paths = plots.save_figure(fig, base, formats=figure_formats)
        written += paths
        dataset_figure_paths[kind] = next((p for p in paths if p.endswith(".png")), None)
        plt.close(fig)

    # --- summary CSV ---
    summary_df = pd.DataFrame(summary_rows)
    summary_csv = os.path.join(csv_dir, f"{dataset}_summary.csv")
    summary_df.to_csv(summary_csv, index=False)
    written.append(summary_csv)

    # --- segment-level CSV (Visher) ---
    seg_rows = []
    for sid, res in results.items():
        for s in res["visher"]["segments"]:
            seg_rows.append({"sample": sid, **{k: s[k] for k in
                             ("label", "phi_start", "phi_end", "pct", "slope")}})
    if seg_rows:
        seg_csv = os.path.join(csv_dir, f"{dataset}_visher_segments.csv")
        pd.DataFrame(seg_rows).to_csv(seg_csv, index=False)
        written.append(seg_csv)

    elapsed = (datetime.datetime.now() - t0).total_seconds()
    meta = {"dataset": dataset, "n_samples": len(samples),
            "date": t0.strftime("%Y-%m-%d %H:%M"), "version": __version__,
            "elapsed_s": round(elapsed, 1)}

    # --- reports ---
    if make_reports:
        html_path = os.path.join(html_dir, f"{dataset}_report.html")
        report.write_html(html_path, dataset, results, summary_df,
                          dataset_figure_paths, meta)
        written.append(html_path)
        pdf_path = os.path.join(rep_dir, f"{dataset}_report.pdf")
        try:
            report.write_pdf(pdf_path, dataset, results, summary_df,
                            dataset_figure_paths, meta)
            written.append(pdf_path)
        except Exception as e:
            if verbose:
                print(f"  [warn] PDF report skipped: {e}")

    if verbose:
        print(f"[{dataset}] done in {elapsed:.1f}s -> {len(written)} files")

    return {"results": results, "summary_df": summary_df,
            "dataset_figures": dataset_figure_paths, "paths": written, "meta": meta}
