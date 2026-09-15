# Notebooks

Analysis notebooks for Focal, grouped by the module each one exercises. They are
research records rather than tutorials: they were run on a SLURM cluster against data
that is not distributed here, and the documentation renders their stored outputs
without re-executing them.

To adapt one to your own data, edit `temporal/datasets.yaml` rather than the notebooks
themselves — {doc}`the migration notes <NOTEBOOK_MIGRATION>` record how paths and
imports are wired after the package was restructured.

They live in their own repository,
[FOCAL_notebooks](https://github.com/jishnu-lab/FOCAL_notebooks), pulled in
here as a git submodule.

```{toctree}
:maxdepth: 2

temporal/index
state_specific/index
cross_prediction/index
```

```{toctree}
:maxdepth: 1
:titlesonly:
:caption: Reference

NOTEBOOK_MIGRATION
```
