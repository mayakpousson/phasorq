"""Student-facing Streamlit experiment lab."""

import pandas as pd
import plotly.express as px
import streamlit as st

from src.experiments import EXPERIMENTS
from src.profiles import PROFILES
from src.records import (
    ExperimentConfig, SHOT_OPTIONS, record_from_json, report_html, results_csv,
)
from src.runner import run_comparison


st.set_page_config(page_title="PhasorQ Experiment Lab", page_icon="⚛️", layout="wide")
st.title("PhasorQ Experiment Lab")
st.caption("Plan a small quantum experiment, compare simulations, and take home the evidence.")
st.info("All built-in runs use synthetic hardware models. No real quantum job, account, or payment is involved.")

if "records" not in st.session_state:
    st.session_state.records = []

experiment_tab, results_tab, about_tab = st.tabs(
    ["1 · Choose and run", "2 · Results and reports", "How this works"]
)

with experiment_tab:
    st.subheader("Choose an experiment")
    experiment_key = st.selectbox(
        "Experiment", list(EXPERIMENTS),
        format_func=lambda key: EXPERIMENTS[key].name,
    )
    experiment = EXPERIMENTS[experiment_key]
    st.markdown(f"**Question:** {experiment.question}")
    st.write(experiment.explanation)

    profile_key = st.selectbox(
        "Illustrative hardware", list(PROFILES),
        format_func=lambda key: PROFILES[key].name,
        help="A fixed, five-qubit synthetic processor. These are teaching examples, not live calibration data.",
    )
    st.caption(PROFILES[profile_key].description)
    shots = st.select_slider(
        "Measurements (shots)", options=SHOT_OPTIONS, value=1024,
        help="A shot is one repeated execution and measurement of the circuit.",
    )
    with st.expander("Repeatability settings"):
        seed = st.number_input("Random seed", min_value=0, max_value=2_147_483_647,
                               value=42, step=1)
        st.caption("Keeping the same seed and software versions makes a simulation reproducible.")

    if st.button("Run comparison", type="primary"):
        try:
            with st.spinner("Compiling and simulating both configurations…"):
                record = run_comparison(ExperimentConfig(experiment_key, profile_key,
                                                         int(shots), int(seed)))
            st.session_state.records.insert(0, record)
            st.success("Comparison complete. Open Results and reports to inspect it.")
        except Exception as exc:
            st.error(f"The simulation could not finish: {exc}")

