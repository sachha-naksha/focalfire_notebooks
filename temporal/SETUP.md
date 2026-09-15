# Setup for the temporal notebooks

Two things have to be true before any notebook in `trajectory/`, `dynamic_grn/` or
`analysis/` runs: `focal` must be importable in the kernel, and `datasets.yaml` must
point at your copies of the data. Nothing here is notebook-specific — do it once per
machine.

## 1. Install the Focal backend (editable)

The notebooks import `focal` as an ordinary package; there is no `sys.path`
bootstrap any more. Install the main repository in editable mode **into the same
environment whose kernel the notebooks use** (`dictys` on our cluster):

```bash
source /sw/rh9.4/python/miniforge3/etc/profile.d/conda.sh
conda activate dictys

git clone https://github.com/jishnu-lab/FOCAL Focal   # or use your existing clone
cd Focal
pip install -e .
```

`-e` means edits under `src/focal/` are picked up on the next kernel restart — no
reinstall. Verify from the same environment:

```bash
python -c "import focal, focal.io; print(focal.__file__)"
```

The path printed must be your clone's `src/focal/__init__.py`, not a copy under
`site-packages/`. If it is not, you installed into a different environment.

If you would rather not leave the notebook, `%pip install -e /path/to/Focal` in the
first cell installs into the running kernel's environment; restart the kernel after.

### Optional extras

`pyproject.toml` declares only the numeric/plotting core as required. Add what a given
notebook needs:

```bash
pip install -e ".[scanpy]"      # scanpy
pip install -e ".[dev]"         # pytest
pip install -e ".[docs]"        # sphinx + myst-nb, only for building the docs
```

**Not** declared anywhere, and **not** installed by the line above: `dictys` (every
`dynamic_grn/` and most `analysis/` notebooks), and `stream` / `palantir` / `scvelo` /
`multivelo` / `cellrank` / `velocyto` (the `trajectory/` notebooks). Those have
conflicting pins, which is why they live in separate conda environments here rather
than in `dependencies`. Match the environment to the notebook directory.

## 2. Point `datasets.yaml` at your data

Every dataset location for these notebooks lives in `temporal/datasets.yaml`. Edit that
file — never the notebooks, and never `src/focal/`, which is why the paths were
moved out of the package in the first place.

Every notebook now opens with a loader cell that reads it:

```python
from focal.io import DatasetPaths

config = DatasetPaths.find()
```

and every dataset path below that cell is a `config.NAME` lookup rather than a string
literal. Nothing else in a notebook needs editing to move it to new data.

### Live and dead roots

`roots:` is split into two blocks. The **LIVE** roots were verified to exist on this
cluster, so the B-cell notebooks run against them unchanged:

| root | holds |
|---|---|
| `bcell` | the dictys run — `{bcell}/data`, `{bcell}/outs`, `{bcell}/latent_factors` |
| `tmp_dyn` | the per-window `Subset1..SubsetN` directories |
| `figures` | where figures for the paper are written |

The **DEAD** roots (`tcell`, `donor1`, `donor2`, `velocity`, `motifs`, …) are the PSC
`/ocean/...` and `bgdb` paths the notebooks were originally run against. No copy of
them resolves here. They are kept verbatim as a provenance record — repoint the root
and everything below it follows, because every scalar is written relative to one.

To see where you stand before running anything, use the check at the end of this
section: on an untouched checkout it reports the live scalars present and every dead
one missing, which is expected, not a fault.

### The three sections

```yaml
roots:                                  # reusable prefixes; may reference each other
  bcell: /work/nvme/bhdw/asachan/data_files/firefate/bcell
  inputs: "{bcell}/outs/intermediate_tmp_files"

scalars:                                # one path per name
  OUTPUT_FOLDER: "{figures}"
  CELL_LABELS: "{bcell}/data/clusters.csv"

groups:                                 # one path per episode
  PB:
    template: "{enrichment}/enrichment_ep{i}_pb.csv"
    n_episodes: 4
```

* `{name}` is substituted from `roots`. Roots may refer to other roots — they are
  expanded repeatedly until stable, so ordering does not matter.
* `{i}` in a group `template` is the episode number.
* A group needs **either** `n_episodes: 4` (meaning 1…4) **or** an explicit
  `episodes: [1, 2, 5]` when the numbering has gaps. Giving neither raises `KeyError`.
