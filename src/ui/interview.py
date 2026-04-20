import streamlit as st

def _render_question_header(question, question_number=None):
    # Renders the mentor-style question card header common to all input types
    
    # Subtle question counter badge (no dimension labels — UX spec: feels like a mentor, not a rubric)
    if question_number is not None:
        st.markdown(
            f'<p style="font-size: 0.78rem; font-weight: 600; letter-spacing: 0.12em; '
            f'color: var(--text-color, #888); text-transform: uppercase; margin-bottom: 0.25rem;">'
            f'Question {question_number}</p>', unsafe_allow_html=True )
    
    # The actual question — large, readable, prominent
    st.markdown(
        f'<h3 style=" letter-spacing: 0.6px; '
        f'margin-top: 0;">{question}</h2>',
        unsafe_allow_html=True,
    )


def _render_submit_button(label="Submit Answer"):
    # Renders the shared submit CTA and returns True when clicked
    st.markdown("<div style='margin-top: 1.2rem;'></div>", unsafe_allow_html=True)
    return st.button(label, type="primary", use_container_width=True)


def render_open_text( question, key, placeholder="Share your thoughts here...", question_number=None, helper_text=None):
    # Renders a narrative open-text question panel
    # Used for: evidence-based, nuanced, or narrative answers where a bounded
    # option set would constrain the founder's thinking.
    
    with st.container(gap='xsmall'):
        _render_question_header(question, question_number)

        # Hint text (Mom Test framing cue, shown lightly)
        if helper_text:
            st.caption(helper_text)

    answer = st.text_area( label="Your answer", key=key, placeholder=placeholder, height=160, label_visibility="collapsed")

    submitted = _render_submit_button()

    if submitted:
        if not answer or not answer.strip():
            st.warning("Please share your thoughts before continuing.")
            return None
        return answer.strip()

    return None


# ─────────────────────────────────────────────
# INPUT TYPE 2: multiple_choice
# ─────────────────────────────────────────────

def render_multiple_choice( question, options, key, question_number=None, helper_text=None):
    
    # Renders a pill-style multiple-choice question panel
    # Used for: questions with a bounded, well-known answer space — e.g. revenue model type, willingness to pay, unfair advantage type.
    # Rendered as `st.pills` (single-select) for a modern, tactile feel that avoids the visual weight of a radio group.
    # Example PRD questions: 1.4, 2.2, 3.2, 5.2, 5.3, 6.1, 6.2, 6.3, 7.3
    _render_question_header(question, question_number)

    if helper_text:
        st.caption(helper_text)

    selected = st.pills( label="Choose one", options=options, key=key, selection_mode="single", label_visibility="collapsed")

    submitted = _render_submit_button()

    if submitted:
        if selected is None:
            st.warning("Please select one of the options above.")
            return None
        return selected

    return None

def render_scale(
    question,
    options,
    key,
    question_number=None,
    helper_text=None,
):
    # Renders a segmented-control scale question panel
    # Used for: frequency, intensity, or ordered-spectrum answers where the ordered
    # nature of the scale should feel natural (e.g. Daily → Rarely, Strong → None).
    # Rendered as `st.segmented_control` — a horizontally ordered button group that
    # communicates the ordered spectrum more clearly than pills or a dropdown.
    # Example PRD questions: 1.2 (Daily / Weekly / Monthly / Rarely)
    _render_question_header(question, question_number)

    if helper_text:
        st.caption(helper_text)

    st.markdown("<div style='margin-bottom: 0.4rem;'></div>", unsafe_allow_html=True)

    selected = st.segmented_control( label="Select frequency", options=options, key=key, label_visibility="collapsed")

    submitted = _render_submit_button()

    if submitted:
        if selected is None:
            st.warning("Please select a point on the scale above.")
            return None
        return selected

    return None

def render_yes_no( question, key, question_number=None, helper_text=None, yes_label="Yes", no_label="No"):
    
    # Renders a binary yes/no question panel as two large choice buttons
    _render_question_header(question, question_number)

    if helper_text:
        st.caption(helper_text)

    st.markdown("<div style='margin-top: 0.5rem;'></div>", unsafe_allow_html=True)

    col_yes, col_no = st.columns(2, gap="medium")

    with col_yes:
        yes_clicked = st.button( yes_label, key=f"{key}_yes", type="primary", use_container_width=True)

    with col_no:
        no_clicked = st.button( no_label, key=f"{key}_no", type="secondary", use_container_width=True)

    if yes_clicked: return "yes"
    if no_clicked: return "no"

    return None


# ─────────────────────────────────────────────
# STAGE 2 ENTRY POINT
# ─────────────────────────────────────────────

