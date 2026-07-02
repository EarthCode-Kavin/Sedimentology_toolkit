"""
grainsize.core
==============
Shared foundations for all grain-size analyses:
  - unit conversion (phi / mm / um)
  - flexible CSV / Excel loading (wide or long, frequency or cumulative)
  - percentile reading and Folk & Ward (1957) graphic statistics
  - Wentworth size-class naming and textural fractions

Every analysis module imports from here so behaviour is consistent.
"""
from __future__ import annotations
import os
import numpy as np
import pandas as pd

__all__ = [
    "to_phi", "phi_to_um", "phi_to_mm", "fmt_size",
    "load_grainsize", "phi_at_pct_finer", "folk_ward_stats",
    "wentworth_class", "textural_fractions", "textural_character",
    "describe_sorting", "describe_skewness", "describe_kurtosis", "describe_mean",
]

# ----------------------------------------------------------------------
# Unit conversion
# ----------------------------------------------------------------------
def to_phi(sizes, unit: str) -> np.ndarray:
    """Convert grain-size class values to phi (phi = -log2(d_mm))."""
    s = np.asarray(sizes, dtype=float)
    unit = str(unit).lower()
    if unit == "phi":
        return s
    if unit == "mm":
        return -np.log2(s)
    if unit in ("um", "µm", "micron", "microns"):
        return -np.log2(s / 1000.0)
    raise ValueError(f"Unknown size unit {unit!r} (use phi, mm or um)")


def phi_to_um(phi) -> float:
    return 1000.0 * (2.0 ** (-np.asarray(phi, dtype=float)))


def phi_to_mm(phi) -> float:
    return 2.0 ** (-np.asarray(phi, dtype=float))


def fmt_size(d_mm: float) -> str:
    """Human-friendly grain size string (mm or um)."""
    if d_mm >= 1:      return f"{d_mm:.1f} mm"
    if d_mm >= 0.1:    return f"{d_mm:.2f} mm"
    if d_mm >= 0.01:   return f"{d_mm * 1000:.0f} um"
    if d_mm >= 0.001:  return f"{d_mm * 1000:.1f} um"
    return f"{d_mm * 1000:.2f} um"


# ----------------------------------------------------------------------
# Loading
# ----------------------------------------------------------------------
def _is_number(x) -> bool:
    try:
        float(str(x))
        return True
    except (TypeError, ValueError):
        return False


def load_grainsize(path: str, layout: str = "auto", sample_col=None,
                   size_unit: str = "phi", value_type: str = "frequency") -> dict:
    """
    Load a grain-size file into {sample_id: (phi_sorted, freq_pct, cum_pct_finer)}.

    layout : 'auto' | 'wide' | 'long'
    value_type : 'frequency' (weight % per class) or 'cumulative' (% finer).
    phi is sorted ascending (coarse -> fine); freq is normalised to 100.
    """
    ext = os.path.splitext(path)[1].lower()
    df = pd.read_excel(path) if ext in (".xlsx", ".xls", ".xlsm") else pd.read_csv(path)
    df.columns = [str(c).strip() for c in df.columns]

    if layout == "auto":
        lower = [c.lower() for c in df.columns]
        has_size = any(k in lower for k in ("size", "grain", "phi", "class", "diameter"))
        has_val = any(k in lower for k in ("value", "weight", "wt", "percent", "pct", "freq", "frequency"))
        layout = "long" if (has_size and has_val) else "wide"

    samples: dict[str, tuple] = {}

    if layout == "long":
        cols = {c.lower(): c for c in df.columns}
        scol = sample_col or cols.get("sample") or cols.get("sample_id") or df.columns[0]
        size_c = next((cols[k] for k in ("size", "grain", "phi", "class", "diameter") if k in cols), None)
        val_c = next((cols[k] for k in ("value", "weight", "wt", "percent", "pct", "freq", "frequency") if k in cols), None)
        if size_c is None or val_c is None:
            raise ValueError("Long layout needs a size column and a value column.")
        for sid, g in df.groupby(scol):
            phi = to_phi(g[size_c].astype(float).values, size_unit)
            vals = g[val_c].astype(float).values
            samples[str(sid)] = _clean(phi, vals, value_type)
    else:
        scol = sample_col or df.columns[0]
        size_headers = [c for c in df.columns if c != scol and _is_number(c)]
        if not size_headers:
            raise ValueError("Wide layout: no numeric grain-size column headers found.")
        sizes = np.array([float(c) for c in size_headers])
        phi_all = to_phi(sizes, size_unit)
        for _, row in df.iterrows():
            sid = str(row[scol])
            vals = row[size_headers].astype(float).values
            samples[sid] = _clean(phi_all, vals, value_type)

    if not samples:
        raise ValueError("No samples found in the input file.")
    return samples


