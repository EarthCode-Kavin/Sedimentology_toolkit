"""
grainsize.plots
===============
Publication-quality figures for every analysis, plus a multi-format
`save_figure` helper (PNG 300 dpi, TIFF 300 dpi, SVG, PDF).

All figures share a consistent style set by `apply_style()`.
"""
from __future__ import annotations
import math
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, Patch
from scipy.stats import norm

from .core import phi_to_um, phi_to_mm, fmt_size
from .analyses import _smooth_curve  # reuse the tested kernel smoother

__all__ = [
    "apply_style", "save_figure",
    "fig_histogram", "fig_frequency_curve", "fig_cumulative",
    "fig_probability", "fig_passega_cm", "fig_folk_ternary", "fig_shepard_ternary",
    "FRACTION_COLORS",
]

# ----------------------------------------------------------------------
# Style
# ----------------------------------------------------------------------
def apply_style():
    plt.rcParams.update({
        "font.family": "DejaVu Sans",
        "font.size": 10,
        "axes.titlesize": 12,
        "axes.titleweight": "bold",
        "axes.labelsize": 11,
        "axes.edgecolor": "0.25",
        "axes.linewidth": 0.9,
        "xtick.labelsize": 9,
        "ytick.labelsize": 9,
        "legend.fontsize": 8.5,
        "legend.framealpha": 0.92,
        "figure.dpi": 110,
        "savefig.bbox": "tight",
    })


FRACTION_COLORS = {"gravel": "#C49464", "sand": "#F4C95D",
                   "silt": "#94BD7A", "clay": "#6FA8DC"}
_FRACTION_LIMITS = [(-np.inf, -1, "gravel"), (-1, 4, "sand"),
                    (4, 8, "silt"), (8, np.inf, "clay")]


def _fraction_for_phi(p):
    for lo, hi, name in _FRACTION_LIMITS:
        if lo <= p < hi:
            return name
    return "sand"


# ----------------------------------------------------------------------
# Multi-format export
# ----------------------------------------------------------------------
def save_figure(fig, basepath: str, formats=("png", "tiff", "svg", "pdf"), dpi=300):
    """Save one figure to several formats. Returns list of written paths."""
    written = []
    os.makedirs(os.path.dirname(basepath) or ".", exist_ok=True)
    for fmt in formats:
        path = f"{basepath}.{fmt}"
        try:
            if fmt == "tiff":
                fig.savefig(path, dpi=dpi, format="tiff",
                            pil_kwargs={"compression": "tiff_lzw"})
            elif fmt in ("svg", "pdf"):
                fig.savefig(path, format=fmt)          # vector
            else:
                fig.savefig(path, dpi=dpi, format=fmt)
            written.append(path)
        except Exception as e:                          # keep going on one bad format
            print(f"    [warn] could not write {path}: {e}")
    return written


# ----------------------------------------------------------------------
# Ternary helper
# ----------------------------------------------------------------------
def _tern_xy(sand, silt, clay):
    s = np.asarray(sand) / 100.0
    z = np.asarray(silt) / 100.0
    c = np.asarray(clay) / 100.0
    h = math.sqrt(3) / 2
    return s * 0.5 + z * 1.0 + c * 0.0, s * h


