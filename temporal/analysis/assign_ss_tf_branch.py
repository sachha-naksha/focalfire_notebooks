"""Assign each state-specific TF to the PB or GC branch by mean expression, once, on disk.

Adds the columns ``tf_branch``, ``tf_PB_mean_log2cpm``, ``tf_GC_mean_log2cpm`` and
``tf_log2FC_PB_vs_GC`` to the state-specific links CSV (``config.SS_LINKS_CSV``), so
Fig4_4_tf_binding_phases can split the state-specific TF universe per branch without touching the
dynamic network again. Same test as the "branch with higher expression" table in
Fig3_2: smoothed log2-CPM expression curve per branch from the branch node
(node 0 -> 2 for PB, 0 -> 3 for GC; 100 points, dist=0.0005, sparsity=0.01), mean
over the branch, ``PB`` if PB - GC > 0 else ``GC``. TFs without an expression curve
get an empty ``tf_branch``. The previous CSV is kept as ``<csv>.bak_<YYYYMMDD>``.

Run from this folder in the ``dictys`` env (needs the full dynamic.h5, ~45 GB RAM):
    python assign_ss_tf_branch.py
"""
import datetime
import shutil

import numpy as np
import pandas as pd
import dictys

from focal.io import DatasetPaths
from focal.temporal import SmoothedCurvesGRN

BRANCHES = {'PB': (0, 2), 'GC': (0, 3)}
SMOOTHING = dict(num_points=100, dist=0.0005, sparsity=0.01)

config = DatasetPaths.find()
csv_path = str(config.SS_LINKS_CSV)
links = pd.read_csv(csv_path, dtype={"key": "Int64", "cluster": "Int64"})  # keep ints on write
tfs = list(dict.fromkeys(links['source']))

dyn = dictys.net.dynamic_network.from_file(config.DYNAMIC_H5)
means = {}
for branch, rng in BRANCHES.items():
    sc = SmoothedCurvesGRN(dyn, trajectory_range=rng, mode='expression', **SMOOTHING)
    dy, _ = sc.get_smoothed_curves()
    means[branch] = dy.reindex(tfs).mean(axis=1)

expr = pd.DataFrame({'tf_PB_mean_log2cpm': means['PB'], 'tf_GC_mean_log2cpm': means['GC']})
expr['tf_log2FC_PB_vs_GC'] = expr['tf_PB_mean_log2cpm'] - expr['tf_GC_mean_log2cpm']
expr['tf_branch'] = np.where(expr['tf_log2FC_PB_vs_GC'] > 0, 'PB', 'GC')
expr.loc[expr['tf_log2FC_PB_vs_GC'].isna(), 'tf_branch'] = ''
expr = expr.round(4)
print(expr.sort_values('tf_log2FC_PB_vs_GC', ascending=False).to_string())
print('\nTFs per branch:', expr['tf_branch'].value_counts().to_dict())

backup = f"{csv_path}.bak_{datetime.date.today():%Y%m%d}"
shutil.copy2(csv_path, backup)
links = links.drop(columns=[c for c in expr.columns if c in links.columns])
links = links.join(expr[['tf_branch', 'tf_PB_mean_log2cpm', 'tf_GC_mean_log2cpm',
                         'tf_log2FC_PB_vs_GC']], on='source')
links.to_csv(csv_path, index=False)
print(f'\nwrote {csv_path} (backup: {backup})')