def _clean(phi, vals, value_type):
    phi = np.asarray(phi, float)
    vals = np.asarray(vals, float)
    mask = np.isfinite(phi) & np.isfinite(vals)
    phi, vals = phi[mask], vals[mask]
    order = np.argsort(phi)
    phi, vals = phi[order], vals[order]
    if str(value_type).lower().startswith("cum"):
        freq = np.diff(np.concatenate([[0.0], vals]))
        freq = np.clip(freq, 0, None)
    else:
        freq = np.clip(vals, 0, None)
    total = freq.sum()
    if total <= 0:
        raise ValueError("A sample has zero total weight.")
    freq = 100.0 * freq / total
    cum_finer = np.cumsum(freq)
    return phi, freq, cum_finer


# ----------------------------------------------------------------------
# Percentiles & Folk-Ward statistics
# ----------------------------------------------------------------------
def phi_at_pct_finer(phi, cum_finer, p) -> float:
    """phi value at which p percent of the sample is finer (graphic method)."""
    x, idx = np.unique(cum_finer, return_index=True)
    y = phi[idx]
    return float(np.interp(p, x, y))


def folk_ward_stats(phi, cum_finer) -> dict:
    """Folk & Ward (1957) graphic statistics in phi, with verbal descriptions."""
    p5 = phi_at_pct_finer(phi, cum_finer, 5)
    p16 = phi_at_pct_finer(phi, cum_finer, 16)
    p25 = phi_at_pct_finer(phi, cum_finer, 25)
    p50 = phi_at_pct_finer(phi, cum_finer, 50)
    p75 = phi_at_pct_finer(phi, cum_finer, 75)
    p84 = phi_at_pct_finer(phi, cum_finer, 84)
    p95 = phi_at_pct_finer(phi, cum_finer, 95)

    mean_phi = (p16 + p50 + p84) / 3.0
    sigma = (p84 - p16) / 4.0 + (p95 - p5) / 6.6
    if (p84 - p16) > 0 and (p95 - p5) > 0:
        skew = ((p16 + p84 - 2 * p50) / (2 * (p84 - p16))
                + (p5 + p95 - 2 * p50) / (2 * (p95 - p5)))
    else:
        skew = np.nan
    kurt = (p95 - p5) / (2.44 * (p75 - p25)) if (p75 - p25) > 0 else np.nan

    return {
        "phi5": p5, "phi16": p16, "phi25": p25, "phi50": p50,
        "phi75": p75, "phi84": p84, "phi95": p95,
        "mean_phi": mean_phi, "mean_um": float(phi_to_um(mean_phi)),
        "median_phi": p50, "median_um": float(phi_to_um(p50)),
        "sigma_I": sigma, "Sk_I": skew, "K_G": kurt,
        "mean_class": describe_mean(mean_phi),
        "sorting": describe_sorting(sigma),
        "skewness": describe_skewness(skew),
        "kurtosis": describe_kurtosis(kurt),
    }


