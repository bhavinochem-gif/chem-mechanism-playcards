import streamlit as st
import os
import tempfile
from modules.deterministic_matcher import DeterministicChemistryEngine
from modules.pdf_parser import extract_pdf_text, detect_candidate_reactions
from modules.pdf_exporter import generate_mechanism_dossier_pdf
from modules.chem_renderer import smarts_reaction_to_svg

st.set_page_config(
    page_title="ChemMechAI | Play Card & Mechanism Dossier Engine",
    page_icon="⚗️",
    layout="wide"
)

# Custom Styling for Play Card and Responsive Metrics
st.markdown("""
<style>
  .playcard-front {
    background-color: #f8fafc;
    border: 2px solid #3b82f6;
    border-radius: 8px;
    padding: 16px;
    margin-bottom: 12px;
  }
  .playcard-back {
    background-color: #ffffff;
    border: 2px solid #10b981;
    border-radius: 8px;
    padding: 16px;
    margin-bottom: 12px;
  }
  .step-box {
    background: #f1f5f9;
    border-left: 4px solid #2563eb;
    padding: 8px 12px;
    margin: 6px 0;
    border-radius: 4px;
  }
</style>
""", unsafe_allow_html=True)

# Initialize Engine
@st.cache_resource
def get_engine():
    return DeterministicChemistryEngine("data/chemistry_master_db.json")

engine = get_engine()

# Sidebar: Configurations
with st.sidebar:
    st.header("⚙️ Engine Architecture")
    st.markdown("""
    **Deterministic Priority Hierarchy:**
    1. 🧠 **Offline Master DB** *(Named reactions, SMARTS, pKa)*
    2. 🌐 **PubChem REST API** *(Live Web Index)*
    3. 🔑 **AI API Key Fallback** *(Last resort)*
    """)
    api_key = st.text_input(
        "Tier 3 Fallback API Key (Optional)", 
        type="password", 
        help="Used strictly if query fails offline matching."
    )
    st.info(f"Loaded {len(engine.named_rxns)} core reaction classes, {len(engine.pka_scales)} pKa scales, and {len(engine.protecting_groups)} protecting group rules.")

st.title("⚗️ Chemical Reaction Mechanism Play Card Engine")
st.caption("Automatic mechanism deduction, electron-pushing analysis, and PDF dossier compiler")

tab1, tab2 = st.tabs(["📄 Upload Synthetic Route PDF", "🔍 Manual Pathway Query"])

query_target = None
source_label = None

with tab1:
    pdf_file = st.file_uploader("Upload Synthetic Route Literature / Patent (PDF)", type=["pdf"])
    if pdf_file is not None:
        with st.spinner("Extracting text and scanning for chemical schemes..."):
            extracted_text = extract_pdf_text(pdf_file)
            detected_rxns = detect_candidate_reactions(extracted_text, engine.named_rxns)

        st.success(f"PDF processed successfully. Detected {len(detected_rxns)} reaction candidates.")
        
        with st.expander("Show Extracted Document Text Preview"):
            st.text(extracted_text[:1200] + ("..." if len(extracted_text) > 1200 else ""))

        if detected_rxns:
            query_target = st.selectbox("Select Detected Transformation to Analyze:", detected_rxns)
            source_label = "PDF Ingestion Scan"
        else:
            st.warning("No standard named reactions detected automatically from text. Switch to Manual Pathway Query or enter below:")
            manual_fallback = st.text_input("Enter target transformation from PDF:")
            if manual_fallback:
                query_target = manual_fallback
                source_label = "User Specified from PDF"

with tab2:
    manual_input = st.text_input("Enter Reaction Name, Reagents, or Class (e.g., 'Suzuki-Miyaura', 'Swern', 'Diels-Alder'):")
    if manual_input:
        query_target = manual_input
        source_label = "Manual Search"

# Execution & Resolution Pipeline
if query_target:
    st.markdown("---")
    st.subheader(f"Mechanism Analysis: **{query_target}**")

    with st.spinner("Running deterministic resolution cascade..."):
        result = engine.resolve(query_target, api_key=api_key)

    source = result["source"]
    status = result["status"]
    data = result["data"]

    # Resolution Status Banner
    col_stat1, col_stat2 = st.columns([3, 1])
    with col_stat1:
        st.markdown(f"**Resolution Tier:** `{source}`")
    with col_stat2:
        if status == "MATCHED":
            st.success(f"Confidence: {int(result.get('confidence', 1.0) * 100)}%")
        else:
            st.error("Unresolved")

    if status == "MATCHED":
        # 2D Reaction Scheme Visualization (if SMARTS exists)
        if "smarts" in data:
            svg = smarts_reaction_to_svg(data["smarts"])
            if svg:
                st.image(f"data:image/svg+xml;utf8,{svg}", caption="Overall 2D Transformation Scheme", use_container_width=True)

        col_front, col_back = st.columns(2)

        with col_front:
            st.markdown("### 🎴 Play Card: Front (Challenge & Setup)")
            st.markdown(f"""
            <div class="playcard-front">
              <h4 style="margin-top:0; color:#1e40af;">{data.get('name', query_target)}</h4>
              <p><strong>Reaction Class:</strong> {data.get('class', 'General Synthesis')}</p>
              <p><strong>Rate Law:</strong> <code>{data.get('rate_law', 'Experimental Determination Required')}</code></p>
              <p><strong>Stereochemical Outcome:</strong> {data.get('stereochemistry', 'Stereospecific / Retention / Inversion')}</p>
              <p><strong>Solvent Preference:</strong> {', '.join(data.get('solvents', ['Standard organic solvents'])) if isinstance(data.get('solvents'), list) else data.get('solvents', 'N/A')}</p>
            </div>
            """, unsafe_allow_html=True)

        with col_back:
            st.markdown("### 🔄 Play Card: Back (Mechanism & Solution)")
            if "mechanism_steps" in data:
                for s in data["mechanism_steps"]:
                    st.markdown(f"""
                    <div class="step-box">
                      <strong>Step {s.get('step', 1)}: {s.get('name', 'Elementary Step')}</strong><br>
                      &bull; <strong>Electron Flow:</strong> <code>{s.get('electron_source', 'HOMO')}</code> &rarr; <code>{s.get('electron_sink', 'LUMO')}</code><br>
                      &bull; <strong>Intermediate:</strong> {s.get('intermediate', 'Reactive Complex')}<br>
                      &bull; <span style="color:#2563eb;"><strong>Driving Force:</strong> {s.get('driving_force', 'Thermodynamic equilibrium')}</span>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.json(data)

        # PDF Compilation & Export
        st.markdown("---")
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_pdf:
            generate_mechanism_dossier_pdf(query_target, source, data, tmp_pdf.name)
            pdf_bytes = open(tmp_pdf.name, "rb").read()

        st.download_button(
            label="📥 Download Publication-Ready Mechanism Dossier (PDF)",
            data=pdf_bytes,
            file_name=f"{query_target.replace(' ', '_')}_Mechanism_Dossier.pdf",
            mime="application/pdf"
        )
    else:
        st.warning(data.get("message"))
        st.info("Tip: Enter an API key in the left sidebar to generate dynamic mechanisms for unindexed or novel reactions.")
