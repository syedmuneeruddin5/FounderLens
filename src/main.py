import streamlit as st
from ui.intake import render_intake
from ui.interview import render_interview

st.set_page_config(
    page_title="FounderLens",
    page_icon="src/assets/logo.svg"  # can be PNG, JPG, or emoji
)
st.logo("src/assets/logo.svg", size="large")

STAGES = [
    "intake",
    "interview",
    "synthesis",
    "review",
    "complete"
]

if "canvas" not in st.session_state:
    st.session_state.canvas = {
    "stage": "intake",  # enum: intake | interview | synthesis | review | complete

    "idea": {
        "raw_input": None,       # str — founder's original free-text idea from Stage 1
        "one_liner": None,       # str — one sentence summary extracted by AI
        "problem": None,         # str — the core problem being solved
        "solution": None,        # str — the proposed solution in 2-3 sentences
        "why_now": None          # str — timing rationale
    },

    "audience": {
        "primary_segment": None,        # str — specific customer segment, not broad demographic
        "early_adopter_profile": None,  # str — most specific description of who buys first
        "pain_description": None,       # str — what the pain feels like from customer's view
        "current_alternatives": None,   # str — how they solve this today without the product
        "willingness_to_pay": None      # enum: yes_paying | yes_free_tools | nothing | unsure
    },

    "market": {
        "tam_estimate": None,           # str — rough total addressable market with reasoning
        "sam_estimate": None,           # str — serviceable addressable market
        "size_bucket": None,            # enum: thousands | hundreds_of_thousands | millions | unsure
        "timing_signal": None,          # str — specific trend or event the founder is riding
        "market_signal_strength": None  # enum: strong | moderate | weak | none
    },

    "solution": {
        "description": None,        # str — what the product actually does
        "key_differentiator": None, # str — what it does that nothing else does
        "ten_x_claim": None,        # str — why meaningfully better, not just different
        "mvp_scope": None           # str — smallest useful version
    },

    "competition": {
        "alternatives": [],             # list[str] — top 2-3 existing alternatives
        "alternatives_shortfall": None, # str — why existing alternatives fall short
        "differentiation": None,        # str — how this product differs from all alternatives
        "unfair_advantage": None,       # str — what is genuinely hard to copy
        "advantage_type": None          # enum: domain_expertise | proprietary_data |
                                        #       network_effects | first_mover |
                                        #       team_background | unsure
    },

    "business_model": {
        "revenue_type": None,      # enum: subscription | one_time | commission |
                                   #       freemium | usage_based | unsure
        "who_pays": None,          # enum: user | business | advertiser | unsure
        "price_hypothesis": None,  # str — what a first customer would pay
        "price_bucket": None,      # enum: under_10 | 10_to_50 | 50_to_200 | over_200 | not_paid
        "cost_structure": None,    # str — main cost drivers
        "channels": None,          # str — how customers are reached
        "key_metrics": None        # str — the one number that signals this is working
    },

    "founder": {
        "background_relevance": None,  # str — why this founder for this problem
        "known_vs_guessed": None,      # str — what is evidence-based vs assumed
        "validation_done": None,       # enum: talked_to_users | built_prototype | both | nothing_yet
        "validation_plan": None        # str — how to test the riskiest assumption cheaply
    },

    "risks": [
        # Each entry is a dict:
        # {
        #   "assumption": str,           — a specific thing that must be true for this to work
        #   "risk_level": str,           — "high" | "medium" | "low"
        #   "validation_method": str,    — how to test this cheaply and quickly
        #   "is_riskiest": bool          — True for the single most critical assumption
        # }
    ],

    "conversation_history": [
        # Built up incrementally during Stage 2.
        # One entry appended per founder answer.
        # Primary input to the synthesis extraction call.
        # {
        #   "dimension": str,        — which of the 7 dimensions this exchange targets
        #   "question": str,         — exact question shown to the founder
        #   "question_format": str,  — open_text | multiple_choice | scale | yes_no
        #   "answer": str,           — founder's exact answer
        #   "probe_triggered": bool  — whether a follow-up probe was asked next
        # }
    ],

    "dimensions_covered": {
        "problem_discovery": False,
        "target_audience": False,
        "market_timing": False,
        "solution_pressure": False,
        "competitive_reality": False,
        "business_model": False,
        "founder_market_fit_risk": False
    },

    "artifacts_generated": {
        "lean_canvas": False,
        "risk_register": False,
        "one_pager": False
    },

    "audio_generated": {
        "skeptical_vc": False,
        "target_customer": False,
        "fellow_founder": False
    }
}
    

if st.session_state.canvas["stage"] == "intake":
    render_intake()
elif st.session_state.canvas["stage"] == "interview":
    render_interview()
elif st.session_state.canvas["stage"] == "synthesis":
    st.write("Synthesis Stage")
    st.write(st.session_state.canvas["conversation_history"])
    st.write(st.session_state.canvas)
    st.write(st.session_state.completed_clusters)
elif st.session_state.canvas["stage"] == "review":
    st.write("Review Stage")
elif st.session_state.canvas["stage"] == "complete":
    st.write("Complete Stage")

