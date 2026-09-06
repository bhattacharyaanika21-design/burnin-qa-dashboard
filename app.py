"""
ISRO Burn-In Screening -- QA Dashboard

Reads the CSVs produced by the Module A + Module B notebook and gives a QA
engineer three views, matching the project brief's "Dashboard UI Views":

  1. Module A Inspector   -- population scatter with anomalies highlighted,
                              plus the selected device's own curve.
  2. Module B Forecast Visualizer -- observed early behavior vs. actual and
                              predicted late behavior for the selected device.
  3. Explainability panel -- why a device was flagged, in plain language,
                              plus the numeric breakdown behind the risk score.

Expects three files in ./data/ :
  - module_a_results.csv
  - module_b_results.csv
  - all_curves.csv   (long format: component, time, signal)
"""

import pandas as pd
import numpy as np
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px

st.set_page_config(page_title="Burn-In Screening QA Dashboard", layout="wide")

DATA_DIR = "data"

# ---------------------------------------------------------------------------
# Load data
# ---------------------------------------------------------------------------
@st.cache_data
def load_data():
    module_a = pd.read_csv(f"{DATA_DIR}/module_a_results.csv")
    module_b = pd.read_csv(f"{DATA_DIR}/module_b_results.csv")
    curves = pd.read_csv(f"{DATA_DIR}/all_curves.csv")
    return module_a, module_b, curves


try:
    module_a, module_b, curves = load_data()
except FileNotFoundError as e:
    st.error(
        "Couldn't find the result CSVs. Run the Module A + Module B notebook "
        "first, then copy module_a_results.csv, module_b_results.csv, and "
        "all_curves.csv into this app's ./data/ folder.\n\n"
        f"Details: {e}"
    )
    st.stop()

STATUS_COLORS = {"NORMAL": "#4C72B0", "WATCH": "#DD8452", "CRITICAL": "#C44E52"}

# ---------------------------------------------------------------------------
# Sidebar -- filters and device selector
# ---------------------------------------------------------------------------
st.sidebar.title("Burn-In Screening")
st.sidebar.caption("AI-Driven Anomaly Detection in Component Burn-In & Screening")

status_filter = st.sidebar.multiselect(
    "Show status",
    options=["NORMAL", "WATCH", "CRITICAL"],
    default=["NORMAL", "WATCH", "CRITICAL"],
)

filtered = module_a[module_a["status"].isin(status_filter)].sort_values(
    "risk_score", ascending=False
)

selected_component = st.sidebar.selectbox(
    "Select a component to inspect",
    options=filtered["component"].tolist(),
    index=0 if len(filtered) else None,
)

if not selected_component:
    st.warning("No components match the selected status filter. Choose at least one status in the sidebar.")
    st.stop()

st.sidebar.markdown("---")
st.sidebar.metric("Total screened", len(module_a))
st.sidebar.metric("Critical", int((module_a["status"] == "CRITICAL").sum()))
st.sidebar.metric("Watch", int((module_a["status"] == "WATCH").sum()))
st.sidebar.metric("Normal", int((module_a["status"] == "NORMAL").sum()))

# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
st.title("Component Burn-In & Screening -- QA Dashboard")
st.caption(
    "Module A flags components that are anomalous relative to the tested "
    "population. Module B predicts late-stage drift from early readings, "
    "flagging candidates for early rejection."
)

tab_a, tab_b, tab_explain, tab_table = st.tabs(
    ["Module A -- Outlier Inspector", "Module B -- Forecast Visualizer", "Explainability", "Full Results Table"]
)

# ---------------------------------------------------------------------------
# Tab 1 -- Module A Inspector
# ---------------------------------------------------------------------------
with tab_a:
    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("Population view")
        fig = px.scatter(
            module_a,
            x="change_percent",
            y="volatility",
            color="status",
            color_discrete_map=STATUS_COLORS,
            hover_name="component",
            hover_data={"risk_score": ":.1f", "change_percent": ":.1f", "volatility": ":.2f"},
            labels={"change_percent": "Change from start to end (%)", "volatility": "Signal volatility"},
        )
        # Highlight the selected device
        if selected_component:
            sel_row = module_a[module_a["component"] == selected_component].iloc[0]
            fig.add_trace(
                go.Scatter(
                    x=[sel_row["change_percent"]],
                    y=[sel_row["volatility"]],
                    mode="markers",
                    marker=dict(size=18, color="black", symbol="circle-open", line=dict(width=3)),
                    name="Selected",
                    showlegend=True,
                )
            )
        fig.update_layout(height=450, legend_title_text="Status")
        st.plotly_chart(fig, width="stretch")
        st.caption(
            "Every point is one tested component. Position is driven by how much "
            "it changed over the test and how noisy its signal was -- not an "
            "absolute datasheet limit, since the anomaly judgment here is "
            "relative to the tested population."
        )

    with col2:
        st.subheader(f"Curve: {selected_component}")
        if selected_component:
            comp_curve = curves[curves["component"] == selected_component]
            comp_status = module_a[module_a["component"] == selected_component]["status"].iloc[0]
            fig2 = go.Figure()
            fig2.add_trace(
                go.Scatter(
                    x=comp_curve["time"],
                    y=comp_curve["signal"],
                    mode="lines",
                    line=dict(color=STATUS_COLORS[comp_status], width=2),
                    name=selected_component,
                )
            )
            fig2.update_layout(
                height=450,
                xaxis_title="Time / Burn-in cycle",
                yaxis_title="Rds(on) / signal",
            )
            st.plotly_chart(fig2, width="stretch")
            st.markdown(f"**Status:** :{'red' if comp_status=='CRITICAL' else 'orange' if comp_status=='WATCH' else 'blue'}[{comp_status}]")

