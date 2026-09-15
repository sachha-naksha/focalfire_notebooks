# Temporal

Notebooks for {mod}`focal.temporal` — how TF regulation changes *along* a
trajectory. Read them in the order below: pseudotime is inferred first, the dictys
window networks are built on top of it, and everything else is analysis of those
networks.

Titles are given explicitly here because these notebooks open on a code cell rather
than a heading.

## Setup

Installing the `focal` backend and pointing `datasets.yaml` at your own data, once
per machine.

```{toctree}
:maxdepth: 1

Setup <SETUP>
```

## Trajectory inference

Pseudotime and RNA velocity for the B-cell and T-cell systems, per donor.

```{toctree}
:maxdepth: 1
:titlesonly:

STREAM trajectory — male donor <trajectory/traj_stream_male_donor>
STREAM trajectory — female donor <trajectory/traj_stream_female_donor>
Expression imputation — male donor <trajectory/imputation_male_donor>
Expression imputation — female donor <trajectory/imputation_female_donor>
B-cell RNA velocity (MultiVelo) <trajectory/b_cell_velocity>
T-cell trajectory <trajectory/t_cell_trajectory>
T-cell expression imputation <trajectory/t_cell_imputation>
```

## Dynamic GRN construction

Preparing dictys inputs, checking them, and reconstructing the per-window networks
that every downstream notebook reads.

```{toctree}
:maxdepth: 1
:titlesonly:

Preparing and checking dictys inputs <dynamic_grn/data_prep_and_checks>
B-cell dynamic GRN reconstruction <dynamic_grn/dynamic_grn_b_cell>
T-cell dictys inputs <dynamic_grn/t_cell_dictys_data>
```

## Analysis

Built on the reconstructed networks: episodic GRNs and their enrichment, regulatory
phases, chromatin dynamics, and the enriched-vs-random validation.

```{toctree}
:maxdepth: 1
:titlesonly:

Global regulation of a latent factor <analysis/Fig4_1_LF_global_dynamics>
Episodic TF enrichment <analysis/Fig3_2_episodic_enrichment>
Episodic TF enrichment — knockout programs <analysis/Fig5_episodic_enrichment>
Clustering links into regulatory phases <analysis/Fig4_3_phase_clustered_links>
TF binding dynamics from chromatin <analysis/Ext_chromatin_dynamics>
Validation — enriched vs random TF force <analysis/Fig4_2_dynamic_validation>
Tpex/Tex TF forces <analysis/Ext_tpex_ex_forces>
```
