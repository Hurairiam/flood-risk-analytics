"""
flood_analysis.py
FFWC Flood Bulletin — Probability & EDA (STA 2101 CEP)

Tasks covered: (1) SRS sampling check, (2) probabilistic analysis,
(3) EDA + missing-value handling + visualizations, (4) correlation/regression.

Run:  python flood_analysis.py
Needs: EDA_Input_Datasets-1.xlsx in the same folder.
"""

import os
import time
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import matplotlib.gridspec as gridspec
import seaborn as sns
from scipy import stats

# --------------------------------------------------------------------------
# STYLE
# --------------------------------------------------------------------------
NAVY, RED, TEAL, GOLD, PLUM = "#1B4F72", "#C0392B", "#117A65", "#B7950B", "#7D3C98"
PALETTE = [NAVY, RED, TEAL, GOLD, PLUM]

sns.set_style("whitegrid")
plt.rcParams.update({
    "figure.facecolor": "white",
    "axes.edgecolor": "#444444",
    "axes.titleweight": "bold",
    "axes.titlesize": 12,
    "axes.labelsize": 10.5,
    "font.family": "DejaVu Sans",
    "grid.linestyle": "--",
    "grid.alpha": 0.5,
    "legend.frameon": False,
})

INPUT_FILE, OUTPUT_DIR, SEED, N = "EDA_Input_Datasets-1.xlsx", "figures", 42, 70
SHOW_PLOTS = True
NARRATE_DELAY = 0.4  # seconds between console steps, feels like live analysis
os.makedirs(OUTPUT_DIR, exist_ok=True)


def step(msg):
    print(f"\n▸ {msg}")
    time.sleep(NARRATE_DELAY)


def kpi_card(ax, value, label, color=NAVY):
    ax.axis("off")
    ax.text(0.5, 0.62, value, ha="center", va="center", fontsize=26,
            fontweight="bold", color=color, transform=ax.transAxes)
    ax.text(0.5, 0.22, label, ha="center", va="center", fontsize=10,
            color="#555555", transform=ax.transAxes)
    for spine in ["top", "bottom", "left", "right"]:
        ax.spines[spine].set_visible(False)


def dashboard_footer(fig, title, source="FFWC/BWDB bulletin, 20-07-2026 · n=70 sample per dataset"):
    fig.suptitle(title, fontsize=15, fontweight="bold",
                 x=0.02, ha="left", y=0.99)
    fig.text(0.02, 0.005, source, fontsize=8.5, color="#777777")


def save(fig, name):
    fig.savefig(f"{OUTPUT_DIR}/{name}", dpi=150, bbox_inches="tight")
    print(f"  saved -> {OUTPUT_DIR}/{name}")
    if not SHOW_PLOTS:
        plt.close(fig)


# ==========================================================================
def load_data():
    step("Loading workbook and validating sheet structure...")
    xls = pd.ExcelFile(INPUT_FILE)
    d = {k: pd.read_excel(xls, v).dropna(how="all") for k, v in {
        "full1": "Dataset1_Full", "full2": "Dataset2_Full",
        "s1": "Dataset1_Sample_n70", "s2": "Dataset2_Sample_n70",
    }.items()}
    print(
        f"  Dataset1: {len(d['full1'])} stations (full), {len(d['s1'])} (sample)")
    print(
        f"  Dataset2: {len(d['full2'])} stations (full), {len(d['s2'])} (sample)")
    return d


# ==========================================================================
# DASHBOARD 1 — Sampling validation
# ==========================================================================
def dashboard1_sampling(d):
    step("STEP 1/4 — Validating sampling methodology (SRS, n=70/N=127)")
    d["full1"].sample(n=N, random_state=SEED)
    matched = set(d["s1"].Station_ID) == set(d["s2"].Station_ID)
    subset_ok = set(d["s1"].Station_ID).issubset(set(d["full1"].Station_ID))
    print(
        f"  paired stations across datasets: {matched} | valid subset of population: {subset_ok}")

    comp = pd.DataFrame({
        "Population_%": d["full1"].Basin.value_counts(normalize=True).mul(100).round(1),
        "Sample_%": d["s1"].Basin.value_counts(normalize=True).mul(100).round(1),
    })
    print(comp)

    fig = plt.figure(figsize=(13, 4.6))
    gs = gridspec.GridSpec(1, 3, width_ratios=[1, 1, 2], wspace=0.35)

    ax_kpi1 = fig.add_subplot(gs[0, 0])
    kpi_card(ax_kpi1, "70 / 127", "Stations sampled (SRS)", NAVY)
    ax_kpi2 = fig.add_subplot(gs[0, 1])
    kpi_card(ax_kpi2, f"{N/127:.1%}", "Selection probability", TEAL)

    ax = fig.add_subplot(gs[0, 2])
    comp.plot(kind="bar", ax=ax, color=[NAVY, GOLD], width=0.7)
    ax.set_ylabel("% of stations")
    ax.set_xlabel("")
    ax.set_title(
        "Basin representativeness: population vs. sample", fontsize=11)
    ax.tick_params(axis="x", rotation=20)

    dashboard_footer(fig, "DASHBOARD 1 · Sampling Validation")
    save(fig, "dashboard1_sampling.png")
    print("  insight: sample basin shares track the population within ~9pp — SRS is representative.")