# ---------------------------------------------------------------------------
# Tab 2 -- Module B Forecast Visualizer
# ---------------------------------------------------------------------------
with tab_b:
    st.subheader(f"Early-window forecast: {selected_component}")

    b_row = module_b[module_b["component"] == selected_component]

    if b_row.empty:
        st.info("This component has no Module B result (its curve may have been too short to split into early/late windows).")
    else:
        b_row = b_row.iloc[0]
        comp_curve = curves[curves["component"] == selected_component].reset_index(drop=True)
        n = len(comp_curve)
        n_early = max(3, int(n * 0.2))
        n_late = max(3, int(n * 0.1))

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Early mean (observed)", f"{b_row['early_mean']:.2f}")
        col2.metric("Actual late value", f"{b_row['target_late_value']:.2f}")
        col3.metric("Predicted late value", f"{b_row['predicted_target']:.2f}")
        col4.metric(
            "Early-reject flag",
            "YES" if b_row["early_reject_flag"] else "no",
            delta=f"{b_row['predicted_change']:.1f} predicted change",
            delta_color="inverse" if b_row["early_reject_flag"] else "normal",
        )

        fig3 = go.Figure()
        fig3.add_trace(go.Scatter(
            x=comp_curve["time"], y=comp_curve["signal"],
            mode="lines", line=dict(color="lightgray", width=1.5),
            name="Full observed curve (for reference)",
        ))
        fig3.add_trace(go.Scatter(
            x=comp_curve["time"].iloc[:n_early], y=comp_curve["signal"].iloc[:n_early],
            mode="lines", line=dict(color="#4C72B0", width=3),
            name="Early window (used as input)",
        ))
        fig3.add_trace(go.Scatter(
            x=comp_curve["time"].iloc[-n_late:], y=comp_curve["signal"].iloc[-n_late:],
            mode="lines", line=dict(color="#55A868", width=3),
            name="Late window (actual target)",
        ))
        fig3.add_trace(go.Scatter(
            x=[comp_curve["time"].iloc[-n_late:].mean()],
            y=[b_row["predicted_target"]],
            mode="markers", marker=dict(size=14, color="#C44E52", symbol="x"),
            name="Predicted late value",
        ))
        fig3.update_layout(
            height=450,
            xaxis_title="Time / Burn-in cycle",
            yaxis_title="Rds(on) / signal",
            legend=dict(orientation="h", yanchor="bottom", y=1.02),
        )
        st.plotly_chart(fig3, width="stretch")
        st.caption(
            "Blue = the only data Module B is allowed to see. Green = what "
            "actually happened later. Red X = what the model predicted from "
            "the blue window alone, before the green data existed."
        )

# ---------------------------------------------------------------------------
# Tab 3 -- Explainability
# ---------------------------------------------------------------------------
with tab_explain:
    st.subheader(f"Why was {selected_component} classified this way?")

    a_row = module_a[module_a["component"] == selected_component].iloc[0]

    col1, col2 = st.columns([1, 1])
    with col1:
        st.markdown(f"**Status:** {a_row['status']}")
        st.markdown(f"**Risk score:** {a_row['risk_score']:.1f} / 100")
        st.markdown(f"**Plain-language reason:** {a_row['explanation']}")

        fig4 = go.Figure(go.Bar(
            x=["Anomaly percentile\n(55% weight)", "Drift percentile\n(45% weight)"],
            y=[a_row["anomaly_percentile"], a_row["drift_percentile"]],
            marker_color=["#4C72B0", "#DD8452"],
        ))
        fig4.add_hline(y=75, line_dash="dash", line_color="red", annotation_text="CRITICAL threshold")
        fig4.add_hline(y=50, line_dash="dash", line_color="orange", annotation_text="WATCH threshold")
        fig4.update_layout(height=350, yaxis_title="Percentile (0-100)", yaxis_range=[0, 100])
        st.plotly_chart(fig4, width="stretch")
        st.caption(
            "Risk score = 0.55 x anomaly percentile + 0.45 x drift percentile. "
            "This is the same blend used to assign NORMAL / WATCH / CRITICAL."
        )

    with col2:
        b_match = module_b[module_b["component"] == selected_component]
        if not b_match.empty:
            b_row = b_match.iloc[0]
            st.markdown("**Module B agreement check**")
            agree = b_row["early_reject_flag"] and a_row["status"] in ("WATCH", "CRITICAL")
            b_only = b_row["early_reject_flag"] and a_row["status"] == "NORMAL"
            if agree:
                st.success("Both modules agree this component is a concern.")
            elif b_only:
                st.warning(
                    "Module B flags this component for early rejection based on "
                    "its early readings, even though Module A's full-lifetime "
                    "view calls it NORMAL -- an early-warning catch."
                )
            else:
                st.info("Module B does not flag this component for early rejection.")

            st.metric("Predicted change", f"{b_row['predicted_change']:.2f}")
            st.metric("Actual change", f"{b_row['actual_change']:.2f}")
        else:
            st.info("No Module B result available for this component.")

# ---------------------------------------------------------------------------
# Tab 4 -- Full results table
# ---------------------------------------------------------------------------
with tab_table:
    st.subheader("All screened components")
    merged = module_a.merge(
        module_b[["component", "early_reject_flag", "predicted_change"]],
        on="component", how="left",
    )
    st.dataframe(
        merged[[
            "component", "status", "risk_score", "change_percent", "volatility",
            "early_reject_flag", "predicted_change", "explanation",
        ]].sort_values("risk_score", ascending=False),
        width="stretch",
        height=500,
    )
    st.download_button(
        "Download combined results as CSV",
        data=merged.to_csv(index=False).encode("utf-8"),
        file_name="burnin_screening_combined_results.csv",
        mime="text/csv",
    )