* Quote any value containing `{`, otherwise YAML reads it as a flow mapping.

### Loading it

`DatasetPaths.find()` walks up from the kernel's working directory to the first
`datasets.yaml`, so it finds `temporal/datasets.yaml` from `analysis/`, `dynamic_grn/`
or `trajectory/` regardless of where Jupyter was started; a kernel started outside the
notebook tree sets `FOCAL_DATASETS=/path/to/datasets.yaml` once instead.
`DatasetPaths.from_yaml(path)` is the explicit form.

```python
from focal.io import DatasetPaths

config = DatasetPaths.find()  # or DatasetPaths.from_yaml("../datasets.yaml")
config.OUTPUT_FOLDER          # scalar -> str
config.PB["ep1"]              # group  -> path for episode 1
config.load_enrichment("PB")  # the group's CSVs, in episode order, p_value < 0.05
```

Keep the variable named `config`: the notebooks were written against an older
`Config()` class with the same attribute names, so every downstream
`config.OUTPUT_FOLDER` / `config.PB['ep1']` keeps working unchanged. Unknown names
raise `AttributeError` listing the scalars and groups that *are* defined, so a typo
fails at the top of the notebook rather than three cells in.

### Check it before running anything

```python
from pathlib import Path

for name, path in config.scalars.items():
    print(f"{'ok     ' if Path(path).exists() else 'MISSING'}  {name}  {path}")

for name, episodes in config.groups.items():
    present = sum(Path(p).exists() for p in episodes.values())
    print(f"{name}: {present}/{len(episodes)} episode files present")
```

`load_enrichment` returns an empty frame for a missing episode by default so partial
runs still line up positionally; pass `missing_ok=False` if you would rather it raise.

### Keeping your paths out of git

The committed `datasets.yaml` records the paths these notebooks were run against, and
the `tcell` root is a PSC `/ocean/...` path that no longer resolves on this cluster.
Rather than committing a rewrite of it, copy it:

```bash
cp datasets.yaml datasets.local.yaml     # edit this one
echo "datasets.local.yaml" >> ../.gitignore
```

and load `"../datasets.local.yaml"`. Only commit a change to `datasets.yaml` itself
when the canonical location of a dataset actually moves.

## 3. Paths and imports are both migrated

Nothing here is outstanding. `Config()` and the `sys.path` shim that pointed at the
deleted `py_scripts/` tree are gone, replaced by the loader cell above, and the
pre-split module imports (`utils_custom`, `pseudotime_curves`, `episodic_dynamics`,
`state_dynamics`, `episode_plots`, `firefate.core.*`, `firefate.enrichment`,
`firefate.utils.plots`) have been rewritten onto the `temporal` / `state_specific` /
`io` / `backends.dictys` layout. `../NOTEBOOK_MIGRATION.md` remains the record of what
moved where; `apply_imports.py` is the tool that applied it.

Because the new packages define `__all__`, a star import no longer leaks the module's
own imports into the notebook. Where a notebook depended on that, the name is now
imported explicitly — `pickle`, `matplotlib` and `dictys.net.stat` in
`LF_global_dynamics`, and `calculate_tf_episodic_enrichment` (which lives in
`focal.base`, not `focal.temporal`) in `LF_local_dynamics`.

Two renames that `NOTEBOOK_MIGRATION.md` does not mention were applied as well:
`SmoothedCurves` → `SmoothedCurvesGRN` and `run_episode` → `run_episodic_enrichment`.
Both were matched on identical parameter lists, not on name similarity.

### One thing still missing

`dynamic_validation.ipynb` calls `bp_pb.plot_box(category_tfs, ...)` and
`bp_gc.plot_box(category_tfs, ...)`, but `category_tfs` is never defined — it is a
notebook variable whose defining cell is gone, not a name any import supplies (it
appears in the package only as a parameter of `BindingPhases.plot_box`). It maps each
category name to its TF universe. Define it before running those two cells.

A few paths are deliberately still literals, because they are scratch rather than
data: `/dev/shm` staging in the trajectory notebooks, the `.cache/*.pkl` pickles in
`b_cell_velocity`, and the STREAM tutorial `tut_files/skin` directory in
`traj_stream_female_donor`. `%%bash` cells are also untouched — a shell cell cannot
read `config`, so the SLURM and `dictys_helper` blocks still carry absolute paths and
must be edited by hand.
