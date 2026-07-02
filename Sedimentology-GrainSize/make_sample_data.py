"""
Generate 17 realistic grain-size example datasets, one per sedimentary
environment. Each CSV has multiple samples with distinct, environment-typical
distributions in the standard WIDE phi-frequency format.

Run:  python make_sample_data.py
"""
import os
import numpy as np
import pandas as pd

OUTDIR = "sample_data"
os.makedirs(OUTDIR, exist_ok=True)

PHI = np.arange(-4.0, 11.001, 0.25)   # -4 phi (16 mm) to 11 phi (~0.5 um)
rng = np.random.default_rng(42)


def gauss(mode, sd):
    g = np.exp(-0.5 * ((PHI - mode) / sd) ** 2)
    return g / g.sum()


def mix(components):
    """components: list of (mode, sd, weight)."""
    f = np.zeros_like(PHI)
    for m, sd, w in components:
        f += w * gauss(m, sd)
    s = f.sum()
    return 100 * f / s if s > 0 else f


def jitter(mode, amt=0.25):
    return mode + rng.uniform(-amt, amt)


def build(spec_fn, n_samples, prefix):
    rows = []
    for k in range(1, n_samples + 1):
        freq = spec_fn()
        # small multiplicative noise for realism
        freq = freq * (1 + rng.normal(0, 0.05, size=freq.shape))
        freq = np.clip(freq, 0, None)
        freq = 100 * freq / freq.sum()
        row = {"sample": f"{prefix}-{k:02d}"}
        row.update({f"{p:g}": round(v, 4) for p, v in zip(PHI, freq)})
        rows.append(row)
    return pd.DataFrame(rows)


# ---------------------------------------------------------------- specs
def river():        # medium sand, moderately-well sorted, minor mud tail
    return mix([(jitter(1.5), 0.55, 0.85), (jitter(4.5), 1.1, 0.12), (7, 1.2, 0.03)])

def floodplain():   # fine sand to silt, fine-skewed, mud admixture
    return mix([(jitter(3.2), 0.9, 0.55), (jitter(5.5), 1.2, 0.35), (8, 1.3, 0.10)])

def beach():        # clean medium sand, very well sorted, symmetrical
    return mix([(jitter(1.8, 0.15), 0.30, 0.99), (4.5, 0.8, 0.01)])

def dune():         # fine sand, extremely well sorted, unimodal
    return mix([(jitter(2.4, 0.15), 0.26, 0.995), (5, 0.7, 0.005)])

def delta():        # bimodal: distributary sand + prodelta mud
    return mix([(jitter(2.0), 0.6, 0.55), (jitter(6.5), 1.3, 0.45)])

def estuary():      # poorly sorted sandy mud, wide range
    return mix([(jitter(2.5), 1.0, 0.4), (jitter(5.5), 1.4, 0.35), (jitter(8), 1.4, 0.25)])

def shelf():        # very fine sand / coarse silt, well sorted
    return mix([(jitter(4.2), 0.7, 0.9), (jitter(6.5), 1.0, 0.10)])

def deep_marine():  # fine-grained clay-rich mud, unimodal fine
    return mix([(jitter(8.5), 1.0, 0.85), (jitter(6.0), 1.1, 0.15)])

def turbidite():    # broad graded suspension, poorly sorted
    return mix([(jitter(1.0), 0.7, 0.15), (jitter(4.0), 1.7, 0.72), (7.5, 0.9, 0.13)])

def glacial():      # extremely poorly sorted, gravel to clay (diamict)
    return mix([(jitter(-2.5), 1.4, 0.25), (jitter(1.5), 1.6, 0.35),
                (jitter(5), 1.8, 0.25), (jitter(8.5), 1.6, 0.15)])

def alluvial_fan(): # coarse, poorly sorted, gravelly sand
    return mix([(jitter(-2.0), 1.2, 0.35), (jitter(0.5), 1.1, 0.45), (jitter(3.5), 1.4, 0.20)])

def desert():       # aeolian fine sand, exceptionally well sorted
    return mix([(jitter(2.6, 0.15), 0.24, 0.995), (5, 0.6, 0.005)])

def bimodal():      # deliberate strong bimodality (sand + silt)
    return mix([(jitter(1.5), 0.45, 0.5), (jitter(6.0), 0.8, 0.5)])

def poorly_sorted():# very wide unimodal spread
    return mix([(jitter(3.0), 2.4, 1.0)])

def well_sorted():  # very narrow unimodal
    return mix([(jitter(2.0, 0.1), 0.22, 1.0)])

def mud_rich():     # silt + clay, no sand
    return mix([(jitter(6.5), 1.0, 0.45), (jitter(8.5), 1.1, 0.55)])

def gravel_rich():  # granule-pebble dominated, sandy matrix
    return mix([(jitter(-3.0), 1.0, 0.55), (jitter(-1.0), 0.9, 0.30), (jitter(1.5), 1.1, 0.15)])


DATASETS = [
    ("river", river, 5),
    ("floodplain", floodplain, 5),
    ("beach", beach, 5),
    ("dune", dune, 4),
    ("delta", delta, 5),
    ("estuary", estuary, 5),
    ("shelf", shelf, 4),
    ("deep_marine", deep_marine, 4),
    ("turbidite", turbidite, 5),
    ("glacial", glacial, 4),
    ("alluvial_fan", alluvial_fan, 4),
    ("desert", desert, 4),
    ("bimodal", bimodal, 4),
    ("poorly_sorted", poorly_sorted, 4),
    ("well_sorted", well_sorted, 4),
    ("mud_rich", mud_rich, 4),
    ("gravel_rich", gravel_rich, 4),
]

PREFIX = {
    "river": "RIV", "floodplain": "FPL", "beach": "BCH", "dune": "DUN",
    "delta": "DLT", "estuary": "EST", "shelf": "SHF", "deep_marine": "DMR",
    "turbidite": "TRB", "glacial": "GLC", "alluvial_fan": "ALF", "desert": "DSR",
    "bimodal": "BIM", "poorly_sorted": "PSO", "well_sorted": "WSO",
    "mud_rich": "MUD", "gravel_rich": "GRV",
}


def main():
    for name, fn, n in DATASETS:
        df = build(fn, n, PREFIX[name])
        # trim all-zero leading/trailing columns for tidiness but keep a common grid
        path = os.path.join(OUTDIR, f"{name}.csv")
        df.to_csv(path, index=False)
        print(f"  {path:38s} {n} samples")
    print(f"\n{len(DATASETS)} datasets written to {OUTDIR}/")


if __name__ == "__main__":
    main()
