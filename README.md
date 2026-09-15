# Focal notebooks

All code notebooks for reproducibility, for
[**Focal**](https://github.com/jishnu-lab/FOCAL) — Functional and Interpretable
Regulatory Encoding of cellular Fate.

This repository is consumed as a git submodule at `docs/notebooks` in the main
repository, and rendered into the documentation at
[focalfire.readthedocs.io](https://focalfire.readthedocs.io/). Keeping the notebooks
here keeps ~26 MB of stored cell outputs out of the source tree while still letting the
docs render them.

## Layout

Notebooks are grouped by the Focal module they exercise, mirroring `src/focal/`:

| directory | module | what it covers |
|---|---|---|
| `temporal/` | `focal.temporal` | trajectory inference, dynamic GRNs, episodic GRNs and their enrichment (capabilities 3, 4, dynamic 5) |
| `state_specific/` | `focal.state_specific` | preprocessing, state-specific GRN inference, latent-factor enrichment, in-silico perturbation (capabilities 1, 2, static 5, 6) |
| `cross_prediction/` | `focal.cross_prediction` | fate-bias stratification by transferring programs across datasets (capability 7) — empty until that module is ported |

Within `temporal/`, `trajectory/` comes first (STREAM/Palantir/MultiVelo pseudotime),
then `dynamic_grn/` (dictys inputs and window networks), then `analysis/` (everything
built on top of the reconstructed networks).

## Running them

These are **research records, not tutorials.** They were run on a SLURM cluster against
data that is not distributed with either repository, and their paths reflect that. To
re-run one you need:

1. The `fftemporal` environment, which pins `dictys` 1.1.0 and the rest of the
   runtime stack it needs — `pytorch` 2.3.1 (CUDA 11.8), `gimmemotifs`, `genomepy`,
   `homer`, `macs2`, `samtools`, `bedtools`:
   ```bash
   conda env create -f environment.yml
   conda activate fftemporal
   ```
2. `focal` on top of it, editable from your own clone. It is deliberately **not**
   in `environment.yml`: the package is under active development, so the environment
   tracks whatever you have checked out rather than a pinned snapshot. `--no-deps`
   keeps pip from re-resolving packages conda already placed:
   ```bash
   git clone https://github.com/jishnu-lab/FOCAL Focal
   pip install -e Focal --no-deps
   ```
3. Dataset paths pointed at your own copies. Every path lives in
   `temporal/datasets.yaml` — edit that file, not the notebooks. Each temporal
   notebook already opens with the loader cell that reads it:
   ```python
   from focal.io import DatasetPaths
   config = DatasetPaths.find()
   ```
   `find()` walks up from the kernel's working directory to the first
   `datasets.yaml`, or takes the path in `$FOCAL_DATASETS`, so it does not matter
   where Jupyter was started.
   `temporal/SETUP.md` explains which roots are live on this cluster and which are
   dead PSC paths you have to repoint first.
4. Separate environments for the other two groups. `fftemporal` covers the
   dictys-based dynamic GRN work — `temporal/dynamic_grn/` and `temporal/analysis/` —
   and nothing else. `temporal/trajectory/` needs `stream` / `palantir` / `scvelo` /
   `multivelo`; `state_specific/` needs `scanpy` and `celloracle`. None of those are
   in `environment.yml`. Build them separately and carry results across as files.

   One wrinkle if you go looking: `anndata` 0.6.22.post1 ships in the environment but
   does not import, because it predates the pinned pandas 2.2.2 (`pandas.core.index`
   was removed). Nothing in the environment depends on it and `dictys` never imports
   it, so the dynamic GRN path is unaffected — but any notebook doing `import anndata`
   belongs in one of the environments above, not this one.

### Regenerating environment.yml

`environment.yml` is an export of the working `fftemporal` environment with the
`focal` line stripped, since that entry refers to a local editable install and
resolves for nobody else:

```bash
conda env export -n fftemporal --no-builds \
  | sed -e '/^      - focal==/d' -e '/^prefix: /d' > environment.yml
```

It pins exact versions and is linux-64 only — the `homer` / `macs2` / `samtools`
dependencies have no macOS or Windows builds.

`NOTEBOOK_MIGRATION.md` records the import changes made when the Focal package was
restructured around its three modules, with the old and new cell for each notebook.

## Page titles

Sphinx needs one top-level heading per notebook to give the page a title and a sidebar
link. `add_titles.py` prepends a `# Title` cell to any notebook missing one — run
`python add_titles.py` for a dry run, `--apply` to write. It is idempotent, so run it
again after adding a notebook.

## Migration tools

`temporal/apply_paths.py` is the one-shot tool that rewrote the hardcoded dataset paths
in the temporal notebooks into `config.NAME` lookups against `temporal/datasets.yaml`.
It is idempotent and dry-run by default (`--apply` to write), so re-running it after
adding a notebook picks up only the new literals. It never touches cell outputs,
`%%bash` cells, or scratch paths (`/dev/shm`, `.cache`). **Close the notebooks in
Jupyter before running it with `--apply`** — an open kernel will overwrite the change
on its next autosave.

`temporal/apply_imports.py` is its counterpart for imports: it applied
`NOTEBOOK_MIGRATION.md` to the temporal notebooks, moving them off the pre-split
modules (`utils_custom`, `pseudotime_curves`, `firefate.core.*`, …) and onto
`focal.temporal` / `state_specific` / `io` / `backends.dictys`. Same contract —
idempotent, dry-run by default, matches on cell content rather than index, and leaves
outputs untouched. Its docstring records the three places it deliberately departs from
the doc.

## Contributing

Commit notebooks **with their outputs** — the documentation renders stored outputs and
never executes anything (`nb_execution_mode = "off"`), so a stripped notebook shows up
as an empty page. Keep the folder a notebook lives in matched to the module it exercises.

## License

MIT, same as the main repository.