# ======================================================================
# 1. Histogram
# ======================================================================
def fig_histogram(sid, phi, freq, summary):
    apply_style()
    fig, ax = plt.subplots(figsize=(9.5, 5.6))
    dphi = float(np.median(np.diff(phi))) if len(phi) > 1 else 0.5
    colors = [FRACTION_COLORS[_fraction_for_phi(p)] for p in phi]
    bars = ax.bar(phi, freq, width=dphi * 0.92, color=colors,
                  edgecolor="0.2", linewidth=0.6, zorder=3)
    i_mode = int(np.argmax(freq))
    bars[i_mode].set_edgecolor("red"); bars[i_mode].set_linewidth(2.2)
    ymax = max(freq) * 1.2

    xlim = (phi.min() - 0.6, phi.max() + 0.6)
    ax.set_xlim(*xlim); ax.set_ylim(0, ymax)
    for lo, hi, n in [(-2, -1, "gravel"), (-1, 4, "sand"), (4, 8, "silt"), (8, 12, "clay")]:
        ax.axvspan(lo, hi, color=FRACTION_COLORS[n], alpha=0.08, zorder=0)
    for bx in (-1, 4, 8):
        if xlim[0] <= bx <= xlim[1]:
            ax.axvline(bx, color="0.5", lw=0.8, ls=":", zorder=1)

    ax.axvline(summary["mean_phi"], color="black", lw=1.5, ls="--", zorder=5,
               label=f"Mean = {summary['mean_phi']:.2f} phi ({summary['mean_um']:.0f} um)")
    ax.axvline(summary["median_phi"], color="purple", lw=1.5, ls=":", zorder=5,
               label=f"Median = {summary['median_phi']:.2f} phi")

    ax2 = ax.twiny(); ax2.set_xlim(*xlim)
    ticks = [t for t in ax.get_xticks() if xlim[0] <= t <= xlim[1]]
    ax2.set_xticks(ticks)
    ax2.set_xticklabels([fmt_size(phi_to_mm(t)) for t in ticks], fontsize=8)
    ax2.set_xlabel("Grain size (mm / um)", fontsize=9)

    ax.set_xlabel("Grain size (phi)"); ax.set_ylabel("Weight %")
    ax.set_title(f"{sid} - Grain-size histogram")
    ax.grid(True, axis="y", ls=":", lw=0.4, alpha=0.5)
    leg1 = ax.legend(loc="upper left"); ax.add_artist(leg1)
    handles = [Patch(facecolor=FRACTION_COLORS[k], edgecolor="0.3", label=k.capitalize())
               for k in ("gravel", "sand", "silt", "clay")]
    ax.legend(handles=handles, loc="upper right", title="Wentworth fraction", fontsize=8)
    fig.tight_layout()
    return fig


# ======================================================================
# 2. Frequency distribution curve
# ======================================================================
def fig_frequency_curve(sid, phi, freq, fc):
    apply_style()
    fig, ax = plt.subplots(figsize=(10, 5.4))
    phi_d, f_d = fc["phi_dense"], fc["freq_dense"]
    xmin, xmax = phi_d.min() - 0.3, phi_d.max() + 0.3
    ymax = max(f_d.max(), freq.max()) * 1.18
    for lo, hi, n in [(xmin, -1, "gravel"), (-1, 4, "sand"), (4, 8, "silt"), (8, xmax, "clay")]:
        if lo < hi:
            ax.axvspan(max(lo, xmin), min(hi, xmax), color=FRACTION_COLORS[n], alpha=0.30, zorder=0)
    dphi = float(np.median(np.diff(phi))) if len(phi) > 1 else 0.5
    ax.bar(phi, freq, width=dphi * 0.85, color="white", edgecolor="0.3",
           linewidth=0.6, alpha=0.65, zorder=2, label="Histogram")
    ax.plot(phi_d, f_d, color="#1F4E79", lw=2.2, zorder=4, label="Frequency curve")
    ax.fill_between(phi_d, 0, f_d, color="#1F4E79", alpha=0.10, zorder=3)
    for i, (mp, mf) in enumerate(fc["modes"], 1):
        ax.plot(mp, mf, "v", color="red", markersize=10, markeredgecolor="black", zorder=6)
        ax.annotate(f"Mode {i}\n{mp:.2f} phi", (mp, mf), xytext=(0, 12),
                    textcoords="offset points", ha="center", fontsize=8,
                    bbox=dict(boxstyle="round,pad=0.25", fc="white", ec="0.5"), zorder=7)
    for bx in (-1, 4, 8):
        if xmin <= bx <= xmax:
            ax.axvline(bx, color="0.4", ls=":", lw=0.8, zorder=1)
    ax.set_xlim(xmin, xmax); ax.set_ylim(0, ymax)
    ax.set_xlabel("Grain size (phi)"); ax.set_ylabel("Weight %")
    ax.set_title(f"{sid} - Frequency distribution curve ({fc['modality']})")
    ax.grid(True, ls=":", lw=0.4, alpha=0.5)
    ax.legend(loc="upper left")
    fig.tight_layout()
    return fig


