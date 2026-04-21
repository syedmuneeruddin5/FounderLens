import json
from llm_client import call_llm
from prompts import (
    INTERVIEW_SYSTEM,
    GENERATE_CLUSTER_PROMPT,
    GENERATE_PROBE_CLUSTER_PROMPT,
    EVALUATE_CLUSTER_PROMPT,
    QUESTION_BANK,
)

DIMENSION_ORDER = [
    "problem_discovery",
    "target_audience",
    "market_timing",
    "solution_pressure",
    "competitive_reality",
    "business_model",
    "founder_market_fit_risk",
]

# Canvas field groups that each dimension primarily targets — used in build_prior_signals
DIMENSION_FIELDS = {
    "problem_discovery":        ["idea", "audience"],
    "target_audience":          ["audience"],
    "market_timing":            ["market"],
    "solution_pressure":        ["solution"],
    "competitive_reality":      ["competition"],
    "business_model":           ["business_model"],
    "founder_market_fit_risk":  ["founder", "risks"],
}


# ─── Internal Helpers ─────────────────────────────────────────────────────────

def _build_canvas_summary(canvas):
    # Compact readable string of non-null canvas fields — skips conversation_history
    lines = []
    field_labels = {
        "idea": {
            "problem": "Problem",
            "one_liner": "One-liner",
            "solution": "Solution",
            "why_now": "Why now",
        },
        "audience": {
            "primary_segment": "Primary segment",
            "early_adopter_profile": "Early adopter",
            "pain_description": "Pain description",
            "current_alternatives": "Current alternatives",
            "willingness_to_pay": "Willingness to pay",
        },
        "market": {
            "tam_estimate": "TAM estimate",
            "size_bucket": "Market size",
            "timing_signal": "Timing signal",
            "market_signal_strength": "Signal strength",
        },
        "solution": {
            "description": "Solution description",
            "key_differentiator": "Key differentiator",
            "ten_x_claim": "10x claim",
            "mvp_scope": "MVP scope",
        },
        "competition": {
            "alternatives": "Alternatives",
            "alternatives_shortfall": "Why alternatives fall short",
            "differentiation": "Differentiation",
            "unfair_advantage": "Unfair advantage",
            "advantage_type": "Advantage type",
        },
        "business_model": {
            "revenue_type": "Revenue type",
            "who_pays": "Who pays",
            "price_bucket": "Price range",
            "cost_structure": "Cost structure",
            "channels": "Channels",
            "key_metrics": "Key metrics",
        },
        "founder": {
            "background_relevance": "Founder background",
            "known_vs_guessed": "Known vs guessed",
            "validation_done": "Validation done",
            "validation_plan": "Validation plan",
        },
    }

    for group, fields in field_labels.items():
        group_data = canvas.get(group, {})
        for key, label in fields.items():
            val = group_data.get(key)
            if val is not None:
                if isinstance(val, list):
                    val = ", ".join(val) if val else None
                if val:
                    lines.append(f"{label}: {val}")

    risks = canvas.get("risks", [])
    for r in risks:
        lines.append(f"Risk: {r.get('assumption')} [{r.get('risk_level')}]")

    return "\n".join(lines) if lines else "No information captured yet."


def _build_conversation_history_summary(canvas):
    history = canvas.get("conversation_history", [])
    if not history:
        return "No conversation yet."
    lines = []
    for entry in history:
        lines.append(f"[{entry['dimension']}] Q: {entry['question']}\nA: {entry['answer']}")
    return "\n\n".join(lines)


def _build_qa_pairs(cluster):
    pairs = []
    for q, a in zip(cluster["questions"], cluster["answers"]):
        pairs.append({
            "question": q["question"],
            "format": q["format"],
            "answer": a,
        })
    return pairs


def _format_qa_pairs(pairs):
    lines = []
    for i, p in enumerate(pairs, 1):
        lines.append(f"Q{i} ({p['format']}): {p['question']}\nA: {p['answer']}")
    return "\n\n".join(lines)


def _build_prior_signals(canvas, dimension):
    # Pull current non-null canvas values for fields relevant to this dimension
    groups = DIMENSION_FIELDS.get(dimension, [])
    lines = []
    for group in groups:
        if group == "risks":
            for r in canvas.get("risks", []):
                lines.append(f"Risk: {r.get('assumption')} [{r.get('risk_level')}]")
        else:
            group_data = canvas.get(group, {})
            for k, v in group_data.items():
                if v is not None:
                    if isinstance(v, list):
                        v = ", ".join(v) if v else None
                    if v:
                        lines.append(f"{k}: {v}")
    return "\n".join(lines) if lines else "Nothing known yet."


def _build_dimension_exchanges(canvas, dimension):
    # Q&A entries from conversation_history for a specific dimension
    history = canvas.get("conversation_history", [])
    entries = [e for e in history if e["dimension"] == dimension]
    if not entries:
        return "No prior exchanges for this dimension."
    lines = []
    for e in entries:
        lines.append(f"Q: {e['question']}\nA: {e['answer']}")
    return "\n\n".join(lines)


def _format_question_bank(dimension):
    bank = QUESTION_BANK.get(dimension, {})
    lines = [
        f"Goal: {bank.get('goal', '')}",
        f"Core fields to cover: {', '.join(bank.get('core_fields', []))}",
        "Reference questions (do not copy verbatim):",
    ]
    for i, q in enumerate(bank.get("seed_questions", []), 1):
        opts = f" [options: {', '.join(q['options'])}]" if "options" in q else ""
        lines.append(f"  {i}. [{q['format']}]{opts} {q['q']}")
    lines.append("Probe triggers (conditions that suggest a follow-up is needed):")
    for t in bank.get("probe_triggers", []):
        lines.append(f"  - {t}")
    return "\n".join(lines)