# ----------------------------------------------------------------------
# Verbal descriptions
# ----------------------------------------------------------------------
def describe_mean(mz) -> str:
    if mz < -8:  return "boulder"
    if mz < -6:  return "cobble"
    if mz < -2:  return "pebble"
    if mz < -1:  return "granule"
    if mz < 0:   return "very coarse sand"
    if mz < 1:   return "coarse sand"
    if mz < 2:   return "medium sand"
    if mz < 3:   return "fine sand"
    if mz < 4:   return "very fine sand"
    if mz < 5:   return "very coarse silt"
    if mz < 6:   return "coarse silt"
    if mz < 7:   return "medium silt"
    if mz < 8:   return "fine silt"
    if mz < 9:   return "very fine silt"
    return "clay"


def describe_sorting(s) -> str:
    if not np.isfinite(s):  return "-"
    if s < 0.35:  return "very well sorted"
    if s < 0.50:  return "well sorted"
    if s < 0.70:  return "moderately well sorted"
    if s < 1.00:  return "moderately sorted"
    if s < 2.00:  return "poorly sorted"
    if s < 4.00:  return "very poorly sorted"
    return "extremely poorly sorted"


def describe_skewness(sk) -> str:
    if not np.isfinite(sk):  return "-"
    if sk < -0.30:  return "very coarse-skewed"
    if sk < -0.10:  return "coarse-skewed"
    if sk < 0.10:   return "near-symmetrical"
    if sk < 0.30:   return "fine-skewed"
    return "very fine-skewed"


def describe_kurtosis(k) -> str:
    if not np.isfinite(k):  return "-"
    if k < 0.67:  return "very platykurtic"
    if k < 0.90:  return "platykurtic"
    if k < 1.11:  return "mesokurtic"
    if k < 1.50:  return "leptokurtic"
    if k < 3.00:  return "very leptokurtic"
    return "extremely leptokurtic"


# ----------------------------------------------------------------------
# Wentworth classes & textural fractions
# ----------------------------------------------------------------------
_WENTWORTH = [
    (-8, -6, "boulder"), (-6, -2, "cobble"), (-2, -1, "granule"),
    (-1, 0, "very coarse sand"), (0, 1, "coarse sand"), (1, 2, "medium sand"),
    (2, 3, "fine sand"), (3, 4, "very fine sand"), (4, 5, "very coarse silt"),
    (5, 6, "coarse silt"), (6, 7, "medium silt"), (7, 8, "fine silt"),
    (8, 9, "very fine silt"), (9, 99, "clay"),
]


def wentworth_class(phi_value) -> str:
    for lo, hi, name in _WENTWORTH:
        if lo <= phi_value < hi:
            return name
    return "out of range"


def textural_fractions(phi, freq) -> dict:
    """Weight % gravel / sand / silt / clay (Wentworth boundaries)."""
    f = np.asarray(freq); p = np.asarray(phi)
    return {
        "gravel": float(f[p < -1].sum()),
        "sand": float(f[(p >= -1) & (p < 4)].sum()),
        "silt": float(f[(p >= 4) & (p < 8)].sum()),
        "clay": float(f[p >= 8].sum()),
    }


def textural_character(fr: dict) -> str:
    g, s, z, c = fr["gravel"], fr["sand"], fr["silt"], fr["clay"]
    mud = z + c
    parts = []
    if g >= 30:   parts.append("gravelly")
    elif g >= 5:  parts.append("slightly gravelly")
    if s >= 50 and mud < 50:
        parts.append("sand-dominated")
    elif mud >= 50 and s < 50:
        if c > z * 2:   parts.append("clay-dominated mud")
        elif z > c * 2: parts.append("silt-dominated mud")
        else:           parts.append("mud (silt+clay)")
    elif s >= 30 and mud >= 30:
        parts.append("sand-mud mixture")
    elif s >= 30:  parts.append("sandy")
    elif z >= 30:  parts.append("silty")
    elif c >= 30:  parts.append("clayey")
    return ", ".join(parts) if parts else "mixed"