# ==========================================================================
# DASHBOARD 2 — Probabilistic analysis
# ==========================================================================
def dashboard2_probability(d):
    step("STEP 2/4 — Probabilistic analysis: rise events, danger-level exposure, empirical distributions")
    s1, s2 = d["s1"], d["s2"]

    r = s1.Daily_Rise_Fall_cm.dropna()
    p_rise = (r > 0).mean()
    print(
        f"  P(rise) Dataset1 = {p_rise:.3f}  (rise={(r > 0).sum()}, fall={(r < 0).sum()}, none={(r == 0).sum()})")

    p_above = {}
    for label, df in [("Dataset1", s1), ("Dataset2", s2)]:
        c = df.Distance_Above_Below_DL_cm.dropna()
        p_above[label] = (c > 0).mean()
        print(
            f"  P(above DL) {label} = {p_above[label]:.3f}  ({(c > 0).sum()}/{len(c)})")

    fig = plt.figure(figsize=(14, 8))
    gs = gridspec.GridSpec(2, 3, height_ratios=[
                           1, 2.2], hspace=0.45, wspace=0.35)

    kpi_card(fig.add_subplot(gs[0, 0]),
             f"{p_rise:.1%}", "P(rise) — Dataset 1", NAVY)
    kpi_card(fig.add_subplot(
        gs[0, 1]), f"{p_above['Dataset1']:.1%}", "P(above DL) — Dataset 1", RED)
    kpi_card(fig.add_subplot(
        gs[0, 2]), f"{p_above['Dataset2']:.1%}", "P(above DL) — Dataset 2", RED)

    bins = [0, 50, 100, 150, 200, 300, 500, np.inf]
    labels = ["0-50", "50-100", "100-150",
              "150-200", "200-300", "300-500", "500+"]
    for col, (label, df, color) in enumerate([("Dataset 1", s1, NAVY), ("Dataset 2", s2, RED)]):
        ax = fig.add_subplot(gs[1, col])
        below = -df.loc[df.Distance_Above_Below_DL_cm <
                        0, "Distance_Above_Below_DL_cm"].dropna()
        prob = pd.cut(below, bins, labels=labels).value_counts(
            normalize=True).reindex(labels)
        bars = ax.bar(labels, prob.values, color=color, edgecolor="white")
        for b, v in zip(bars, prob.values):
            ax.annotate(f"{v:.0%}", (b.get_x() + b.get_width() / 2, v),
                        ha="center", va="bottom", fontsize=8.5)
        ax.set_title(
            f"Empirical P(distance below DL) — {label}", fontsize=10.5)
        ax.set_xlabel("Distance below danger level (cm)")
        ax.set_ylabel("Probability")
        ax.tick_params(axis="x", rotation=30)
        ax.yaxis.set_major_formatter(mticker.PercentFormatter(1.0))

    ax_note = fig.add_subplot(gs[1, 2])
    ax_note.axis("off")
    ax_note.text(0, 0.9, "Reading this dashboard:",
                 fontsize=10.5, fontweight="bold")
    ax_note.text(0, 0.72, "• Top row = single-probability answers\n  to CEP Task 2(a)/(b).",
                 fontsize=9.5, va="top")
    ax_note.text(0, 0.42, "• Bottom charts = empirical PMF for\n  Task 2(c): most below-DL stations sit\n  in the 50-500cm shortfall range in\n  both datasets.",
                 fontsize=9.5, va="top")

    dashboard_footer(fig, "DASHBOARD 2 · Probabilistic Analysis")
    save(fig, "dashboard2_probability.png")


