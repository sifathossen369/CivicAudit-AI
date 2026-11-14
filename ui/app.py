import streamlit as st
import json
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import sys

# Ensure root dir in path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from config import AuditConfig
from core.agents.auditor_orchestrator import CivicAuditOrchestrator
from core.tools.dossier_generator import DossierGeneratorTool
from core.models import AuditDossier

st.set_page_config(
    page_title="CivicAudit AI - Autonomous Procurement Forensic Engine",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling
st.markdown("""
<style>
    .metric-card {
        background-color: #1e293b;
        border-radius: 10px;
        padding: 18px;
        border: 1px solid #334155;
        text-align: center;
    }
    .metric-title {
        color: #94a3b8;
        font-size: 0.85rem;
        font-weight: 600;
        text-transform: uppercase;
        margin-bottom: 5px;
    }
    .metric-value {
        color: #f8fafc;
        font-size: 1.8rem;
        font-weight: 700;
    }
    .metric-danger {
        color: #ef4444 !important;
    }
    .metric-success {
        color: #10b981 !important;
    }
    .badge-critical {
        background-color: #dc2626;
        color: white;
        padding: 4px 8px;
        border-radius: 4px;
        font-size: 0.75rem;
        font-weight: bold;
    }
    .badge-warning {
        background-color: #d97706;
        color: white;
        padding: 4px 8px;
        border-radius: 4px;
        font-size: 0.75rem;
        font-weight: bold;
    }
    .badge-normal {
        background-color: #059669;
        color: white;
        padding: 4px 8px;
        border-radius: 4px;
        font-size: 0.75rem;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# Sidebar
st.sidebar.image("https://img.icons8.com/fluency/96/courthouse.png", width=64)
st.sidebar.title("CivicAudit AI")
st.sidebar.caption("Autonomous Public Procurement Oversight & Price-Gouging Anomaly Engine")
st.sidebar.divider()

st.sidebar.subheader("1. Procurement Selection")
sample_files = list(AuditConfig.SAMPLES_DIR.glob("*.json"))
sample_options = {f.name: f for f in sample_files}

selected_sample = st.sidebar.selectbox(
    "Choose Procurement Docket:",
    options=list(sample_options.keys()),
    index=0 if sample_options else None
)

uploaded_file = st.sidebar.file_uploader("Or Upload Custom Tender JSON:", type=["json"])

st.sidebar.divider()
st.sidebar.subheader("2. Forensic Parameters")
currency = st.sidebar.selectbox("Currency Unit:", ["USD ($)", "EUR (€)", "BDT (৳)", "GBP (£)"], index=0)
curr_symbol = currency.split("(")[-1].replace(")", "")
AuditConfig.DEFAULT_CURRENCY = curr_symbol

critical_threshold = st.sidebar.slider(
    "Critical Gouging Alert Threshold (%):",
    min_value=40,
    max_value=150,
    value=75,
    step=5
)
AuditConfig.CRITICAL_THRESHOLD_PERCENT = float(critical_threshold)

run_button = st.sidebar.button("🚀 Execute Autonomous Audit", type="primary", use_container_width=True)

# Main Dashboard View
st.title("🏛️ CivicAudit Autonomous Forensic Platform")
st.caption("AI-Powered Due Diligence & Price-Gouging Discovery for Municipal & State Tenders")

# Load Target Data
tender_data = None
if uploaded_file is not None:
    tender_data = json.load(uploaded_file)
elif selected_sample and sample_options:
    with open(sample_options[selected_sample], "r", encoding="utf-8") as f:
        tender_data = json.load(f)

if not tender_data:
    st.info("Please select or upload a procurement tender from the sidebar.")
    st.stop()

# Display Tender Basic Details
col_meta1, col_meta2, col_meta3 = st.columns([2, 1, 1])
with col_meta1:
    st.markdown(f"**Tender Title:** `{tender_data.get('title', 'Unknown')}`")
    st.markdown(f"**Procuring Authority:** {tender_data.get('procuring_entity', 'Public Entity')}")
with col_meta2:
    st.markdown(f"**Dossier Reference:** `{tender_data.get('tender_id', 'TND-000')}`")
with col_meta3:
    st.markdown(f"**Submission Date:** `{tender_data.get('submission_date', 'N/A')}`")

st.divider()

if run_button or "current_dossier" in st.session_state:
    if run_button:
        # Run Live Agent Pipeline
        agent_logs = []
        progress_bar = st.progress(0)
        status_box = st.empty()

        def ui_callback(phase, msg, data=None):
            agent_logs.append(f"[{phase}] {msg}")
            status_box.info(f"🤖 **Forensic Agent Working:** {msg}")

        orchestrator = CivicAuditOrchestrator(step_callback=ui_callback)
        progress_bar.progress(25)
        
        dossier = orchestrator.audit_tender(
            tender_id=tender_data.get("tender_id", "TND-999"),
            title=tender_data.get("title", "Public Municipal Tender"),
            procuring_entity=tender_data.get("procuring_entity", "Government Municipal Board"),
            tender_source_data=tender_data
        )
        progress_bar.progress(100)
        status_box.empty()
        st.session_state["current_dossier"] = dossier
        st.session_state["agent_logs"] = agent_logs

    dossier: AuditDossier = st.session_state["current_dossier"]

    # Top KPI Metrics Row
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Total Quoted Budget</div>
            <div class="metric-value">{curr_symbol}{dossier.total_quoted_budget:,.2f}</div>
        </div>
        """, unsafe_allow_html=True)
    with m2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Fair Market Value</div>
            <div class="metric-value metric-success">{curr_symbol}{dossier.fair_market_estimated_budget:,.2f}</div>
        </div>
        """, unsafe_allow_html=True)
    with m3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Taxpayer Money at Risk</div>
            <div class="metric-value metric-danger">{curr_symbol}{dossier.potential_taxpayer_loss:,.2f}</div>
        </div>
        """, unsafe_allow_html=True)
    with m4:
        score_color = "metric-danger" if dossier.risk_score >= 60 else "metric-warning"
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Corruption Risk Score</div>
            <div class="metric-value {score_color}">{dossier.risk_score} / 100</div>
        </div>
        """, unsafe_allow_html=True)

    st.write("")
    
    # Risk Alert Banner
    if dossier.risk_score >= 60:
        st.error(f"🚨 **HIGH RISK AUDIT ALERT ({dossier.risk_tier}):** {dossier.executive_summary}")
    elif dossier.risk_score >= 35:
        st.warning(f"⚠️ **ELEVATED RISK NOTICE:** {dossier.executive_summary}")
    else:
        st.success(f"✅ **NORMAL PROCUREMENT STATUS:** {dossier.executive_summary}")

    st.divider()

    # Visual Analytics & Table
    tab1, tab2, tab3 = st.tabs(["📊 Price Anomaly Visualization", "📑 Full Bill of Quantities Audit", "🛡️ Statutory & Legal Violations"])

    with tab1:
        # Chart: Quoted vs Fair Market Price
        chart_data = []
        for f in dossier.findings:
            chart_data.append({"Item": f.item_name[:24], "Type": "Quoted Rate", "Amount": f.quoted_unit_price})
            chart_data.append({"Item": f.item_name[:24], "Type": "Market Fair Rate", "Amount": f.fair_market_unit_price})
        
        df_chart = pd.DataFrame(chart_data)
        fig = px.bar(
            df_chart,
            x="Item",
            y="Amount",
            color="Type",
            barmode="group",
            title="Quoted Unit Price vs. Verified Fair Market Benchmark",
            color_discrete_map={"Quoted Rate": "#ef4444", "Market Fair Rate": "#10b981"},
            labels={"Amount": f"Unit Price ({curr_symbol})"}
        )
        fig.update_layout(template="plotly_dark", height=420)
        st.plotly_chart(fig, use_container_width=True)

    with tab2:
        # Table of Findings
        table_rows = []
        for f in dossier.findings:
            table_rows.append({
                "BOQ ID": f.item_id,
                "Description": f.item_name,
                "Quantity": f.quantity,
                f"Quoted ({curr_symbol})": f"${f.quoted_unit_price:,.2f}",
                f"Market Fair ({curr_symbol})": f"${f.fair_market_unit_price:,.2f}",
                "Markup %": f"{f.gouging_percentage:+.1f}%",
                f"Fiscal Loss ({curr_symbol})": f"${f.variance_total:,.2f}",
                "Status": f.risk_level,
                "Benchmark Source": f.evidence_source
            })
        df_table = pd.DataFrame(table_rows)
        st.dataframe(df_table, use_container_width=True, hide_index=True)

    with tab3:
        st.subheader("⚖️ Legal Compliance & Integrity Assessment")
        col_l1, col_l2 = st.columns(2)
        with col_l1:
            st.markdown("#### Detected Violations:")
            if dossier.legal_statutory_violations:
                for v in dossier.legal_statutory_violations:
                    st.markdown(f"- 🔴 **{v}**")
            else:
                st.markdown("No direct statutory threshold violations detected.")
        
        with col_l2:
            st.markdown("#### Mandatory Action Checklist:")
            for a in dossier.immediate_actions_recommended:
                st.markdown(f"- 📋 {a}")

    # Export Dossier
    st.divider()
    col_dl1, col_dl2 = st.columns([3, 1])
    with col_dl1:
        st.caption(f"Forensic Dossier compiled autonomously by CivicAudit Core Engine.")
    with col_dl2:
        markdown_dossier = DossierGeneratorTool.render_markdown(dossier)
        st.download_button(
            label="📥 Download Official Audit Dossier (.md)",
            data=markdown_dossier,
            file_name=f"CivicAudit_Dossier_{dossier.tender_id}.md",
            mime="text/markdown",
            use_container_width=True
        )

else:
    st.info("👈 Click **'Execute Autonomous Audit'** in the sidebar to initiate the AI forensic investigation.")