def _format_dimensions_covered(canvas):
    covered = canvas.get("dimensions_covered", {})
    lines = []
    for dim in DIMENSION_ORDER:
        status = "✓ covered" if covered.get(dim) else "✗ not yet covered"
        lines.append(f"  {dim}: {status}")
    return "\n".join(lines)


def _parse_json_with_retry(raw, messages, json_mode):
    # Try parse; on failure retry once with a clarification appended
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        pass

    retry_messages = messages + [
        {"role": "assistant", "content": raw or ""},
        {"role": "user", "content": "Your previous response was not valid JSON. Return JSON only — no explanation, no markdown fences."},
    ]
    raw2 = call_llm(retry_messages, json_mode=json_mode)
    try:
        return json.loads(raw2)
    except (json.JSONDecodeError, TypeError):
        raise ValueError("LLM returned invalid JSON after two attempts.")


def _validate_cluster(cluster):
    if not isinstance(cluster, dict):
        raise ValueError("Cluster is not a dict.")
    if not cluster.get("questions"):
        raise ValueError("Cluster has no questions.")
    for q in cluster["questions"]:
        if not q.get("question") or not q.get("format"):
            raise ValueError(f"Malformed question in cluster: {q}")


def _finalize_cluster(cluster):
    # Ensure runtime fields are set before returning
    n = len(cluster["questions"])
    cluster["answers"] = [None] * n
    cluster["current_index"] = 0
    return cluster


def _build_messages(canvas, user_content):
    system = INTERVIEW_SYSTEM.format(
        raw_input=canvas.get("idea", {}).get("raw_input", ""),
        canvas_summary=_build_canvas_summary(canvas),
    )
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user_content},
    ]


# ─── Public Functions ─────────────────────────────────────────────────────────

def get_next_dimension(canvas):
    covered = canvas.get("dimensions_covered", {})
    for dim in DIMENSION_ORDER:
        if not covered.get(dim, False):
            return dim
    return None


def is_complete(canvas):
    return all(canvas.get("dimensions_covered", {}).values())


def generate_cluster(canvas):
    dimension = get_next_dimension(canvas)
    if dimension is None:
        raise ValueError("All dimensions are already covered.")

    user_content = GENERATE_CLUSTER_PROMPT.format(
        dimension=dimension,
        is_probe=False,
        dimensions_covered=_format_dimensions_covered(canvas),
        conversation_history_summary=_build_conversation_history_summary(canvas),
        question_bank=_format_question_bank(dimension),
        probe_context="",
    )
    messages = _build_messages(canvas, user_content)
    raw = call_llm(messages, json_mode=True, temperature=0.7)
    cluster = _parse_json_with_retry(raw, messages, json_mode=True)

    # Retry if cluster came back empty
    if not cluster.get("questions"):
        raw = call_llm(messages, json_mode=True, temperature=0.7)
        cluster = _parse_json_with_retry(raw, messages, json_mode=True)

    _validate_cluster(cluster)
    return _finalize_cluster(cluster)


def generate_probe_cluster(canvas, dimension, probe_reason):
    user_content = GENERATE_PROBE_CLUSTER_PROMPT.format(
        dimension=dimension,
        probe_reason=probe_reason,
        dimension_exchanges=_build_dimension_exchanges(canvas, dimension),
    )
    messages = _build_messages(canvas, user_content)
    raw = call_llm(messages, json_mode=True, temperature=0.7)
    cluster = _parse_json_with_retry(raw, messages, json_mode=True)

    if not cluster.get("questions"):
        raw = call_llm(messages, json_mode=True, temperature=0.7)
        cluster = _parse_json_with_retry(raw, messages, json_mode=True)

    _validate_cluster(cluster)
    cluster["is_probe"] = True
    return _finalize_cluster(cluster)


def evaluate_cluster(canvas, cluster):
    qa_pairs = _build_qa_pairs(cluster)
    user_content = EVALUATE_CLUSTER_PROMPT.format(
        dimension=cluster["dimension"],
        qa_pairs=_format_qa_pairs(qa_pairs),
        prior_signals=_build_prior_signals(canvas, cluster["dimension"]),
    )
    messages = _build_messages(canvas, user_content)
    raw = call_llm(messages, json_mode=True, temperature=0.3)
    result = _parse_json_with_retry(raw, messages, json_mode=True)

    if "covered" not in result or "extracted_signals" not in result:
        raise ValueError("Evaluation response is missing required fields.")

    # Side effect: merge signals into canvas draft fields
    apply_extracted_signals(canvas, result.get("extracted_signals", {}))
    return result


def apply_extracted_signals(canvas, signals):
    if not signals:
        return

    # Scalar field groups
    scalar_groups = ["idea", "audience", "market", "solution", "competition", "business_model", "founder"]
    for group in scalar_groups:
        group_signals = signals.get(group)
        if not isinstance(group_signals, dict):
            continue
        canvas_group = canvas.setdefault(group, {})
        for field, value in group_signals.items():
            if value is None:
                continue
            existing = canvas_group.get(field)
            # For list fields: extend without duplicates
            if isinstance(existing, list):
                if isinstance(value, list):
                    for item in value:
                        if item not in existing:
                            existing.append(item)
            else:
                # Only write if field is currently empty
                if existing is None:
                    canvas_group[field] = value

    # risks[] — always append new entries
    risk_signals = signals.get("risks")
    if isinstance(risk_signals, list):
        canvas_risks = canvas.setdefault("risks", [])
        for risk in risk_signals:
            if risk.get("assumption"):
                canvas_risks.append(risk)