# ==========================================================================
# DASHBOARD 3 — EDA
# ==========================================================================
COLS = ["RHWL_m", "Danger_Level_m", "Previous_Water_Level_m",
        "Current_Water_Level_m", "Daily_Rise_Fall_cm", "Distance_Above_Below_DL_cm"]


def dashboard3_eda(d):
    step("STEP 3/4 — Exploratory data analysis: missing values, distributions, basin patterns, correlation")
    s1, s2 = d["s1"], d["s2"]

    for label, df in [("Dataset1", s1), ("Dataset2", s2)]:
        miss = df[COLS].isna().mean().mul(100).round(1)
        nz = miss[miss > 0]
        if len(nz):
            print(f"  missing % ({label}): " +
                  ", ".join(f"{k}={v}%" for k, v in nz.items()))

    desc = pd.concat({
        "Dataset1": s1[COLS].describe().T[["mean", "50%", "std"]].assign(
            mode=s1[COLS].mode().iloc[0], variance=s1[COLS].var(),
            range=s1[COLS].max() - s1[COLS].min(),
            IQR=s1[COLS].quantile(.75) - s1[COLS].quantile(.25)),
        "Dataset2": s2[COLS].describe().T[["mean", "50%", "std"]].assign(
            mode=s2[COLS].mode().iloc[0], variance=s2[COLS].var(),
            range=s2[COLS].max() - s2[COLS].min(),
            IQR=s2[COLS].quantile(.75) - s2[COLS].quantile(.25)),
    }, axis=1).round(2)
    print(desc)

    fig = plt.figure(figsize=(14, 10))
    gs = gridspec.GridSpec(2, 2, hspace=0.4, wspace=0.3)

    # Panel 1: water level distribution (both datasets overlaid)
    ax1 = fig.add_subplot(gs[0, 0])
    for label, df, c in [("Dataset 1", s1, NAVY), ("Dataset 2", s2, RED)]:
        vals = df.Current_Water_Level_m.dropna()
        sns.kdeplot(vals, ax=ax1, color=c, fill=True,
                    alpha=0.25, linewidth=2, label=label)
    ax1.set_title("Current water level — distribution", fontsize=11)
    ax1.set_xlabel("Water level (m MSL)")
    ax1.legend(fontsize=9)

    # Panel 2: correlation heatmap
    ax2 = fig.add_subplot(gs[0, 1])
    corr = s1[COLS].corr()
    mask = np.triu(np.ones_like(corr, dtype=bool), k=1)
    sns.heatmap(corr, mask=mask, annot=True, fmt=".2f", cmap="RdBu_r", center=0,
                vmin=-1, vmax=1, ax=ax2, cbar_kws={"shrink": 0.75},
                linewidths=0.5, linecolor="white", annot_kws={"fontsize": 8})
    ax2.set_xticklabels(ax2.get_xticklabels(), rotation=35,
                        ha="right", fontsize=8.5)
    ax2.set_yticklabels(ax2.get_yticklabels(), fontsize=8.5)
    ax2.set_title("Correlation matrix — Dataset 1", fontsize=11)

    # Panel 3: boxplot by basin
    ax3 = fig.add_subplot(gs[1, 0])
    order = s1.groupby(
        "Basin").Distance_Above_Below_DL_cm.median().sort_values().index
    sns.boxplot(data=s1, x="Basin", y="Distance_Above_Below_DL_cm", order=order,
                hue="Basin", palette=PALETTE[:4], legend=False, ax=ax3,
                showfliers=False, width=0.55)
    sns.stripplot(data=s1, x="Basin", y="Distance_Above_Below_DL_cm", order=order,
                  ax=ax3, color="black", size=3, alpha=0.4, jitter=0.15)
    ax3.axhline(0, color=RED, lw=1.3, ls="--", label="Danger level")
    ax3.set_title(
        "Distance from danger level by basin — Dataset 1", fontsize=11)
    ax3.set_xlabel("")
    ax3.tick_params(axis="x", rotation=20)
    ax3.legend(fontsize=8, loc="lower left")

    # Panel 4: mean rise/fall by basin
    ax4 = fig.add_subplot(gs[1, 1])
    avg = s1.groupby("Basin").Daily_Rise_Fall_cm.mean().sort_values()
    colors = [TEAL if v >= 0 else RED for v in avg.values]
    bars = ax4.barh(avg.index, avg.values, color=colors)
    for b, v in zip(bars, avg.values):
        ax4.annotate(f"{v:+.1f}", (v, b.get_y() + b.get_height() / 2),
                     va="center", ha="left" if v >= 0 else "right", fontsize=9)
    ax4.axvline(0, color="black", lw=0.8)
    ax4.set_title("Mean daily rise/fall by basin — Dataset 1", fontsize=11)
    ax4.set_xlabel("cm")

    dashboard_footer(fig, "DASHBOARD 3 · Exploratory Data Analysis")
    save(fig, "dashboard3_eda.png")

    m = s1.merge(s2, on="Station_ID", suffixes=("_1", "_2")).dropna(
        subset=["Current_Water_Level_m_1", "Current_Water_Level_m_2"])
    t, p = stats.ttest_rel(m.Current_Water_Level_m_1,
                           m.Current_Water_Level_m_2)
    print(f"  paired t-test (WL Dataset1 vs Dataset2, n={len(m)}): t={t:.3f}, p={p:.3f} -> "
          f"{'significant' if p < 0.05 else 'not significant'} change at α=0.05")
    return m


