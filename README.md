# burnin-qa-dashboard
component burn-in and screening dashboard 
Burn-In Screening QA Dashboard

Interactive Streamlit dashboard for AI-Driven Anomaly Detection in Component Burn-In & Screening — a working prototype built for Smart India Hackathon 2026, Problem Statement 26170 (ISRO / Department of Space).

Component burn-in testing stresses electronic parts under extreme conditions to catch latent defects before they reach a satellite or launch vehicle. A defective part can still pass its absolute datasheet limits and slip through — the real signal is that it behaves differently from the rest of its own manufacturing lot, or drifts in a way that predicts failure later in its life. This dashboard visualizes both of those checks for a QA engineer.

What it does

The prototype has two detection modules feeding one dashboard:

Module A — Dynamic Outlier Detector Flags components that are anomalous relative to the population they were tested with, not against a fixed threshold. Combines per-lot Z-scores and IQR bounds (simple, explainable checks) with an Isolation Forest (catches multi-parameter anomalies a single-parameter check would miss). Each component gets a risk score, a NORMAL / WATCH / CRITICAL status, and a plain-language explanation.

Module B — Time-Series Drift Predictor Looks only at a component's early readings and predicts where its signal will end up later, so a likely failure can be flagged for early rejection before the full burn-in cycle finishes — the whole point being to catch problems without waiting out the entire test.

Dashboard

Module A — Outlier Inspector: population scatter plot with anomalies highlighted, plus the selected component's own signal curve.
Module B — Forecast Visualizer: the model's early-window input, the actual late-stage outcome, and what it predicted, side by side.
Explainability: risk score breakdown, plain-language reasoning, and a Module A / Module B agreement check.
Full Results Table: every component, sortable, with a CSV export.
Data

Built and validated on real NASA MOSFET Thermal Overstress Aging data (component degradation measured as Rds(on) = Vds / Id over time), as a public stand-in for the proprietary ISRO burn-in dataset described in the problem statement. See module_a_and_b_mosfet_real_data.ipynb for the full pipeline — from raw .mat files to the three CSVs this dashboard reads.

Project structure
├── app.py                  # the dashboard
├── requirements.txt
├── data/
│   ├── module_a_results.csv
│   ├── module_b_results.csv
│   └── all_curves.csv
└── module_a_and_b_mosfet_real_data.ipynb   # generates the three CSVs above