def render_interview():
    # Entry point for Stage 2 — AI Mentor Interview
    # Reads the current question from `st.session_state` and delegates rendering
    # to the appropriate input-type function
    # Interview engine populates `session_state.current_question` with dict form:
    # {"question": str, "format": "open_text"|"multiple_choice"|"scale"|"yes_no", 
    #  "options": list[str]|None, "dimension": str, "number": int|None}

    st.title("FounderLens 🚀")
    st.markdown( '<h3 style="letter-spacing: 0.8px;">Let\'s pressure-test your idea.</h3>', unsafe_allow_html=True)
    st.markdown( "Answer honestly — vague answers won't move you forward. There are no right answers, only evidence.")
    st.divider()

    # ── Current question payload (populated by interview engine) ───────────
    current_q = st.session_state.get("current_question")

    if current_q is None:
        # Interview engine not yet wired — show a holding state
        st.info("The interview engine is initialising your first question…")
        return

    fmt = current_q.get("format", "open_text")
    question_text = current_q.get("question", "")
    options = current_q.get("options") or []
    q_number = current_q.get("number")

    # ── Dispatch to the correct input-type renderer ────────────────────────
    answer = None

    if fmt == "open_text":
        answer = render_open_text(
            question=question_text,
            key=f"q_{q_number}_{fmt}",
            question_number=q_number,
        )

    elif fmt == "multiple_choice":
        answer = render_multiple_choice(
            question=question_text,
            options=options,
            key=f"q_{q_number}_{fmt}",
            question_number=q_number,
        )

    elif fmt == "scale":
        answer = render_scale(
            question=question_text,
            options=options,
            key=f"q_{q_number}_{fmt}",
            question_number=q_number,
        )

    elif fmt == "yes_no":
        answer = render_yes_no(
            question=question_text,
            key=f"q_{q_number}_{fmt}",
            question_number=q_number,
        )

    # ── Hand the answer back to the interview engine (placeholder) ─────────
    if answer is not None:
        # ENHANCE: Replace this stub with interview_engine.handle_answer(answer)
        # which will: append to conversation_history, evaluate coverage, pick
        # next question or trigger synthesis → st.rerun()
        st.session_state["last_answer"] = answer
        st.rerun()


# ─────────────────────────────────────────────
# DEMO: Sample Render Interview
# ─────────────────────────────────────────────

def sample_render_interview():
    # A demonstration flow of the 4 interview input components
    # Cycles through each input type using sample questions from the PRD
    # to showcase the layout and UX
    
    if "demo_step" not in st.session_state:
        st.session_state.demo_step = 0
        st.session_state.demo_answers = {}

    with st.container(gap='xxsmall'):
        st.title("Interview UI Preview 🛡️")
        st.markdown("Experience the modular input layouts designed for the AI Mentor Stage.")
        st.divider()

    step = st.session_state.demo_step

    if step == 0:
        # Open Text Example (PRD 1.1)
        ans = render_open_text(
            question="How would you describe the core problem your idea solves, in one sentence?",
            key="demo_open",
            question_number=1,
            placeholder="e.g., Local farmers struggle to find consistent buyers for seasonal produce...",
            helper_text="Avoid buzzwords—describe the pain exactly as your customer experiences it."
        )
        if ans:
            st.session_state.demo_answers["problem"] = ans
            st.session_state.demo_step = 1
            st.rerun()

    elif step == 1:
        # Scale Example (PRD 1.2)
        ans = render_scale(
            question="How often does your target customer run into this problem?",
            options=["Daily", "Weekly", "Monthly", "Rarely"],
            key="demo_scale",
            question_number=2,
            helper_text="Establish the frequency and urgency of the pain point."
        )
        if ans:
            st.session_state.demo_answers["frequency"] = ans
            st.session_state.demo_step = 2
            st.rerun()

    elif step == 2:
        # Multiple Choice Example (PRD 2.2)
        ans = render_multiple_choice(
            question="Are these people currently paying for any solution to this problem?",
            options=["Yes, paying", "Yes, using free tools", "No, nothing", "Not sure"],
            key="demo_mc",
            question_number=3,
            helper_text="This establishes if there is already a 'willingness to pay' in the market."
        )
        if ans:
            st.session_state.demo_answers["current_behavior"] = ans
            st.session_state.demo_step = 3
            st.rerun()

    elif step == 3:
        # Yes/No Example (PRD 1.4-ish)
        ans = render_yes_no(
            question="Is your understanding of this problem based on personal experience?",
            yes_label="Yes, seen it directly",
            no_label="No, logical assumption",
            key="demo_yn",
            question_number=4,
            helper_text="We distinguish between first-hand evidence and second-hand hypotheses."
        )
        if ans:
            st.session_state.demo_answers["evidence_type"] = ans
            st.session_state.demo_step = 4
            st.rerun()

    else:
        # Completion State
        st.balloons()
        st.success("Modular Input Demo Complete!")
        st.write("### Mock Data Path Collected:")
        st.json(st.session_state.demo_answers)
        
        if st.button("Reset Demo Flow", use_container_width=True):
            st.session_state.demo_step = 0
            st.session_state.demo_answers = {}
            st.rerun()