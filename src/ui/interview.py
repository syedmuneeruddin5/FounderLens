import streamlit as st
from interview_engine import (
    generate_cluster,
    generate_probe_cluster,
    evaluate_cluster,
    is_complete,
)

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

def render_scale(question, options, key, question_number=None, helper_text=None):
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


# ─── Dispatcher ───────────────────────────────────────────────────────────────

def _dispatch_question(question_dict, key, question_number):
    fmt = question_dict.get("format")
    q   = question_dict.get("question", "")

    if fmt == "open_text":
        return render_open_text(
            question=q,
            key=key,
            placeholder=question_dict.get("placeholder") or "Share your thoughts here...",
            question_number=question_number,
            helper_text=question_dict.get("helper_text"),
        )
    elif fmt == "multiple_choice":
        return render_multiple_choice(
            question=q,
            options=question_dict.get("options", []),
            key=key,
            question_number=question_number,
            helper_text=question_dict.get("helper_text"),
        )
    elif fmt == "scale":
        return render_scale(
            question=q,
            options=question_dict.get("options", []),
            key=key,
            question_number=question_number,
            helper_text=question_dict.get("helper_text"),
        )
    elif fmt == "yes_no":
        return render_yes_no(
            question=q,
            key=key,
            question_number=question_number,
            helper_text=question_dict.get("helper_text"),
            yes_label=question_dict.get("yes_label") or "Yes",
            no_label=question_dict.get("no_label") or "No",
        )
    else:
        st.error(f"Unknown question format: {fmt}")
        return None


# ─── Main Entry Point ─────────────────────────────────────────────────────────

def render_interview():
    canvas = st.session_state.canvas

    # Initialize interview-local state on first entry
    if "current_cluster" not in st.session_state:
        st.session_state.current_cluster = None
        st.session_state.completed_clusters = []
        st.session_state.interview_ready = False

    # Generate first cluster if none exists yet
    if st.session_state.current_cluster is None:
        with st.spinner("Preparing your first question..."):
            try:
                cluster = generate_cluster(canvas)
            except Exception as e:
                st.error(f"Couldn't generate the first question. Please refresh and try again.\n\n_{e}_")
                return
        st.session_state.current_cluster = cluster
        st.session_state.interview_ready = True
        st.rerun()

    cluster = st.session_state.current_cluster
    idx = cluster["current_index"]

    # Global question counter — computed from completed clusters + progress in current
    total_answered = sum(
        len(c["answers"]) for c in st.session_state.completed_clusters
    ) + idx
    question_number = total_answered + 1

    question_dict = cluster["questions"][idx]

    # Key is globally unique: dimension + position + how many clusters are done
    key = f"q_{cluster['dimension']}_{idx}_{len(st.session_state.completed_clusters)}"

    answer = _dispatch_question(question_dict, key, question_number)

    if answer is None:
        return

    # Store answer and advance index
    cluster["answers"][idx] = answer
    cluster["current_index"] += 1

    # More questions remain in this cluster — show next
    if cluster["current_index"] < len(cluster["questions"]):
        st.rerun()
        return

    # All cluster questions answered — evaluate
    with st.spinner("Thinking about your answers..."):
        try:
            result = evaluate_cluster(canvas, cluster)
        except Exception as e:
            st.error(f"Something went wrong evaluating your answers. Please refresh and try again.\n\n_{e}_")
            return

    # Append all Q&A to conversation_history
    for i, q in enumerate(cluster["questions"]):
        canvas["conversation_history"].append({
            "dimension": cluster["dimension"],
            "question": q["question"],
            "question_format": q["format"],
            "answer": cluster["answers"][i],
            "probe_triggered": cluster.get("is_probe", False),
        })

    # Update dimension coverage
    canvas["dimensions_covered"][result["dimension"]] = result.get("covered", False)

    # Archive this cluster
    st.session_state.completed_clusters.append(cluster)

    # ── Decide next step ──────────────────────────────────────────────────────

    if is_complete(canvas):
        canvas["stage"] = "synthesis"
        st.rerun()
        return

    if result.get("probe_needed"):
        with st.spinner("Following up on something you mentioned..."):
            try:
                probe = generate_probe_cluster(
                    canvas,
                    result["dimension"],
                    result.get("probe_reason", ""),
                )
            except Exception as e:
                st.error(f"Couldn't generate the follow-up question. Please refresh and try again.\n\n_{e}_")
                return
        st.session_state.current_cluster = probe
        st.rerun()
        return

    # Move to next dimension
    with st.spinner("Moving to the next topic..."):
        try:
            next_cluster = generate_cluster(canvas)
        except Exception as e:
            st.error(f"Couldn't generate the next question. Please refresh and try again.\n\n_{e}_")
            return
    st.session_state.current_cluster = next_cluster
    st.rerun()