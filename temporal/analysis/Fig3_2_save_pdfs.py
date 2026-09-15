"""Save the plot outputs of Fig3_2_episodic_enrichment.ipynb as PDFs.

Reproduces the two episodic-enrichment dotplots (cells 8-9) and the per-episode
enrichment-score bar plots (cells 11-13) and writes every figure to OUT_DIR.
Only the enrichment CSVs are needed, so this runs on a login node.

    cd temporal/analysis && python Fig3_2_save_pdfs.py
"""
import ast
import os
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from focal.io import DatasetPaths, load_lf_gene_colors
from focal.state_specific import build_tf_color_bar_table, plot_tf_enrichment_bars
from focal.temporal import plot_tf_episodic_enrichment_dotplot

plt.rcParams["pdf.fonttype"] = 42  # editable text

OUT_DIR = Path("/projects/bhdw/asachan/papers/focalfire/figures/z11_episodic_enrichment")
OUT_DIR.mkdir(parents=True, exist_ok=True)

config = DatasetPaths.from_yaml(Path(__file__).resolve().parents[1] / "datasets.yaml")

episode_labels = ["Ep1", "Ep2", "Ep3", "Ep4"]
pb_dfs = {ep: pd.read_csv(config.PB[ep.lower()]) for ep in episode_labels}
gc_dfs = {ep: pd.read_csv(config.GC[ep.lower()]) for ep in episode_labels}

# ---- dotplots (notebook cells 8 and 9) ------------------------------------
DOT_KW = dict(
    episode_labels=episode_labels,
    figsize=(4.5, 3.5),
    p_value_threshold=0.05,
    min_significance_threshold=0.05,
    min_dot_size=10,
    max_dot_size=200,
    tf_order=None,
    figure_title=None,
    log_scale=True,
    horizontal_layout=False,
)
fig, _, plotted_tfs_pb = plot_tf_episodic_enrichment_dotplot(
    dfs=list(pb_dfs.values()), cmap_name="Reds", **DOT_KW)
fig.savefig(OUT_DIR / "z11_pb_ee_005.pdf", dpi=300, bbox_inches="tight")
plt.close(fig)

fig, _, plotted_tfs_gc = plot_tf_episodic_enrichment_dotplot(
    dfs=list(gc_dfs.values()), cmap_name="Greens", **DOT_KW)
fig.savefig(OUT_DIR / "z11_gc_ee_005.pdf", dpi=300, bbox_inches="tight")
plt.close(fig)

# ---- episodic links (notebook cell 11) ------------------------------------
PB_PVAL_THRESHOLD = 0.05
GC_PVAL_THRESHOLD = 0.05


def parse_genes_in_lf(genes_str):
    try:
        if pd.isna(genes_str) or genes_str in ("", "()"):
            return ()
        val = ast.literal_eval(genes_str)
        return val if isinstance(val, tuple) else (val,)
    except Exception:
        return ()


def collect_lf_targets(dfs_by_episode, enriched_tfs, lineage, p_value_threshold):
    tf_rank = {tf: i for i, tf in enumerate(enriched_tfs)}
    rows = []
    for episode, df in dfs_by_episode.items():
        sub = df[(df["TF"].isin(tf_rank.keys())) & (df["p_value"] <= p_value_threshold)]
        for _, r in sub.iterrows():
            genes = parse_genes_in_lf(r["genes_in_lf"])
            if not genes:
                continue
            rows.append({
                "lineage": lineage,
                "episode": episode,
                "TF": r["TF"],
                "tf_rank": tf_rank[r["TF"]],
                "enrichment_score": r["enrichment_score"],
                "p_value": r["p_value"],
                "genes_in_lf": ", ".join(genes),
                "n_genes_in_lf": len(genes),
            })
    return rows


enriched_tf_lf_targets = (
    pd.DataFrame(
        collect_lf_targets(pb_dfs, plotted_tfs_pb, "PB", PB_PVAL_THRESHOLD)
        + collect_lf_targets(gc_dfs, plotted_tfs_gc, "GC", GC_PVAL_THRESHOLD)
    )
    .sort_values(["lineage", "tf_rank", "episode"])
    .drop(columns="tf_rank")
    .reset_index(drop=True)
)

# ---- ES bar plots (notebook cell 13) ---------------------------------------
gene_colors = load_lf_gene_colors([config.LF_Z11_GC_PB])

for (lineage, episode), sub in enriched_tf_lf_targets.groupby(["lineage", "episode"]):
    links = pd.DataFrame(
        [{"source": r["TF"], "target": g}
         for _, r in sub.iterrows()
         for g in r["genes_in_lf"].split(", ")
         if g in gene_colors],
        columns=["source", "target"],
    ).drop_duplicates()
    if links.empty:
        print(f"{lineage} {episode}: no LF targets, skipped")
        continue
    plot_df = build_tf_color_bar_table(
        links,
        sub[["TF", "enrichment_score"]].rename(columns={"enrichment_score": "score"}),
        gene_colors,
    )
    out_path = OUT_DIR / f"z11_{lineage.lower()}_es_bars_{episode.lower()}.pdf"
    fig, _ = plot_tf_enrichment_bars(
        plot_df,
        f"{lineage} {episode}: enrichment score per TF, LF targets split by sign",
        out_path=out_path,
    )
    plt.close(fig)
    print(f"saved {out_path}")

print(f"\nPDFs in {OUT_DIR}:")
for p in sorted(OUT_DIR.glob("*.pdf")):
    print(" ", p.name)