with results_tab:
    uploaded = st.file_uploader("Import a PhasorQ JSON record", type="json")
    if uploaded is not None and st.button("Import record"):
        try:
            incoming = record_from_json(uploaded.getvalue())
            if any(record.record_id == incoming.record_id for record in st.session_state.records):
                st.info("That record is already in this session.")
            else:
                st.session_state.records.insert(0, incoming)
                st.success("Record imported into this browser session.")
        except ValueError as exc:
            st.error(f"Could not import record: {exc}")

    if not st.session_state.records:
        st.write("Run an experiment or import a record to see results here.")
    else:
        selected_id = st.selectbox(
            "Experiment history", [record.record_id for record in st.session_state.records],
            format_func=lambda identifier: next(
                f"{EXPERIMENTS[record.config.experiment_key].name} · "
                f"{'Imported hardware' if record.source == 'imported_hardware' else 'Simulation'} · "
                f"{record.created_at_utc[:19]} UTC"
                for record in st.session_state.records if record.record_id == identifier
            ),
        )
        selected = next(record for record in st.session_state.records
                        if record.record_id == selected_id)
        details = EXPERIMENTS[selected.config.experiment_key]
        st.subheader(details.name)
        st.write(details.question)
        if selected.source == "imported_hardware":
            st.warning("User-imported hardware result. PhasorQ has not verified provider provenance. "
                       "The synthetic simulations are illustrative and are not calibrated to this device.")
            st.caption(f"Backend: {selected.metadata['backend']} · Job: {selected.metadata['job_id']}")
            if selected.metadata.get("charge") is not None:
                st.caption(f"Recorded charge: {selected.metadata['charge']} provider credit units")
        else:
            st.caption(f"Synthetic profile: {PROFILES[selected.config.profile_key].name} · "
                       f"Shots per method: {selected.config.shots} · Seed: {selected.config.seed}")

        summary = pd.DataFrame([
            {
                "Method": trial.method.replace("_", " ").title(),
                "Distance from expected": round(trial.distance, 4),
                "Depth": trial.depth if trial.depth is not None else "Unknown",
                "Two-qubit gates": (trial.two_qubit_gates if trial.two_qubit_gates is not None
                                    else "Unknown"),
                "Proposed layout": (str(trial.proposed_layout) if trial.proposed_layout
                                    is not None else "—"),
                "Final layout": (str(trial.final_layout) if trial.final_layout
                                 is not None else "Unknown"),
            }
            for trial in selected.trials
        ])
        st.dataframe(summary, hide_index=True, width="stretch")
        st.caption("Distance from expected compares measured bitstrings. Lower is closer; "
                   "it is not quantum-state fidelity.")

        if len(selected.trials) == 2:
            baseline, alternative = selected.trials
            gap = baseline.distance - alternative.distance
            if abs(gap) < 1e-12:
                st.info("Both methods have the same measured distance in this run.")
            elif gap > 0:
                st.success(f"PhasorQ's proposed layout was closer by {gap:.3f} in this run.")
            else:
                st.warning(f"Qiskit's default layout was closer by {-gap:.3f} in this run.")
            st.caption("A single run can vary through measurement sampling. Compare repeated runs "
                       "before drawing a general conclusion.")

        outcomes = sorted(set(details.expected) |
                          {bits for trial in selected.trials for bits in trial.counts})
        rows = [{"Outcome": bits, "Probability": details.expected.get(bits, 0.),
                 "Series": "Ideal"} for bits in outcomes]
        for trial in selected.trials:
            rows.extend({"Outcome": bits,
                         "Probability": trial.counts.get(bits, 0) / selected.config.shots,
                         "Series": trial.method.replace("_", " ").title()}
                        for bits in outcomes)
        figure = px.bar(pd.DataFrame(rows), x="Outcome", y="Probability", color="Series",
                        barmode="group", range_y=[0, 1],
                        title="Expected and observed measurement outcomes")
        st.plotly_chart(figure, width="stretch")
        if selected.config.experiment_key == "bv":
            for trial in selected.trials:
                correct = trial.counts.get("101", 0) / selected.config.shots
                st.write(f"{trial.method.replace('_', ' ').title()}: "
                         f"correct answer 101 in {correct:.1%} of shots.")

        a, b, c = st.columns(3)
        with a:
            st.download_button("Download JSON record", selected.to_json(),
                               file_name=f"phasorq-{selected.record_id}.json", mime="application/json")
        with b:
            st.download_button("Download CSV data", results_csv(selected),
                               file_name=f"phasorq-{selected.record_id}.csv", mime="text/csv")
        with c:
            st.download_button("Download HTML report", report_html(selected),
                               file_name=f"phasorq-{selected.record_id}.html", mime="text/html")
        st.caption("History lasts for this browser session. Download a record to keep or share it.")

with about_tab:
    st.subheader("What a comparison means")
    st.write("Qiskit chooses a standard physical layout. PhasorQ first ranks qubits by a "
             "simple health score, then Qiskit compiles that proposal to the same five-qubit "
             "device. Routing can add gates and make either choice worse.")
    st.write("The ideal bars show what an error-free circuit should measure. The other bars "
             "come from a noisy simulator. More shots can make estimates steadier, but they do "
             "not remove systematic device errors.")
    with st.expander("About the old success estimate"):
        st.write("The original project multiplied average gate-survival and coherence terms. "
                 "That was an unvalidated heuristic, not a measured probability of a useful "
                 "answer. This lab evaluates actual simulated outcome distributions instead.")
    st.write("Future hardware studies can import results from Open Quantum. The public website "
             "does not submit jobs or store quantum-cloud credentials.")