# ======================================================================
# 3. Cumulative curve (arithmetic)
# ======================================================================
def fig_cumulative(sid, phi, cum, stats):
    apply_style()
    fig, ax = plt.subplots(figsize=(8.5, 5.6))
    ax.plot(phi, cum, "o-", color="#1F4E79", markersize=4, lw=1.4)
    for p in (5, 16, 25, 50, 75, 84, 95):
        pv = stats[f"phi{p}"]
        ax.plot([phi.min(), pv], [p, p], color="0.6", lw=0.5, ls=":")
        ax.plot([pv, pv], [0, p], color="0.6", lw=0.5, ls=":")
        ax.annotate(f"phi{p}", (pv, p), xytext=(3, 3), textcoords="offset points",
                    fontsize=7, color="0.4")
    ax.set_ylim(0, 100)
    ax.set_xlabel("Grain size (phi)"); ax.set_ylabel("Cumulative % finer")
    ax.set_title(f"{sid} - Cumulative curve")
    ax.grid(True, ls=":", lw=0.4, alpha=0.6)
    fig.tight_layout()
    return fig


# ======================================================================
# 4. Probability plot (Visher)
# ======================================================================
_PROB_TICKS = [0.1, 1, 5, 16, 25, 50, 75, 84, 95, 99, 99.9]
_SEG_COLOR = {"Traction": "#C0504D", "Saltation": "#4F81BD", "Suspension": "#9BBB59"}


def _seg_color(label):
    return _SEG_COLOR.get(label.split()[0], "0.5")


def fig_probability(sid, phi, cum, visher):
    apply_style()
    fig, ax = plt.subplots(figsize=(9.5, 6.6))
    z = norm.ppf(np.clip(cum, 0.1, 99.9) / 100.0)
    ax.plot(phi, z, "o", color="0.25", markersize=4, zorder=4, label="Measured points")
    for s in visher["segments"]:
        m = (phi >= s["phi_start"] - 1e-9) & (phi <= s["phi_end"] + 1e-9)
        if m.sum() >= 2:
            slope, intercept = np.polyfit(phi[m], z[m], 1)
            xl = np.array([s["phi_start"], s["phi_end"]])
            ax.plot(xl, slope * xl + intercept, "-", lw=3, color=_seg_color(s["label"]),
                    zorder=3, label=f"{s['label']}: {s['pct']:.1f}% (slope {slope:.2f})")
        ax.axvline(s["phi_end"], color="0.7", ls=":", lw=0.8, zorder=1)
    ax.set_yticks([norm.ppf(p / 100) for p in _PROB_TICKS])
    ax.set_yticklabels([str(p) for p in _PROB_TICKS])
    ax.set_ylim(norm.ppf(0.001), norm.ppf(0.999))
    ax.set_xlabel("Grain size (phi)")
    ax.set_ylabel("Cumulative % finer (probability scale)")
    ax.set_title(f"{sid} - Log-probability plot (Visher)")
    ax.grid(True, ls=":", lw=0.4, alpha=0.6)
    ax.legend(loc="lower right")
    fig.tight_layout()
    return fig


# ======================================================================
# 5. Passega C-M (single sample or whole set)
# ======================================================================
def fig_passega_cm(cm_by_sample: dict, highlight=None):
    """cm_by_sample: {sample: {'C_um','M_um','C_over_M'}}."""
    apply_style()
    fig, ax = plt.subplots(figsize=(7.2, 7.2))
    Cs = np.array([v["C_um"] for v in cm_by_sample.values()])
    Ms = np.array([v["M_um"] for v in cm_by_sample.values()])
    lo = 10 ** math.floor(math.log10(max(min(Ms.min(), Cs.min()) / 2, 0.5)))
    hi = 10 ** math.ceil(math.log10(max(Cs.max(), Ms.max()) * 2))
    ax.plot([lo, hi], [lo, hi], color="0.45", lw=1, ls="--", zorder=1)
    ax.text(hi * 0.8, hi * 0.68, "C = M", color="0.45", fontsize=9, rotation=45)
    ax.axhline(100, color="0.82", lw=0.8, zorder=0)
    sc = ax.scatter(Ms, Cs, c=np.log10([v["C_over_M"] for v in cm_by_sample.values()]),
                    cmap="viridis", s=70, edgecolor="k", linewidth=0.5, zorder=3)
    fig.colorbar(sc, ax=ax, fraction=0.046, pad=0.04, label="log10(C/M)")
    for name, v in cm_by_sample.items():
        ax.annotate(str(name), (v["M_um"], v["C_um"]), xytext=(4, 4),
                    textcoords="offset points", fontsize=7)
    ax.set_xscale("log"); ax.set_yscale("log")
    ax.set_xlim(lo, hi); ax.set_ylim(lo, hi)
    ax.set_xlabel("M - median diameter (um)")
    ax.set_ylabel("C - 1st-percentile diameter (um)")
    ax.set_title("Passega C-M diagram")
    ax.set_aspect("equal", adjustable="box")
    ax.grid(True, which="both", ls=":", lw=0.4, alpha=0.5)
    fig.tight_layout()
    return fig


