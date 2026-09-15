#!/usr/bin/env python
"""Rewrite hardcoded dataset paths in the temporal notebooks into `config.*` lookups.

Dry run by default; pass --apply to write. Notebook outputs and metadata are
preserved -- only `source` is touched, plus one inserted loader cell.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

OCEAN1 = "/ocean/projects/cis240075p/asachan/datasets/B_Cell/multiome_1st_donor_UPMC_aggr"
TCELLR = "/ocean/projects/cis240075p/asachan/datasets/B_Cell/T_cell"
TCELL = f"{TCELLR}/outs/dictys/rbpj_ntc"
DONOR2 = "/ocean/projects/cis240075p/asachan/datasets/B_Cell/multiome_2nd_donor"
MOTIFS = "/ocean/projects/cis240075p/asachan/datasets/TF_motif_files"
NVME = "/work/nvme/bhdw/asachan/data_files/firefate/bcell"
VEL = "/work/hdd/bgdb/asachan/datasets/B_cell_dictys_actb1_added_v2"
VELIN = "/projects/bgdb/asachan/datasets/Bcell_in_vitro_human"
FIGS = "/projects/bhdw/asachan/papers/firefate/figures"

# Whole-literal matches -> bare `config.NAME`
EXACT = {
    # dictys dynamic object
    f"{OCEAN1}/dictys_outs/actb1_added_v2/output/dynamic.h5": "DYNAMIC_H5",
    f"{OCEAN1}/dictys_outs/output/dynamic.h5": "DYNAMIC_H5",
    f"{NVME}/outs/dynamic.h5": "DYNAMIC_H5",
    # dictys data inputs
    f"{OCEAN1}/dictys_outs/actb1_added_v2/data/day_labels.csv": "DAY_LABELS",
    f"{OCEAN1}/dictys_outs/actb1_added_v2/data/clusters.csv": "CELL_LABELS",
    f"{OCEAN1}/dictys_outs/actb1_added_v2/tmp_dynamic/subset_locs.h5": "SUBSET_LOCS",
    f"{OCEAN1}/dictys_outs/actb1_added_v2/output/episodic_grns/84_percentile": "EPISODIC_GRN_DIR",
    f"{OCEAN1}/dictys_outs/actb1_added_v2/output/intermediate_tmp_files/prdm1_ko/bcl6_dynamic_activity_KO_program": "KO_PROGRAM_DIR",
    f"{OCEAN1}/dictys_outs/actb1_added_v2/output/intermediate_tmp_files/filtered_edges_significant_invariant_PB_ep4.parquet": "FILTERED_EDGES_PB_EP4",
    # latent factors
    f"{OCEAN1}/other_files/latent_factors/feature_list_Z11_GC_PB.txt": "LF_Z11_GC_PB",
    f"{OCEAN1}/other_files/latent_factors/feature_list_Z3_GC_PB.txt": "LF_Z3_GC_PB",
    f"{OCEAN1}/other_files/latent_factors/feature_list_Z5_PRDM1_KO.txt": "LF_Z5_PRDM1_KO",
    f"{OCEAN1}/other_files/latent_factors/feature_list_Z4_IRF4_KO.txt": "LF_Z4_IRF4_KO",
    f"{OCEAN1}/other_files/latent_factors/z_matrix_GC_PB.csv": "Z_MATRIX_GC_PB",
    f"{OCEAN1}/other_files/latent_factors/z_matrix_blimp1_ko_ntc_perturb_seq_cells_day4.csv": "Z_MATRIX_PREDISPOSED",
    f"{NVME}/latent_factors/feature_list_Z11_GC_PB.txt": "LF_Z11_GC_PB",
    # male donor pre-dictys
    f"{OCEAN1}/other_files/combinatorial_control/genes.txt": "MALE_GENE_MASK",
    f"{OCEAN1}/other_files/combinatorial_control/CO_TFs.txt": "MALE_CO_TFS",
    f"{OCEAN1}/cell_ranger_outs/adata_aggregated_gene.leiden.h5ad": "MALE_CELLRANGER_H5AD",
    f"{OCEAN1}/other_files/objects/stream_input_filtered_cells_v7.h5ad": "MALE_STREAM_INPUT",
    f"{OCEAN1}/other_files/SLIDE_cell_barcodes": "MALE_SLIDE_BARCODES",
    "/ocean/projects/cis240075p/skeshari/igvf/bcell1/male_donor/out_data/sc_preproc/out_files/male_sc_processed.h5ad": "MALE_SC_PROCESSED",
    # figures / intermediates
    f"{FIGS}/enriched_tf_lf_targets_per_episode.csv": "EPISODIC_LINKS_CSV",
    f"{FIGS}/z11_episodic_enrichment": "ES_BAR_DIR",
    "/projects/bhdw/asachan/tmp/ss_firefate_links_2B.csv": "SS_LINKS_CSV",
    # T cell
    f"{TCELL}/output": "TCELL_OUTPUT",
    f"{TCELL}/data": "TCELL_DATA",
    f"{TCELL}/output/figs": "TCELL_FIGS",
    f"{TCELL}/data/raw_counts_gene_by_cell.tsv": "TCELL_RAW_COUNTS",
    f"{TCELLR}/Data/grn_files/base_GRN.csv": "TCELL_BASE_GRN",
    f"{TCELLR}/outs/objects": "TCELL_OBJECTS",
    f"{TCELLR}/outs/stream_objs": "TCELL_STREAM_OBJS",
    f"{TCELLR}/outs/stream_objs/rbpj_ntc/rbpj_ntc_v2.pkl": "TCELL_STREAM_TRAJ",
    f"{TCELLR}/outs/stream_objs/rbpj_rna_imputed_v2.h5ad": "TCELL_RNA_IMPUTED",
    f"{TCELLR}/outs/dictys/rbpj_ets1_ikzf1_ntc/data": "TCELL_DICTYS_ALL_DATA",
    # female donor
    f"{DONOR2}/anndata/female_sc_processed.h5ad": "FEMALE_SC_PROCESSED",
    f"{DONOR2}/h5ad_objects/stream_input_filtered_cells.h5ad": "FEMALE_STREAM_INPUT",
    f"{DONOR2}/multiome_rna_imputed.h5ad": "FEMALE_RNA_IMPUTED",
    f"{DONOR2}/stream_outs": "FEMALE_STREAM_OUTS",
    f"{DONOR2}/stream_outs/no_rerun_pca": "FEMALE_STREAM_NO_PCA",
    f"{DONOR2}/stream_outs/stream_traj_no_pca.pkl": "FEMALE_STREAM_TRAJ",
    f"{DONOR2}/dictys_outs/data": "FEMALE_DICTYS_DATA",
    # velocity
    VEL: "VELOCITY_BASE",
    f"{VEL}/velocity_related": "VELOCITY_RELATED",
    f"{VEL}/multivelo_results/multivelo_result.h5ad": "MULTIVELO_RESULT",
    f"{VELIN}/bcell_rna.h5ad": "VELOCITY_RNA_H5AD",
    f"{VELIN}/bcell_atac.h5ad": "VELOCITY_ATAC_H5AD",
    f"{VELIN}/adata_stream_obs.tsv.gz": "VELOCITY_STREAM_OBS",
    f"{VELIN}/stream_outs/stream_traj_v6.pkl": "VELOCITY_STREAM_TRAJ",
    f"{VELIN}/tmp": "VELOCITY_TMP",
    f"{VEL}/data/coord_rna.tsv.gz": "COORD_RNA",
    # motifs
    f"{MOTIFS}/CisBP_Human_FigR_meme": "MOTIF_CISBP_MEME",
    f"{MOTIFS}/JASPAR2020_vertebrates.motif": "MOTIF_JASPAR",
    f"{MOTIFS}/hocomoco_human.motif": "MOTIF_HOCOMOCO",
}

# Directory prefixes -> f"{config.NAME}/rest". Longest match wins.
PREFIX = {
    f"{OCEAN1}/dictys_outs/actb1_added_v2/output/intermediate_tmp_files": "INPUT_FOLDER",
    f"{OCEAN1}/dictys_outs/actb1_added_v2/output/figures": "DICTYS_FIGURES",
    f"{OCEAN1}/dictys_outs/actb1_added_v2/output": "DICTYS_OUTPUT",
    f"{OCEAN1}/dictys_outs/actb1_added_v2/data": "DICTYS_DATA",
    f"{OCEAN1}/dictys_outs/actb1_added_v2/tmp_dynamic": "TMP_DYNAMIC",
    f"{OCEAN1}/dictys_outs/actb1_added/tmp_dynamic": "TMP_DYNAMIC",
    f"{OCEAN1}/dictys_outs/tmp_dynamic": "TMP_DYNAMIC",
    f"{OCEAN1}/dictys_outs/output": "DICTYS_OUTPUT",
    f"{OCEAN1}/other_files/latent_factors": "LF_FOLDER",
    f"{OCEAN1}/other_files/figures_suppli": "FIGURES_SUPPL",
    f"{OCEAN1}/other_files/objects": "MALE_OBJECTS",
    f"{OCEAN1}/other_files/combinatorial_control": "MALE_COMB_CONTROL",
    f"{OCEAN1}/stream_outs/figures": "MALE_STREAM_FIGURES",
    f"{OCEAN1}/stream_outs": "MALE_STREAM_OUTS",
    f"{OCEAN1}/sorting_atac_outs": "MALE_SORTING_ATAC",
    f"{OCEAN1}/outs/filtered_feature_bc_matrix": "MALE_FEATURE_MATRIX",
    # live cluster forms already in some notebooks
    f"{NVME}/outs/intermediate_tmp_files": "INPUT_FOLDER",
    f"{NVME}/outs": "DICTYS_OUTPUT",
    f"{NVME}/data": "DICTYS_DATA",
    f"{NVME}/latent_factors": "LF_FOLDER",
    # two broken spellings of the window directory, both repointed
    f"{NVME}/tmp_dynamic": "TMP_DYNAMIC",
    "//work/hdd/bhdw/asachan/dictys_related/tmp_dynamic": "TMP_DYNAMIC",
    "/work/hdd/bhdw/asachan/dictys_related/tmp_dynamic": "TMP_DYNAMIC",
    FIGS: "OUTPUT_FOLDER",
    # T cell
    f"{TCELL}/tmp_dynamic": "TCELL_TMP_DYNAMIC",
    f"{TCELL}/output": "TCELL_OUTPUT",
    f"{TCELL}/data": "TCELL_DATA",
    f"{TCELLR}/Data/latent_factors/ets1_lfs": "TCELL_LF_ETS1",
    f"{TCELLR}/Data/latent_factors/ikzf1_lfs": "TCELL_LF_IKZF1",
    f"{TCELLR}/outs/objects": "TCELL_OBJECTS",
    f"{TCELLR}/outs/stream_objs": "TCELL_STREAM_OBJS",
    # velocity / female donor directories
    f"{VEL}/velocity_related": "VELOCITY_RELATED",
    f"{DONOR2}/stream_outs": "FEMALE_STREAM_OUTS",
    # raw cellranger, male donor
    f"{OCEAN1}/outs": "MALE_AGGR_OUTS",
    # ---- last-resort per-root fallbacks: anything else under a known root ----
    TCELLR: "TCELL_ROOT",
    OCEAN1: "MALE_BASE",
    DONOR2: "FEMALE_BASE",
    VEL: "VELOCITY_BASE",
    VELIN: "VELOCITY_IN_BASE",
    MOTIFS: "MOTIF_DIR",
    "/ocean/projects/cis240075p/asachan/datasets/B_Cell/multiome_1st_donor_UPMC_day0_2": "DONOR1_DAY0_2",
    "/ocean/projects/cis240075p/asachan/datasets/B_Cell/multiome_1st_donor_UPMC_day3_4": "DONOR1_DAY3_4",
    "/ocean/projects/cis240075p/asachan/datasets/B_Cell/multiome_1st_donor_UPMC_day5_6": "DONOR1_DAY5_6",
}

# Left alone on purpose: one-off debug reads of a single Subset file, /dev/shm,
# .cache pickles, the STREAM tutorial `tut_files/skin` scratch, and the raw
# per-day cellranger dirs in data_prep_and_checks.
SKIP_SUBSTRINGS = ("/dev/shm", "/.cache", "/tut_files/", "/projects/bgdb/asachan/methods/")

LOADER = """# Dataset locations for this notebook come from ../datasets.yaml.
# Edit that file to point at your own copies -- do not hardcode paths below.
from focal.io import DatasetPaths

