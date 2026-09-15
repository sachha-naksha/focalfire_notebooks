#!/usr/bin/env python
"""Apply the import migration from ../NOTEBOOK_MIGRATION.md to the temporal notebooks.

Rewrites the pre-split module imports (`utils_custom`, `pseudotime_curves`,
`episodic_dynamics`, `state_dynamics`, `episode_plots`, `firefate.core.*`,
`firefate.enrichment`, `firefate.utils.plots`) onto the `temporal` /
`state_specific` / `io` / `backends.dictys` layout.

Dry run by default; pass --apply to write. Matches on cell content, not index, so
it is unaffected by the loader cell added by apply_paths.py. Idempotent.

Two deliberate deviations from NOTEBOOK_MIGRATION.md, both verified against the
installed package:

  * `phase_clustered_links.ipynb` uses `sd.StateFrequency` and `sd.TFForceWaves`
    as well as `sd.plot_force_heatmap_by_phase`. The doc's
    `import focal.temporal._phases as sd` would break the first two -- they
    live in `_states` and `_waves` and `_phases` does not re-export them. Aliased
    to the `focal.temporal` package instead, which exports all three.
  * `dynamic_grn_b_cell.ipynb` only ever calls `qc_reads` from the old `utils`,
    so `read_h5_file`, `read_adata_from_pkl` and `plot_main_trajectory_nodes` are
    not imported. The doc lists them; they would be unused.

The doc's `import focal as ff` is also omitted -- no notebook references `ff`.
Explicit numpy/pandas/matplotlib imports are only added where the notebook would
otherwise lose a name it uses (star imports no longer leak them): in practice that
is `pickle` in LF_global_dynamics.ipynb and nothing else.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# (notebook glob, old block, new block). Blocks are matched after stripping
# trailing whitespace on each line, and must appear verbatim.
REPLACEMENTS: list[tuple[str, str, str, bool]] = []


def add(nb: str, old: str, new: str, every: bool = False) -> None:
    """`every=True` rewrites all matching cells, not just the first."""
    REPLACEMENTS.append((nb, old.strip("\n"), new.strip("\n"), every))


# --- the four analysis notebooks that share an import cell -------------------
for _nb in ("Ext_chromatin_dynamics", "Fig4_2_dynamic_validation",
            "Fig3_2_episodic_enrichment", "Fig4_3_phase_clustered_links"):
    add(f"analysis/{_nb}.ipynb", """
import dictys
from utils_custom import *
from pseudotime_curves import *
from episodic_dynamics import *
""", """
import dictys

from focal.temporal import *      # classes AND their figures
from focal.utils import *         # gene / state helpers (was utils_custom)
""")

# --- LF_global_dynamics ------------------------------------------------------
add("analysis/Fig4_1_LF_global_dynamics.ipynb", """
from utils_custom import *
from pseudotime_curves import *
from episode_plots import *
from episodic_dynamics import *
""", """
import pickle

import matplotlib                    # for matplotlib.animation.writers
from dictys.net import stat          # both were leaked by the old star imports

from focal.temporal import *      # classes AND their figures (was episode_plots)
from focal.utils import *         # gene / state helpers (was utils_custom)
""")

add("analysis/Fig4_1_LF_global_dynamics.ipynb",
    "from pseudotime_curves import *",
    "from focal.temporal import *")

# --- t_cell_analysis ---------------------------------------------------------
add("analysis/Ext_tpex_ex_forces.ipynb", """
from utils_custom import *
from pseudotime_curves import *
from episodic_dynamics import *
""", """
from focal.temporal import *
from focal.utils import *
""")

# --- chromatin_dynamics: reload cell ----------------------------------------
add("analysis/Ext_chromatin_dynamics.ipynb", """
import importlib
import firefate.utils.plots, episode_plots
importlib.reload(firefate.utils.plots)   # picks up the new functions
importlib.reload(episode_plots)          # re-runs `from firefate.utils.plots import *`
from episode_plots import *              # re-bind names into the notebook namespace
""", """
import importlib
import focal.temporal._chromatin, focal.temporal._curves, focal.temporal._waves
for _m in (focal.temporal._chromatin, focal.temporal._curves,
           focal.temporal._waves, focal.temporal):
    importlib.reload(_m)
from focal.temporal import *          # re-bind names into the notebook namespace
""")

# --- dynamic_validation ------------------------------------------------------
add("analysis/Fig4_2_dynamic_validation.ipynb", """
import importlib
import firefate.utils.plots, firefate.utils.custom
import state_dynamics
# re-bind
importlib.reload(firefate.utils.plots)
importlib.reload(firefate.utils.custom)
importlib.reload(state_dynamics)
from state_dynamics import TFForceWaves, StateFrequency, BindingPhases
from dynamic_validation import TFForceValidation
""", """
import importlib
import focal.utils
import focal.temporal._phases, focal.temporal._states
import focal.temporal._waves, focal.temporal._validation
# reload order matters: _phases imports from _states/_align, and _validation
# imports from _phases and _waves, so reload the dependencies first.
for _m in (focal.utils, focal.temporal._waves, focal.temporal._states,
           focal.temporal._phases, focal.temporal._validation, focal.temporal):
    importlib.reload(_m)