# ======================================================================
# 6 & 7. Ternary diagrams
# ======================================================================
def _draw_ternary_base(ax, apex_top="SAND", left="CLAY", right="SILT"):
    h = math.sqrt(3) / 2
    ax.plot([0, 1, 0.5, 0], [0, 0, h, 0], color="black", lw=1.5, zorder=3)
    ax.text(0.5, h + 0.04, apex_top, ha="center", va="bottom", fontsize=13, fontweight="bold")
    ax.text(-0.04, -0.03, left, ha="right", va="top", fontsize=13, fontweight="bold")
    ax.text(1.04, -0.03, right, ha="left", va="top", fontsize=13, fontweight="bold")
    for pct in range(10, 100, 10):
        x1, y1 = _tern_xy(pct, 0, 100 - pct)
        ax.plot([x1, x1 - 0.012], [y1, y1 + 0.007], color="black", lw=0.8, zorder=3)
        x2, y2 = _tern_xy(pct, 100 - pct, 0)
        ax.plot([x2, x2 + 0.012], [y2, y2 + 0.007], color="black", lw=0.8, zorder=3)
        x3, y3 = _tern_xy(0, pct, 100 - pct)
        ax.plot([x3, x3], [y3, y3 - 0.012], color="black", lw=0.8, zorder=3)
    ax.set_xlim(-0.15, 1.35); ax.set_ylim(-0.10, h + 0.12)
    ax.set_aspect("equal"); ax.axis("off")


_FOLK_FIELDS = {
    "S": [(100, 0, 0), (90, 10, 0), (90, 0, 10)],
    "zS": [(90, 10, 0), (50, 50, 0), (50, 33.33, 16.67), (90, 6.67, 3.33)],
    "mS": [(90, 6.67, 3.33), (50, 33.33, 16.67), (50, 16.67, 33.33), (90, 3.33, 6.67)],
    "cS": [(90, 3.33, 6.67), (50, 16.67, 33.33), (50, 0, 50), (90, 0, 10)],
    "sZ": [(50, 50, 0), (10, 90, 0), (10, 60, 30), (50, 33.33, 16.67)],
    "sM": [(50, 33.33, 16.67), (10, 60, 30), (10, 30, 60), (50, 16.67, 33.33)],
    "sC": [(50, 16.67, 33.33), (10, 30, 60), (10, 0, 90), (50, 0, 50)],
    "Z": [(10, 90, 0), (0, 100, 0), (0, 66.67, 33.33), (10, 60, 30)],
    "M": [(10, 60, 30), (0, 66.67, 33.33), (0, 33.33, 66.67), (10, 30, 60)],
    "C": [(10, 30, 60), (0, 33.33, 66.67), (0, 0, 100), (10, 0, 90)],
}
_FOLK_COLORS = {"S": "#FFF6D4", "zS": "#FFE7A8", "mS": "#FFD27F", "cS": "#F4B36A",
                "sZ": "#D9EAD3", "sM": "#A8D4A2", "sC": "#76B47A",
                "Z": "#CFE2F3", "M": "#9FC5E8", "C": "#6FA8DC"}
_FOLK_NAMES = {"S": "Sand", "zS": "silty Sand", "mS": "muddy Sand", "cS": "clayey Sand",
               "sZ": "sandy Silt", "sM": "sandy Mud", "sC": "sandy Clay",
               "Z": "Silt", "M": "Mud", "C": "Clay"}