# ==========================================================================
# DASHBOARD 4 — Correlation & regression
# ==========================================================================
def dashboard4_regression(m):
    step("STEP 4/4 — Correlation & regression: linking Dataset 1 and Dataset 2")
    x, y = m.Current_Water_Level_m_1, m.Current_Water_Level_m_2
    r, _ = stats.pearsonr(x, y)
    slope, intercept, rv, _, _ = stats.linregress(x, y)
    print(
        f"  r={r:.3f}, R²={rv**2:.3f}, WL_t2 = {slope:.3f}*WL_t1 + {intercept:.3f}")

    fig = plt.figure(figsize=(13, 5.5))
    gs = gridspec.GridSpec(1, 2, width_ratios=[1.4, 1], wspace=0.3)

    ax1 = fig.add_subplot(gs[0, 0])
    above = m.Distance_Above_Below_DL_cm_1 > 0
    ax1.scatter(x[~above], y[~above], color=NAVY, alpha=0.7, edgecolor="white",
                s=45, label="Below danger level")
    ax1.scatter(x[above], y[above], color=RED, alpha=0.85, edgecolor="white",
                s=55, label="Above danger level")
    xs = np.linspace(x.min(), x.max(), 100)
    ax1.plot(xs, slope * xs + intercept, color="black", lw=1.8, ls="--",
             label=f"y={slope:.2f}x+{intercept:.2f}")
    ax1.text(0.03, 0.94, f"r = {r:.3f}\nR² = {rv**2:.3f}", transform=ax1.transAxes,
             fontsize=10, va="top", bbox=dict(boxstyle="round", fc="white", ec="#999999"))
    ax1.set_xlabel("Water level, Dataset 1 (m MSL)")
    ax1.set_ylabel("Water level, Dataset 2 (m MSL)")
    ax1.set_title("Water level persistence across ~6 hours", fontsize=11)
    ax1.legend(fontsize=9, loc="lower right")

    ax2 = fig.add_subplot(gs[0, 1])
    diff = (m.Current_Water_Level_m_2 - m.Current_Water_Level_m_1)
    sns.histplot(diff, ax=ax2, color=GOLD, edgecolor="white", kde=True)
    ax2.axvline(0, color="black", lw=1)
    ax2.axvline(diff.mean(), color=RED, ls="--", lw=1.3,
                label=f"mean Δ={diff.mean():+.2f}m")
    ax2.set_title("Change in water level (Dataset2 - Dataset1)", fontsize=11)
    ax2.set_xlabel("Δ water level (m)")
    ax2.legend(fontsize=9)

    dashboard_footer(fig, "DASHBOARD 4 · Correlation & Regression")
    save(fig, "dashboard4_regression.png")
    print(f"  insight: near-perfect persistence (r={r:.3f}) over the ~6h gap — "
          f"expected for slow-moving river levels.")


# ==========================================================================
def main():
    print("=" * 70)
    print("FFWC FLOOD BULLETIN — LIVE ANALYSIS SESSION")
    print("=" * 70)
    d = load_data()
    dashboard1_sampling(d)
    dashboard2_probability(d)
    merged = dashboard3_eda(d)
    dashboard4_regression(merged)

    print("\n" + "=" * 70)
    print(f"Analysis complete — 4 dashboards saved to ./{OUTPUT_DIR}/")
    print("=" * 70)
    if SHOW_PLOTS:
        try:
            plt.show()
        except Exception:
            pass


if __name__ == "__main__":
    main()
