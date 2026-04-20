import streamlit as st
import json
from llm_client import call_llm
from prompts import INTAKE_PREFILL

def analyze_idea(idea_text):
    # Prepare messages for LLM
    messages = [
        {"role": "system", "content": "You are a helpful startup mentor extracting information from an idea."},
        {"role": "user", "content": INTAKE_PREFILL.format(raw_input=idea_text)}
    ]
    
    # Call LLM for pre-fill
    response = call_llm(messages, json_mode=True)
    
    if response:
        try:
            # Parse the JSON response
            prefill_data = json.loads(response)
            
            # Update canvas with pre-filled fields
            st.session_state.canvas["idea"]["one_liner"] = prefill_data.get("one_liner")
            st.session_state.canvas["idea"]["problem"] = prefill_data.get("problem")
        except json.JSONDecodeError:
            st.error("There was an error parsing the AI response. Let's proceed anyway.")
    else:
        st.error("The AI could not analyze your idea right now. Let's proceed anyway.")

def render_intake():

    with st.container(horizontal=True, vertical_alignment="center", gap=None):
        st.image('src/assets/logo.svg', width=70)
        st.title("FounderLens")
        
    st.markdown('<h3 style="letter-spacing: 0.8px;">Turn your <span style="background-color: #508757; padding: 2px 4px; border-radius: 3px;">startup idea</span> into a <span style="background-color: #f5f5e9; color: #272927; padding: 2px 4px; border-radius: 3px;">validated business model</span>.</h2>', unsafe_allow_html=True)
    # st.subheader('Turn your startup idea into a validated business model.')
    
    st.markdown("""
    Describe your startup idea. Don't worry about being perfect — just tell us what
    you're trying to build and who it's for.
    """)

    
    # Chat input for the idea
    # ENHANCE: Add File and Audio input options, the return value then will be a dict, so modification required
    idea_text = st.chat_input(
        placeholder="e.g., A platform for local farmers to sell their produce to nearby grocery stores...",
        width="stretch",
        height=200
    )
    
    if idea_text:
        if not idea_text.strip():
            st.warning("Please describe your idea before starting.")
            return

        with st.spinner("Analyzing your idea..."):
            # Update canvas with raw input
            st.session_state.canvas["idea"]["raw_input"] = idea_text
            
            # Analyze the idea
            analyze_idea(idea_text)
            
            # Transition to interview stage
            st.session_state.canvas["stage"] = "interview"
            
            # Rerun to render next stage
            st.rerun()