config = DatasetPaths.from_yaml("../datasets.yaml")
"""

LITERAL = re.compile(r"""(?P<pre>[fFrRbB]{0,2})(?P<q>'''|\"\"\"|'|\")(?P<body>/[^'"\n]{4,}?)(?P=q)""")

# The old path-config bootstrap: a sys.path shim pointing at the deleted
# py_scripts/ tree, plus the `config` import it existed to enable.
# Only ever applied to cells that actually contain that shim (or a Config()
# call) -- `import sys` on its own is left alone.
BOOTSTRAP_HERE = re.compile(
    r"^\s*(import sys\s*$|#\s*Ensure this analysis directory.*$|_here\s*=.*$|"
    r"if _here not in sys\.path:\s*$|\s*sys\.path\.insert\(0, _here\)\s*$)"
)
BOOTSTRAP_CONFIG = re.compile(r"^\s*(from config import \*\s*$|config\s*=\s*Config\(\)\s*$)")


def strip_bootstrap(src: str) -> str:
    has_here = "_here" in src
    kept = [
        ln for ln in src.split("\n")
        if not BOOTSTRAP_CONFIG.match(ln) and not (has_here and BOOTSTRAP_HERE.match(ln))
    ]
    while kept and not kept[0].strip():
        kept.pop(0)
    return "\n".join(kept)


def substitute(body: str, pre: str, quote: str) -> str | None:
    """Return replacement source for one string literal, or None to leave it."""
    if any(s in body for s in SKIP_SUBSTRINGS):
        return None
    if body in EXACT:
        return f"config.{EXACT[body]}"
    for prefix in sorted(PREFIX, key=len, reverse=True):
        if body == prefix:
            return f"config.{PREFIX[prefix]}"
        if body.startswith(prefix + "/"):
            rest = body[len(prefix) + 1:]
            q = '"' if '"' not in rest else "'"
            return f'f{q}{{config.{PREFIX[prefix]}}}/{rest}{q}'
    return None


def process_cell(src: str) -> tuple[str, int]:
    n = 0

    def repl(m):
        nonlocal n
        out = substitute(m.group("body"), m.group("pre"), m.group("q"))
        if out is None:
            return m.group(0)
        n += 1
        return out

    return LITERAL.sub(repl, src), n


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--root", default=".")
    args = ap.parse_args()

    root = Path(args.root)
    total_sub = total_boot = total_loader = 0

    for f in sorted(root.glob("**/*.ipynb")):
        nb = json.loads(f.read_text())
        subs = boots = 0
        emptied = []

        for c in nb["cells"]:
            if c["cell_type"] != "code":
                continue
            src = "".join(c["source"])
            if src.lstrip().startswith(("%%bash", "%%sh", "%%script", "%%capture")):
                continue  # shell cells cannot read `config`

            new, n = process_cell(src)
            subs += n

            # `config._BCELL_BASE` predates DatasetPaths and would AttributeError
            if "config._BCELL_BASE" in new:
                new = new.replace("config._BCELL_BASE", "config.BCELL_BASE")
                subs += 1

            # drop the dead sys.path / `from config import *` bootstrap
            stripped = strip_bootstrap(new)
            if stripped != new:
                boots += 1
                new = stripped

            if new != src:
                c["source"] = new.splitlines(keepends=True)
                # a cell that held nothing but the bootstrap is now dead weight
                if not new.strip() and not c.get("outputs"):
                    emptied.append(id(c))

        if emptied:
            nb["cells"] = [c for c in nb["cells"] if id(c) not in emptied]

        needs_loader = subs > 0 or boots > 0
        already = any(
            "DatasetPaths.from_yaml" in "".join(c["source"])
            for c in nb["cells"] if c["cell_type"] == "code"
        )
        added = 0
        if needs_loader and not already:
            at = 1 if nb["cells"] and nb["cells"][0]["cell_type"] == "markdown" else 0
            nb["cells"].insert(at, {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": LOADER.splitlines(keepends=True),
            })
            added = 1

        if subs or boots or added:
            drop = f"  -{len(emptied)} empty" if emptied else ""
            print(f"{str(f):<48} {subs:>3} paths  {boots:>2} bootstrap  "
                  f"{'+loader' if added else '':<7}{drop}")
            total_sub += subs
            total_boot += boots
            total_loader += added
            if args.apply:
                f.write_text(json.dumps(nb, indent=1, ensure_ascii=False) + "\n")

    verb = "rewrote" if args.apply else "would rewrite"
    print(f"\n{verb}: {total_sub} path literals, {total_boot} bootstrap blocks, "
          f"{total_loader} loader cells inserted")
    if not args.apply:
        print("dry run -- pass --apply to write")


if __name__ == "__main__":
    sys.exit(main())
