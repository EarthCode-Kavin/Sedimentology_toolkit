"""
grainsize.analyses
==================
The seven grain-size analyses, each as a pure function that takes loaded
sample data and returns a result dict (numbers only; plotting is separate).

  1. histogram_summary      - modal class, mean/median, fractions
  2. frequency_curve        - smooth curve + mode detection (uni/bi/polymodal)
  3. statistics             - Folk & Ward graphic statistics (from core)
  4. passega_cm             - C (1st pct) and M (median), transport mechanism
  5. folk_ternary           - Folk (1954) sand-silt-clay class
  6. shepard_ternary        - Shepard (1954) sand-silt-clay class
  7. visher_populations     - log-probability transport-population segmentation
"""
from __future__ import annotations
import math
import numpy as np
from scipy.signal import find_peaks
from scipy.stats import norm

from .core import (
    phi_to_um, phi_at_pct_finer, folk_ward_stats,
    wentworth_class, textural_fractions, textural_character,
)

__all__ = [
    "histogram_summary", "frequency_curve", "statistics",
    "passega_cm", "folk_ternary", "shepard_ternary", "visher_populations",
    "SEGMENT_TABLE",
]


# ======================================================================
# 1. Histogram summary
# ======================================================================
def histogram_summary(phi, freq, cum) -> dict:
    p50 = phi_at_pct_finer(phi, cum, 50)
    p16 = phi_at_pct_finer(phi, cum, 16)
    p84 = phi_at_pct_finer(phi, cum, 84)
    mean_phi = (p16 + p50 + p84) / 3.0
    i_mode = int(np.argmax(freq))
    fr = textural_fractions(phi, freq)
    return {
        "mean_phi": mean_phi, "mean_um": float(phi_to_um(mean_phi)),
        "median_phi": p50, "median_um": float(phi_to_um(p50)),
        "mode_phi": float(phi[i_mode]), "mode_um": float(phi_to_um(phi[i_mode])),
        "mode_pct": float(freq[i_mode]), "mode_class": wentworth_class(phi[i_mode]),
        "mean_class": wentworth_class(mean_phi),
        "fractions": fr, "texture": textural_character(fr),
    }


# ======================================================================
# 2. Frequency distribution curve + mode detection
# ======================================================================
def _smooth_curve(phi, freq, bandwidth=0.5, n_out=400):
    if len(phi) < 2:
        return np.asarray(phi, float), np.asarray(freq, float)
    dphi = float(np.median(np.diff(phi)))
    phi_dense = np.linspace(phi.min() - 0.5, phi.max() + 0.5, n_out)
    f_dense = np.zeros_like(phi_dense)
    norm_c = 1.0 / (bandwidth * np.sqrt(2 * np.pi))
    for p, w in zip(phi, freq):
        if w <= 0:
            continue
        f_dense += w * norm_c * np.exp(-0.5 * ((phi_dense - p) / bandwidth) ** 2)
    return phi_dense, f_dense * dphi


def _modality(n):
    return {0: "no clear mode", 1: "unimodal", 2: "bimodal",
            3: "trimodal"}.get(n, "polymodal")


def frequency_curve(phi, freq, bandwidth=0.5, min_height=2.0, min_prominence=1.0):
    phi_d, f_d = _smooth_curve(phi, freq, bandwidth)
    peaks, _ = find_peaks(f_d, height=min_height, prominence=min_prominence)
    modes = [(float(phi_d[i]), float(f_d[i])) for i in peaks]
    if modes:
        prim = max(modes, key=lambda m: m[1])
    else:
        prim = (float(phi[int(np.argmax(freq))]), float(freq.max()))
    fr = textural_fractions(phi, freq)
    return {
        "phi_dense": phi_d, "freq_dense": f_d,
        "modes": modes, "n_modes": len(modes),
        "modality": _modality(len(modes)),
        "modes_phi": [round(m[0], 2) for m in modes],
        "modes_um": [round(float(phi_to_um(m[0]))) for m in modes],
        "primary_mode_phi": prim[0], "primary_mode_um": float(phi_to_um(prim[0])),
        "primary_class": wentworth_class(prim[0]),
        "fractions": fr, "texture": textural_character(fr),
    }


# ======================================================================
# 3. Statistics (Folk & Ward) - thin wrapper around core
# ======================================================================
def statistics(phi, freq, cum) -> dict:
    return folk_ward_stats(phi, cum)


# ======================================================================
# 4. Passega C-M
# ======================================================================
def _phi_at_pct_coarser(phi, freq, p):
    cum_coarser = np.cumsum(freq)
    x, idx = np.unique(cum_coarser, return_index=True)
    y = phi[idx]
    return float(np.interp(p, x, y))


def passega_cm(phi, freq, cum) -> dict:
    phi_C = _phi_at_pct_coarser(phi, freq, 1.0)
    phi_M = _phi_at_pct_coarser(phi, freq, 50.0)
    C = float(phi_to_um(phi_C))
    M = float(phi_to_um(phi_M))
    r = C / M if M > 0 else np.inf
    if r < 3.0:
        if C < 100:
            mech = "Uniform / pelagic suspension"
        else:
            mech = "Uniform suspension / sorted traction"
    elif r < 12.0:
        mech = "Graded suspension"
    else:
        mech = "Rolling + suspension (bottom transport)"
    return {"C_um": C, "M_um": M, "phi_C": phi_C, "phi_M": phi_M,
            "C_over_M": r, "mechanism": mech}


