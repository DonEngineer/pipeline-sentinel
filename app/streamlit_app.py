"""Streamlit dashboard: source health, incidents, and check history.

Reads the JSONL logs written by the CLI under the sentinel directory.
Run checks from here or from the CLI::

    python -m pipeline_sentinel.cli check --config sentinel.yaml
    streamlit run app/streamlit_app.py
"""

from __future__ import annotations

import streamlit as st

from pipeline_sentinel import history
from pipeline_sentinel.config import settings

SEVERITY_ICONS = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢"}

st.set_page_config(page_title="Pipeline Sentinel", layout="wide")
st.title("Pipeline Sentinel")
st.caption("Agentic data pipeline watchdog")

with st.sidebar:
    st.header("Settings")
    sentinel_dir = st.text_input("State directory", value=settings.sentinel_dir)
    config_path = st.text_input("Suite config", value="sentinel.yaml")
    if st.button("Run checks now"):
        from pipeline_sentinel.cli import run_suite

        with st.spinner("Running checks..."):
            run_suite(config_path)
        st.rerun()
    if st.button("Refresh"):
        st.rerun()

check_history = history.read_history(sentinel_dir, limit=500)
incidents = history.read_incidents(sentinel_dir, limit=100)

latest: dict[tuple[str, str], dict] = {}
for entry in check_history:
    latest[(entry["source"], entry["check"])] = entry

st.header("Source health")
if not latest:
    st.info(
        "No check history yet. Run: `python -m pipeline_sentinel.cli check --config sentinel.yaml`"
    )
else:
    sources = sorted({source for source, _ in latest})
    cols = st.columns(len(sources))
    for col, source in zip(cols, sources):
        with col:
            st.subheader(source)
            for (name, check), entry in sorted(latest.items()):
                if name != source:
                    continue
                icon = "🟢" if entry["passed"] else "🔴"
                st.write(f"{icon} `{check}` — metric `{entry['metric']}`")

st.header("Incidents")
if not incidents:
    st.info("No incidents triaged yet.")
else:
    for incident in reversed(incidents):
        icon = SEVERITY_ICONS.get(incident["severity"], "⚪")
        header = f"{icon} [{incident['severity'].upper()}] {incident['title']}"
        with st.expander(header):
            st.write(f"**ID:** `{incident['id']}`")
            st.write(f"**Probable cause:** {incident['probable_cause']}")
            st.write(f"**Suggested action:** {incident['suggested_action']}")
            st.write(f"**Failed checks:** {', '.join(incident['failed_checks'])}")
            st.write(f"**Created:** {incident['created_at']}")

st.header("Check history")
if check_history:
    rows = [
        {
            "checked_at": entry["checked_at"],
            "source": entry["source"],
            "check": entry["check"],
            "passed": entry["passed"],
            "metric": entry["metric"],
        }
        for entry in reversed(check_history[-50:])
    ]
    st.dataframe(rows, use_container_width=True)
