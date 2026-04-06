import streamlit as st
import pandas as pd
import requests
import json
import time
from datetime import datetime
import os

# ============================================================
# PAGE CONFIG & CSS
# ============================================================
st.set_page_config(
    page_title="NEXUS V3 Enterprise",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
/* Full-Stack Enterprise UI 10k/mo Aesthetic */
:root {
    --bg-color: #0d1117;
    --card-bg: rgba(22, 27, 34, 0.6);
    --border: 1px solid rgba(139, 92, 246, 0.15);
    --primary: #c084fc;
    --text-primary: #e6edf3;
    --text-sec: #8b949e;
}

body {
    background-color: var(--bg-color);
    color: var(--text-primary);
    font-family: 'Inter', sans-serif;
}

.stApp {
    background: radial-gradient(circle at top, rgba(139,92,246,0.05) 0%, transparent 40%), var(--bg-color);
}

.hero {
    text-align: center;
    padding: 3rem 0;
}
.hero-title {
    font-size: 3rem;
    font-weight: 900;
    letter-spacing: -1px;
    margin-bottom: 0px;
    background: linear-gradient(90deg, #c084fc, #8b5cf6, #3b82f6);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}
.hero-sub {
    color: var(--text-sec);
    font-size: 1.1rem;
    margin-top: 0;
    text-transform: uppercase;
    letter-spacing: 2px;
}

.health-dot {
    height: 10px;
    width: 10px;
    background-color: #3fb950;
    border-radius: 50%;
    display: inline-block;
    margin-right: 5px;
    box-shadow: 0 0 8px #3fb950;
}

.health-offline {
    background-color: #f85149;
    box-shadow: 0 0 8px #f85149;
}

.prospect-card {
    background: var(--card-bg);
    border: var(--border);
    border-radius: 12px;
    padding: 1.5rem;
    margin-bottom: 1rem;
    backdrop-filter: blur(10px);
}
.card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 10px;
}
.score-badge {
    background: rgba(63, 185, 80, 0.1);
    color: #3fb950;
    padding: 4px 10px;
    border-radius: 20px;
    font-weight: 700;
    font-size: 0.85rem;
    border: 1px solid rgba(63, 185, 80, 0.3);
}

.log-container {
    background: #000;
    color: #0f0;
    font-family: 'Consolas', monospace;
    font-size: 0.8rem;
    padding: 10px;
    border-radius: 8px;
    max-height: 400px;
    overflow-y: auto;
    border: 1px solid #333;
}
</style>
""", unsafe_allow_html=True)

# ============================================================
# BACKEND CONNECTION UTILS
# ============================================================
BASE_URL = os.getenv("API_URL", "http://localhost:8000")

def ping_health():
    try:
        r = requests.get(f"{BASE_URL}/health", timeout=2)
        return r.status_code == 200
    except:
        return False

# ============================================================
# SIDEBAR
# ============================================================
with st.sidebar:
    st.markdown("""
    <div style="text-align:center;padding:1.2rem 0">
        <div style="font-size:2.5rem">💼</div>
        <div style="font-weight:800;color:#c084fc;font-size:1.15rem;">NEXUS ENTERPRISE</div>
    </div>""", unsafe_allow_html=True)
    st.divider()

    st.markdown("**🔑 Settings**")
    api_key = st.text_input("DeepSeek/GitHub API Token", type="password", help="Required for backend processing")
    model_choice = st.selectbox("LLM Engine", ["DeepSeek-R1", "gpt-4o", "gpt-4o-mini"], index=0)
    max_results = st.slider("Max Search Depth (Dork)", 5, 30, 10, 5)

    st.divider()
    observer_mode = st.toggle("🖥️ Admin Observer Panel", value=False, help="Enable to view raw backend logs")
    
    st.divider()
    
    # System Health Footer
    st.markdown("<br><br>", unsafe_allow_html=True)
    if ping_health():
        st.markdown(f"<div><span class='health-dot'></span><span style='color:#a5d6ff;font-size:0.8rem;font-weight:600'>API Connected</span></div>", unsafe_allow_html=True)
    else:
        st.markdown(f"<div><span class='health-dot health-offline'></span><span style='color:#f85149;font-size:0.8rem;font-weight:600'>API Offline</span></div>", unsafe_allow_html=True)
        st.error("Cannot connect to FastAPI backend. Ensure `uvicorn api:app` is running on port 8000.")

# ============================================================
# MAIN UI
# ============================================================
st.markdown("""
<div class="hero">
  <p class="hero-title">NEXUS ENTERPRISE PIPELINE</p>
  <p class="hero-sub">Decoupled Architecture • Full-Stack Data Mining</p>
</div>
""", unsafe_allow_html=True)

if 'prospects' not in st.session_state:
    st.session_state.prospects = []

tab_search, tab_prospects = st.tabs(["🚀 Command Center", "📊 Prospect Grid"])

with tab_search:
    
    if observer_mode:
        with st.expander("🖥️ Terminal Observer (nexus.log)", expanded=True):
            st.caption("Live streaming structured logging from the FastAPI backend.")
            try:
                with open("nexus.log", "r") as f:
                    logs = f.readlines()[-30:] # tail last 30 lines
                log_html = "".join([f"<div>{l}</div>" for l in logs])
                st.markdown(f"<div class='log-container'>{log_html}</div>", unsafe_allow_html=True)
            except Exception:
                st.write("nexus.log not found yet.")

    with st.form("intake_form"):
        st.subheader("Define Strategic Target Profile")
        omni_prompt = st.text_area(
            "🧠 Long-Tail Target Logic (Natural Language)",
            placeholder="e.g., Business coaches in the USA selling $25k+ masterminds who post on Instagram but suffer from low engagement due to poor video editing.",
            height=150
        )
            
        submitted = st.form_submit_button("Initiate Intelligence Architecture", use_container_width=True)
        
    if submitted:
        if not ping_health():
            st.error("Backend offline. Start the server.")
            st.stop()
        if not api_key:
            st.error("API Key required.")
            st.stop()
            
        payload_base = {
            "omni_prompt": omni_prompt,
            "api_key": api_key,
            "model_choice": model_choice,
            "max_results": max_results
        }
        
        # Phase 1: Compile Intent
        with st.status("🧠 1. Harvesting Intelligence Matrix...", expanded=True) as status_box:
            st.write("Connecting to FastAPI -> `/api/v1/compile-intent`")
            res_intent = requests.post(f"{BASE_URL}/api/v1/compile-intent", json=payload_base).json()
            
            if "detail" in res_intent:
                status_box.update(label="❌ Backend Error", state="error")
                st.error(res_intent["detail"])
                st.stop()
                
            schema = res_intent.get("extracted_schema", {})
            st.markdown("### Target Parameters Extracted")
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Persona", schema.get("Target_Persona", "N/A"))
            m2.metric("Geography", schema.get("Location_Constraint", "N/A"))
            m3.metric("Value", schema.get("Value_Marker", "N/A"))
            m4.metric("Platform", schema.get("Platform_Focus", "N/A"))
            st.info(f"**Target Pain Point:** {schema.get('Pain_Point', 'N/A')}")
                
            status_box.update(label="✅ Intent Verified & Pydantic Enforced", state="complete")
        
        # Phase 2: Execute Scrape
        with st.status("👻 2. Executing Omni-Vector Harvesting...", expanded=True) as search_box:
            st.write("Connecting to FastAPI -> `/api/v1/execute-search`")
            st.write("Executing targeted Dorks across vectors...")
            
            payload_search = {
                "compiled_params": schema,
                "platform_dorks": res_intent["platform_dorks"],
                "api_key": api_key,
                "model_choice": model_choice,
                "max_results": max_results
            }
            
            search_res = requests.post(f"{BASE_URL}/api/v1/execute-search", json=payload_search).json()
            
            if search_res.get("error"):
                st.error(f"Vector search issue: {search_res['error']}")
            
            raw = search_res.get("raw_leads_count", 0)
            qual = search_res.get("qualified_leads_count", 0)
            
            if raw == 0:
                search_box.update(label="⚠️ Validated 0 Targets", state="error")
                st.stop()
                
            st.write(f"Harvested {raw} targets. Filtered to {qual} Validated Prospects.")
            search_box.update(label=f"✅ Operations Completed: {qual} Leads Captured", state="complete")
            
        st.session_state.prospects = search_res.get("qualified_leads", [])
        st.success(f"Successfully generated Prospecting List in Memory.")

with tab_prospects:
    if not st.session_state.prospects:
        st.info("No active prospects loaded. Awaiting intelligence matrix launch.")
    else:
        # Detailed Grid with Color Grading
        for lead in st.session_state.prospects:
            col_score, col_title, col_platform = st.columns([1, 6, 2])
            score = lead.get('Match_Score', 0)
            
            color = "#3fb950" if score >= 85 else "#d29922" # Green vs Yellow
            label = "BULLSEYE" if score >= 85 else "POTENTIAL"
            
            with col_score:
                st.markdown(f"<div class='score-badge' style='color:{color};border-color:{color}'>{score}% {label}</div>", unsafe_allow_html=True)
                
            with col_title:
                st.markdown(f"<strong style='color:#c084fc;font-size:1.1rem;'>{lead.get('Title','Unknown Prospect')}</strong>", unsafe_allow_html=True)
                
            with col_platform:
                st.caption(f"[ {lead.get('Platform')} Target ]")
            
            with st.expander("View 1x1 Prospect Sales Dashboard"):
                st.markdown(f"**Enterprise Fit Evaluation (Pain Point Trigger Score: {lead.get('Pain_Point_Match',0)})**")
                st.markdown(f"<div style='border-left:3px solid #c084fc;padding-left:14px;color:#8b949e'>{lead.get('Snippet')}</div>", unsafe_allow_html=True)
                st.markdown("---")
                st.markdown(f"**📝 Generative Sales Icebreaker:**\n> {lead.get('COPY_Pitch')}")
                st.markdown(f"📧 **Captured Email:** `{lead.get('Validated_Email', 'N/A')}`")
                st.markdown(f"🌐 **LinkedIn Vector:** {lead.get('URL')}")
        
        # Download Option
        if st.session_state.prospects:
            df = pd.DataFrame([{
                "Company / Prospect Name": p.get("Title"),
                "Match Threshold": f"{p.get('Match_Score',0)}%",
                "Validated Email": p.get("Validated_Email", "N/A"),
                "Profile URL": p.get("URL", ""),
                "Sales Icebreaker": p.get("COPY_Pitch", "")
            } for p in st.session_state.prospects])
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button("Export Decoupled Pipeline (CSV)", csv, "B2B_Pipeline.csv", "text/csv")