# ======================================================================
# 5. Folk (1954) ternary classification
# ======================================================================
def folk_ternary(fractions: dict) -> dict:
    """Folk sand-silt-clay class from the (already gravel-free) fractions."""
    s, z, c = _renorm_ssc(fractions)
    sz = z / c if c > 0 else np.inf
    if s >= 90:
        code, name = "S", "Sand"
    elif s >= 50:
        if sz > 2:    code, name = "zS", "silty Sand"
        elif sz < 0.5: code, name = "cS", "clayey Sand"
        else:          code, name = "mS", "muddy Sand"
    elif s >= 10:
        if sz > 2:    code, name = "sZ", "sandy Silt"
        elif sz < 0.5: code, name = "sC", "sandy Clay"
        else:          code, name = "sM", "sandy Mud"
    else:
        if sz > 2:    code, name = "Z", "Silt"
        elif sz < 0.5: code, name = "C", "Clay"
        else:          code, name = "M", "Mud"
    return {"sand": s, "silt": z, "clay": c, "folk_code": code, "folk_class": name}


# ======================================================================
# 6. Shepard (1954) ternary classification
# ======================================================================
def shepard_ternary(fractions: dict) -> dict:
    s, z, c = _renorm_ssc(fractions)
    if s >= 75:  code, name = "S", "Sand"
    elif z >= 75: code, name = "Z", "Silt"
    elif c >= 75: code, name = "C", "Clay"
    elif c < 20:
        code, name = ("zS", "Silty sand") if s >= z else ("sZ", "Sandy silt")
    elif z < 20:
        code, name = ("cS", "Clayey sand") if s >= c else ("sC", "Sandy clay")
    elif s < 20:
        code, name = ("cZ", "Clayey silt") if z >= c else ("zC", "Silty clay")
    else:
        code, name = "SZC", "Sand-silt-clay"
    return {"sand": s, "silt": z, "clay": c, "shepard_code": code, "shepard_class": name}


def _renorm_ssc(fr):
    """Renormalise sand/silt/clay to 100 % (drop gravel)."""
    s, z, c = fr["sand"], fr["silt"], fr["clay"]
    tot = s + z + c
    if tot <= 0:
        return 0.0, 0.0, 0.0
    return 100 * s / tot, 100 * z / tot, 100 * c / tot


# ======================================================================
# 7. Visher log-probability transport populations
# ======================================================================
SEGMENT_TABLE = [
    ("Traction", "Rolling / sliding along the bed", "coarse end, 1-15%"),
    ("Saltation", "Bouncing along the bed", "dominant middle, 50-95%"),
    ("Suspension", "Carried in the water column", "fine end, 5-40%"),
]


def _cum_to_z(cum_pct):
    p = np.clip(cum_pct, 0.1, 99.9) / 100.0
    return norm.ppf(p)


def _segment_ssr(x, y, i, j):
    if j - i < 1:
        return 0.0
    xs, ys = x[i:j + 1], y[i:j + 1]
    n = len(xs)
    sx, sy = xs.sum(), ys.sum()
    sxx, sxy = (xs * xs).sum(), (xs * ys).sum()
    denom = n * sxx - sx * sx
    if abs(denom) < 1e-12:
        return float(np.var(ys) * n)
    slope = (n * sxy - sx * sy) / denom
    intercept = (sy - slope * sx) / n
    return float(((ys - (slope * xs + intercept)) ** 2).sum())