from focal.temporal import TFForceWaves, StateFrequency, BindingPhases, TFForceValidation
""")

add("analysis/Fig4_2_dynamic_validation.ipynb", """
import importlib, dynamic_validation
importlib.reload(dynamic_validation)
from dynamic_validation import TFForceValidation
""", """
import importlib, focal.temporal._validation
importlib.reload(focal.temporal._validation)
from focal.temporal._validation import TFForceValidation
""")

add("analysis/Fig4_2_dynamic_validation.ipynb",
    "from firefate.core.pseudotime_curves import SmoothedCurvesChromatin",
    "from focal.temporal import SmoothedCurvesChromatin")

add("analysis/Fig4_2_dynamic_validation.ipynb", """
import importlib, state_dynamics
importlib.reload(state_dynamics)
from state_dynamics import BindingPhases
""", """
import importlib, focal.temporal._phases
importlib.reload(focal.temporal._phases)
from focal.temporal._phases import BindingPhases
""")

# --- episodic_enrichment -----------------------------------------------------
add("analysis/Fig3_2_episodic_enrichment.ipynb", """
import importlib
from focal.utils import plots
importlib.reload(plots)
from episode_plots import *              # re-bind names into the notebook namespace
""", """
import importlib
import focal.temporal._episodes
importlib.reload(focal.temporal._episodes)
importlib.reload(focal.temporal)
from focal.temporal import *          # re-bind names into the notebook namespace
""")

add("analysis/Fig3_2_episodic_enrichment.ipynb",
    "from firefate.enrichment import build_tf_color_bar_table, load_lf_gene_colors",
    "from focal.io import load_lf_gene_colors\n"
    "from focal.state_specific import build_tf_color_bar_table, plot_tf_enrichment_bars")

# the LF colour-bar figures moved with their subject; call them unqualified now
add("analysis/Fig3_2_episodic_enrichment.ipynb",
    "plots.plot_tf_episodic_enrichment_dotplot(",
    "plot_tf_episodic_enrichment_dotplot(")
add("analysis/Fig3_2_episodic_enrichment.ipynb",
    "fig, _ = plots.plot_tf_enrichment_bars(",
    "fig, _ = plot_tf_enrichment_bars(")

# --- phase_clustered_links ---------------------------------------------------
add("analysis/Fig4_3_phase_clustered_links.ipynb", """
import importlib
import firefate.utils.plots, firefate.utils.custom
import state_dynamics
# re-bind
importlib.reload(firefate.utils.plots)
importlib.reload(firefate.utils.custom)
importlib.reload(state_dynamics)
""", """
import importlib
import focal.utils, focal.temporal._waves, focal.temporal._phases
for _m in (focal.utils, focal.temporal._waves,
           focal.temporal._phases, focal.temporal):
    importlib.reload(_m)
""")

# NOT `focal.temporal._phases as sd`: this notebook also calls sd.StateFrequency
# (_states) and sd.TFForceWaves (_waves), which _phases does not re-export.
add("analysis/Fig4_3_phase_clustered_links.ipynb",
    "import state_dynamics as sd",
    "import focal.temporal as sd")

# --- renamed API, not covered by NOTEBOOK_MIGRATION.md -----------------------
# `SmoothedCurves` was split into SmoothedCurvesGRN / SmoothedCurvesChromatin.
# The GRN one takes the identical constructor signature these call sites use
# (dictys_dynamic_object, trajectory_range, num_points, dist, sparsity, mode)
# and still exposes .get_smoothed_curves().
for _nb in ("Fig4_1_LF_global_dynamics", "Ext_tpex_ex_forces"):
    add(f"analysis/{_nb}.ipynb", "SmoothedCurves(", "SmoothedCurvesGRN(", every=True)

# `run_episode` -> `run_episodic_enrichment`: same parameter list, including the
# `lf_genes` and `percentile` this call site passes (run_episodic_construction
# takes neither).
add("analysis/Ext_tpex_ex_forces.ipynb", "run_episode(", "run_episodic_enrichment(", every=True)

# --- dynamic_grn_b_cell ------------------------------------------------------
# `qc_reads` is the only name this notebook used from the old utils.py.
add("dynamic_grn/dynamic_grn_b_cell.ipynb",
    "from utils import *",
    "from focal.io import qc_reads")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--root", default=".")
    args = ap.parse_args()
    root = Path(args.root)

    by_nb: dict[str, list[tuple[str, str, bool]]] = {}
    for nb, old, new, every in REPLACEMENTS:
        by_nb.setdefault(nb, []).append((old, new, every))

    total = 0
    unmatched: list[tuple[str, str]] = []
    for nb_path, subs in by_nb.items():
        f = root / nb_path
        if not f.is_file():
            unmatched.append((nb_path, "<notebook missing>"))
            continue
        nb = json.loads(f.read_text())
        hits = 0
        for old, new, every in subs:
            found = False
            for c in nb["cells"]:
                if c["cell_type"] != "code":
                    continue
                src = "".join(c["source"])
                if old in src:
                    c["source"] = src.replace(old, new).splitlines(keepends=True)
                    hits += 1
                    found = True
                    if not every:
                        break
            if not found:
                # already migrated is fine; anything else is worth reporting
                already = any(new in "".join(c["source"])
                              for c in nb["cells"] if c["cell_type"] == "code")
                if not already:
                    unmatched.append((nb_path, old.split("\n")[0][:60]))
        if hits:
            print(f"{nb_path:<48} {hits:>2} import block(s)")
            total += hits
            if args.apply:
                f.write_text(json.dumps(nb, indent=1, ensure_ascii=False) + "\n")

    verb = "rewrote" if args.apply else "would rewrite"
    print(f"\n{verb}: {total} import blocks")
    if unmatched:
        print("\nNOT FOUND (neither old nor new form present):")
        for nb_path, frag in unmatched:
            print(f"  {nb_path}: {frag}")
    if not args.apply:
        print("\ndry run -- pass --apply to write")
    return 0


if __name__ == "__main__":
    sys.exit(main())