def fig_folk_ternary(points: list):
    """points: list of dicts with sand/silt/clay/sample/folk_code."""
    apply_style()
    fig, ax = plt.subplots(figsize=(9.5, 8.5))
    for code, verts in _FOLK_FIELDS.items():
        xy = [(_tern_xy(s, z, c)[0], _tern_xy(s, z, c)[1]) for s, z, c in verts]
        ax.add_patch(Polygon(xy, closed=True, facecolor=_FOLK_COLORS[code],
                             edgecolor="0.3", linewidth=0.7, zorder=1))
        cx, cy = np.mean([p[0] for p in xy]), np.mean([p[1] for p in xy])
        ax.text(cx, cy, code, fontsize=11, fontweight="bold", ha="center", va="center", zorder=2)
    _draw_ternary_base(ax)
    for pt in points:
        x, y = _tern_xy(pt["sand"], pt["silt"], pt["clay"])
        ax.scatter(x, y, s=80, c="red", edgecolor="black", linewidth=0.8, zorder=10)
        ax.annotate(str(pt["sample"]), (x, y), xytext=(6, 5), textcoords="offset points",
                    fontsize=7, zorder=11,
                    bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none", alpha=0.75))
    key = "Folk classes:\n" + "\n".join(f"  {c} - {n}" for c, n in _FOLK_NAMES.items())
    ax.text(1.02, math.sqrt(3) / 2 * 0.95, key, fontsize=8.5, va="top", family="monospace",
            bbox=dict(boxstyle="round,pad=0.4", fc="white", ec="0.6"))
    ax.set_title("Folk (1954) ternary - Sand-Silt-Clay")
    fig.tight_layout()
    return fig


_SHEP_FIELDS = {
    "S": [(100, 0, 0), (75, 25, 0), (75, 0, 25)],
    "Z": [(0, 100, 0), (0, 75, 25), (25, 75, 0)],
    "C": [(0, 0, 100), (25, 0, 75), (0, 25, 75)],
    "zS": [(75, 25, 0), (75, 5, 20), (40, 40, 20), (50, 50, 0)],
    "sZ": [(50, 50, 0), (40, 40, 20), (5, 75, 20), (25, 75, 0)],
    "cS": [(75, 0, 25), (75, 20, 5), (40, 20, 40), (50, 0, 50)],
    "sC": [(50, 0, 50), (40, 20, 40), (5, 20, 75), (25, 0, 75)],
    "cZ": [(0, 75, 25), (20, 75, 5), (20, 40, 40), (0, 50, 50)],
    "zC": [(0, 50, 50), (20, 40, 40), (20, 5, 75), (0, 25, 75)],
    "SZC": [(60, 20, 20), (20, 60, 20), (20, 20, 60)],
}
_SHEP_COLORS = {"S": "#FFE9A8", "Z": "#B6D7E8", "C": "#7FA9D0", "zS": "#FFD27F",
                "sZ": "#CFE2B1", "cS": "#F4B36A", "sC": "#C8B3D9", "cZ": "#A8C9B5",
                "zC": "#9FB8D6", "SZC": "#E8E1C4"}
_SHEP_NAMES = {"S": "Sand", "Z": "Silt", "C": "Clay", "zS": "Silty sand",
               "sZ": "Sandy silt", "cS": "Clayey sand", "sC": "Sandy clay",
               "cZ": "Clayey silt", "zC": "Silty clay", "SZC": "Sand-silt-clay"}


def fig_shepard_ternary(points: list):
    apply_style()
    fig, ax = plt.subplots(figsize=(10, 8.5))
    for code, verts in _SHEP_FIELDS.items():
        xy = [(_tern_xy(s, z, c)[0], _tern_xy(s, z, c)[1]) for s, z, c in verts]
        ax.add_patch(Polygon(xy, closed=True, facecolor=_SHEP_COLORS[code],
                             edgecolor="0.3", linewidth=0.7, zorder=1))
        cx, cy = np.mean([p[0] for p in xy]), np.mean([p[1] for p in xy])
        ax.text(cx, cy, code, fontsize=11, fontweight="bold", ha="center", va="center", zorder=2)
    _draw_ternary_base(ax)
    for pt in points:
        x, y = _tern_xy(pt["sand"], pt["silt"], pt["clay"])
        ax.scatter(x, y, s=80, c="red", edgecolor="black", linewidth=0.8, zorder=10)
        ax.annotate(str(pt["sample"]), (x, y), xytext=(6, 5), textcoords="offset points",
                    fontsize=7, zorder=11,
                    bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none", alpha=0.75))
    key = "Shepard classes:\n" + "\n".join(f"  {c:3s} - {n}" for c, n in _SHEP_NAMES.items())
    ax.text(1.02, math.sqrt(3) / 2 * 0.95, key, fontsize=8.5, va="top", family="monospace",
            bbox=dict(boxstyle="round,pad=0.4", fc="white", ec="0.6"))
    ax.set_title("Shepard (1954) ternary - Sand-Silt-Clay")
    fig.tight_layout()
    return fig