def _fit_piecewise(x, y, max_segments=4, min_seg_size=3):
    n = len(x)
    if n < 2:
        return []
    INF = float("inf")
    max_k = min(max_segments, max(1, n // max(min_seg_size, 1)))
    seg_cost = np.full((n, n), INF)
    for i in range(n):
        for j in range(i + min_seg_size - 1, n):
            seg_cost[i, j] = _segment_ssr(x, y, i, j)
    dp_cost = np.full((max_k + 1, n), INF)
    dp_split = np.full((max_k + 1, n), -1, dtype=int)
    for j in range(min_seg_size - 1, n):
        dp_cost[1, j] = seg_cost[0, j]
    for k in range(2, max_k + 1):
        for j in range(k * min_seg_size - 1, n):
            best, best_i = INF, -1
            for i in range((k - 1) * min_seg_size, j - min_seg_size + 2):
                c = dp_cost[k - 1, i - 1] + seg_cost[i, j]
                if c < best:
                    best, best_i = c, i
            dp_cost[k, j] = best
            dp_split[k, j] = best_i

    def bic(k):
        ssr = dp_cost[k, n - 1]
        if not np.isfinite(ssr) or ssr <= 0:
            ssr = 1e-12
        return n * math.log(ssr / n) + 3 * k * math.log(max(n, 2))

    best_k, best_bic = 1, bic(1)
    for k in range(2, max_k + 1):
        b = bic(k)
        if b < best_bic - 1e-6:
            best_bic, best_k = b, k

    segs = []
    j = n - 1
    for k in range(best_k, 0, -1):
        i = 0 if k == 1 else dp_split[k, j]
        xs, ys = x[i:j + 1], y[i:j + 1]
        slope, intercept = (np.polyfit(xs, ys, 1) if len(xs) >= 2 else (0.0, ys[0] if len(ys) else 0.0))
        segs.append((int(i), int(j), float(slope), float(intercept), int(j - i + 1)))
        j = i - 1
        if j < 0:
            break
    segs.reverse()
    return segs


def _label_visher(phi, cum, segs, min_fraction_pct=2.0):
    if not segs:
        return []
    seg_pct = []
    for i, j, *_ in segs:
        pct = float(cum[j]) if i == 0 else float(cum[j] - cum[i - 1])
        seg_pct.append(max(pct, 0.0))
    dominant = int(np.argmax(seg_pct))
    raw = []
    for k, (i, j, slope, intercept, npts) in enumerate(segs):
        base = "Traction" if k < dominant else ("Saltation" if k == dominant else "Suspension")
        raw.append({"segment": k + 1, "base": base,
                    "phi_start": float(phi[i]), "phi_end": float(phi[j]),
                    "um_start": float(phi_to_um(phi[i])), "um_end": float(phi_to_um(phi[j])),
                    "slope": slope, "n_points": npts, "pct": seg_pct[k]})
    merged = []
    for s in raw:
        if s["pct"] < min_fraction_pct and merged:
            prev = merged[-1]
            prev["pct"] += s["pct"]; prev["phi_end"] = s["phi_end"]; prev["um_end"] = s["um_end"]
            continue
        s["label"] = s["base"]
        merged.append(dict(s))
    bases = [s["label"] for s in merged]
    counts = {b: bases.count(b) for b in set(bases)}
    running = {}
    for s in merged:
        b = s["label"]
        running[b] = running.get(b, 0) + 1
        if counts[b] > 1:
            s["label"] = f"{b} {running[b]}"
    return merged


def _infer_environment(segs):
    if not segs:
        return "unclassified"
    bases = [s["label"].split()[0] for s in segs]
    salt = sum(s["pct"] for s in segs if s["label"].startswith("Saltation"))
    susp = sum(s["pct"] for s in segs if s["label"].startswith("Suspension"))
    trac = sum(s["pct"] for s in segs if s["label"].startswith("Traction"))
    salt_slopes = [s["slope"] for s in segs if s["label"].startswith("Saltation")]
    dom_slope = max(salt_slopes) if salt_slopes else 0.0
    salt_seg = next((s for s in segs if s["label"].startswith("Saltation")), None)
    salt_w = (salt_seg["phi_end"] - salt_seg["phi_start"]) if salt_seg else 0.0
    n_salt = sum(1 for b in bases if b == "Saltation")
    n_trac = sum(1 for b in bases if b == "Traction")
    n_susp = sum(1 for b in bases if b == "Suspension")

    if salt > 85 and dom_slope > 3.0 and salt_w < 1.5 and trac < 5:
        return "Aeolian dune sand - exceptional saltation sorting"
    if salt > 80 and dom_slope > 2.0 and salt_w < 2.0 and susp < 15:
        return "Beach / swash-zone sand - sharp saltation truncation"
    if salt > 40 and salt_w > 2.5 and dom_slope < 0.8:
        return "Turbidite / graded-suspension deposit"
    if n_salt >= 2 and salt > 60:
        return "Tidal-channel sand - two saltation populations"
    if n_trac >= 1 and n_salt == 1 and n_susp >= 1 and 1 <= trac <= 15 and salt >= 50:
        return "Fluvial channel sand - full rolling + saltation + suspension"
    if susp > 70:
        return "Distal / suspension-dominated deposit"
    parts = []
    if trac > 0: parts.append(f"traction {trac:.0f}%")
    if salt > 0: parts.append(f"saltation {salt:.0f}%")
    if susp > 0: parts.append(f"suspension {susp:.0f}%")
    return "Mixed transport - " + ", ".join(parts)


def visher_populations(phi, freq, cum, max_segments=4, min_seg_size=3,
                       min_fraction_pct=2.0) -> dict:
    z = _cum_to_z(cum)
    keep = (cum > 0.5) & (cum < 99.5)
    if keep.sum() >= 2 * min_seg_size:
        phi_fit, z_fit = phi[keep], z[keep]
        fit_to_full = np.where(keep)[0]
    else:
        phi_fit, z_fit = phi, z
        fit_to_full = np.arange(len(phi))
    segs_raw = _fit_piecewise(phi_fit, z_fit, max_segments, min_seg_size)
    segs_full = [(int(fit_to_full[i]), int(fit_to_full[j]), sl, ic, npts)
                 for (i, j, sl, ic, npts) in segs_raw]
    segs = _label_visher(phi, cum, segs_full, min_fraction_pct)
    return {"segments": segs, "n_segments": len(segs),
            "environment": _infer_environment(segs)}
