INTAKE_PREFILL = """
You are a startup mentor. A founder has just described their startup idea:
---
{raw_input}
---
Extract the following two pieces of information from their description:
1. A one-sentence summary of the idea (one_liner).
2. The core problem being solved (problem).

Return the result as a JSON object with exactly these two keys: "one_liner" and "problem".
Be concise and use the founder's own language where possible, but make it professional.
"""

# ─── Stage 2: Interview ───────────────────────────────────────────────────────

INTERVIEW_SYSTEM = """
You are a startup mentor conducting a structured validation interview with an early-stage founder.

Your role:
- Ask sharp, specific questions that reveal the truth about the idea
- Challenge assumptions without being hostile — stay curious, not cynical
- Seek real evidence, not opinions or hypotheticals
- Sound like a knowledgeable human mentor — not a form or a chatbot

Rules you never break:
- Never mention Lean Canvas, Mom Test, YC, or any framework by name
- Never refer to "dimensions", "clusters", "stages", or "coverage"
- Never ask for information the founder has already given
- Never cheerlead or validate — stay neutral and curious
- Personalize every question to this specific idea and founder
- Do not copy reference questions verbatim — always adapt them

The founder's idea:
{raw_input}

What you already know about them:
{canvas_summary}
"""

GENERATE_CLUSTER_PROMPT = """
Your task is to generate the next cluster of interview questions.

Dimension to cover: {dimension}
Is this a probe cluster: {is_probe}

Current coverage status:
{dimensions_covered}

Conversation so far:
{conversation_history_summary}

Reference framework — use this to understand what needs to be learned for this dimension.
Do NOT copy these questions verbatim. Use them as a thinking guide only. Personalize every question to this founder's specific idea:
{question_bank}

Generation rules:
- Generate 2-4 questions for a main cluster, 1 for a probe cluster
- Pick the format that fits what you are asking — do not choose format for variety
- For yes_no: write yes_label and no_label specific to the question (e.g. "Seen it firsthand" not "Yes")
- For scale: use for frequency, intensity, or ordered-spectrum answers where the ordered nature should feel natural (e.g. Daily → Rarely, Strong → None)
- Add helper_text only when the question risks a vague or buzzword answer
- Add placeholder only when a concrete example would clarify the expected format — make it specific to their idea
- Omit helper_text and placeholder when the question is already clear
- If earlier answers already partially cover this dimension, focus only on the gaps
- Questions must feel like a natural continuation of the conversation

{probe_context}

Return JSON only — no explanation, no markdown fences:
{{
  "dimension": "string",
  "is_probe": boolean,
  "questions": [
    {{
      "id": "string",
      "question": "string",
      "format": "open_text" | "multiple_choice" | "scale" | "yes_no",
      "options": ["string"] | null,
      "placeholder": "string" | null,
      "helper_text": "string" | null,
      "yes_label": "string" | null,
      "no_label": "string" | null,
      "targets": "string"
    }}
  ]
}}
"""

GENERATE_PROBE_CLUSTER_PROMPT = """
A dimension was not sufficiently covered. Generate 1-2 focused follow-up questions to address the gap.

Dimension: {dimension}
Why a follow-up is needed: {probe_reason}

Questions and answers already given for this dimension:
{dimension_exchanges}

Rules:
- Generate 1 question only
- Questions must directly address the stated gap — not repeat what was already asked
- Use the format that best fits what you need to learn
- Feel like a natural follow-up, not an interrogation
- Personalize to the founder's specific idea

Return JSON only — no explanation, no markdown fences:
{{
  "dimension": "string",
  "is_probe": true,
  "questions": [
    {{
      "id": "string",
      "question": "string",
      "format": "open_text" | "multiple_choice" | "scale" | "yes_no",
      "options": ["string"] | null,
      "placeholder": "string" | null,
      "helper_text": "string" | null,
      "yes_label": "string" | null,
      "no_label": "string" | null,
      "targets": "string"
    }}
  ]
}}
"""

EVALUATE_CLUSTER_PROMPT = """
Evaluate whether the following interview answers give sufficient understanding of the {dimension} dimension.

Questions and answers:
{qa_pairs}

What was already known about this dimension before this cluster:
{prior_signals}

Evaluation criteria — an answer is sufficient when it is:
- Specific: not generic or vague
- Evidence-based: not purely hypothetical ("I think..." or "People would...")
- Relevant: actually addresses what was asked

Rules:
- Mark covered: true only if the core fields for this dimension have enough signal
- If answers are directionally useful but vague, mark covered: true with confidence: "low"
- If answers are clearly hypothetical, contradictory, or missing key signal, mark probe_needed: true and explain exactly what is missing in probe_reason
- Extract only what was actually said — do not infer, embellish, or fill gaps
- Use null for any field where no clear signal was given
- For risks: return as a list even if only one risk is mentioned

Return JSON only — no explanation, no markdown fences:
{{
  "dimension": "string",
  "covered": boolean,
  "confidence": "high" | "medium" | "low",
  "probe_needed": boolean,
  "probe_reason": "string" | null,
  "extracted_signals": {{
    "idea": {{
      "problem": "string" | null,
      "why_now": "string" | null,
      "one_liner": "string" | null,
      "solution": "string" | null
    }},
    "audience": {{
      "primary_segment": "string" | null,
      "early_adopter_profile": "string" | null,
      "pain_description": "string" | null,
      "current_alternatives": "string" | null,
      "willingness_to_pay": "string" | null
    }},
    "market": {{
      "tam_estimate": "string" | null,
      "size_bucket": "string" | null,
      "timing_signal": "string" | null,
      "market_signal_strength": "string" | null
    }},
    "solution": {{
      "description": "string" | null,
      "key_differentiator": "string" | null,
      "ten_x_claim": "string" | null,
      "mvp_scope": "string" | null
    }},
    "competition": {{
      "alternatives": ["string"] | null,
      "alternatives_shortfall": "string" | null,
      "differentiation": "string" | null,
      "unfair_advantage": "string" | null,
      "advantage_type": "string" | null
    }},
    "business_model": {{
      "revenue_type": "string" | null,
      "who_pays": "string" | null,
      "price_bucket": "string" | null,
      "cost_structure": "string" | null,
      "channels": "string" | null,
      "key_metrics": "string" | null
    }},
    "founder": {{
      "background_relevance": "string" | null,
      "known_vs_guessed": "string" | null,
      "validation_done": "string" | null,
      "validation_plan": "string" | null
    }},
    "risks": [
      {{
        "assumption": "string",
        "risk_level": "high" | "medium" | "low",
        "validation_method": "string" | null,
        "is_riskiest": boolean
      }}
    ]
  }}
}}
"""

# Reference framework embedded in GENERATE_CLUSTER_PROMPT at call time
QUESTION_BANK = {
    "problem_discovery": {
        "goal": "Establish that the problem is real, painful, frequent, and observable — not assumed.",
        "core_fields": ["idea.problem", "audience.pain_description"],
        "seed_questions": [
            {"q": "How would you describe the core problem your idea solves, in one sentence?", "format": "open_text"},
            {"q": "How often does your target customer run into this problem?", "format": "scale", "options": ["Daily", "Weekly", "Monthly", "Rarely"]},
            {"q": "What's the real cost of this problem not being solved — what actually happens to them?", "format": "open_text"},
        ],
        "probe_triggers": [
            "Answer is hypothetical — no direct evidence mentioned",
            "Problem described from founder's view, not customer's",
            "Frequency claim not grounded in observation",
        ],
        "probe_questions": [
            {"q": "Is that something you've seen directly, or is it an assumption?", "format": "yes_no"},
            {"q": "Can you describe a specific moment when this problem caused someone a real frustration?", "format": "open_text"},
        ],
    },
    "target_audience": {
        "goal": "Narrow from a broad group to a specific, nameable early adopter.",
        "core_fields": ["audience.primary_segment", "audience.early_adopter_profile", "audience.willingness_to_pay"],
        "seed_questions": [
            {"q": "If you could only sell to 10 people first, who would they be? What do they have in common?", "format": "open_text"},
            {"q": "Are these people currently paying for any solution to this problem?", "format": "multiple_choice", "options": ["Yes, paying for something", "Yes, using free tools", "No, they do nothing", "Not sure"]},
        ],
        "probe_triggers": [
            "Segment is too broad (e.g. 'everyone', 'small businesses')",
            "No differentiation between early adopter and general audience",
        ],
        "probe_questions": [
            {"q": "Within that group, who feels this pain most acutely — what makes them different from the rest?", "format": "open_text"},
        ],
    },
    "market_timing": {
        "goal": "Establish market size signal and a credible why-now rationale.",
        "core_fields": ["market.timing_signal", "market.size_bucket", "market.tam_estimate"],
        "seed_questions": [
            {"q": "What's changed recently — in technology, behavior, or regulation — that makes this solvable now?", "format": "open_text"},
            {"q": "How many people do you think have this problem, roughly?", "format": "multiple_choice", "options": ["Thousands", "Hundreds of thousands", "Millions", "Not sure"]},
        ],
        "probe_triggers": [
            "Why-now is generic (e.g. 'AI is growing')",
            "Market size is asserted without any reasoning",
        ],
        "probe_questions": [
            {"q": "Is there a specific trend or event you're riding, or has this problem always existed?", "format": "open_text"},
        ],
    },
    "solution_pressure": {
        "goal": "Establish that the solution is meaningfully better, not incrementally different.",
        "core_fields": ["solution.description", "solution.key_differentiator", "solution.ten_x_claim"],
        "seed_questions": [
            {"q": "Describe your solution in two or three sentences — what does it actually do?", "format": "open_text"},
            {"q": "Compared to what people do today, why is your solution meaningfully better — not slightly better?", "format": "open_text"},
            {"q": "What's the one thing your solution does that nothing else does?", "format": "open_text"},
        ],
        "probe_triggers": [
            "Differentiation is feature-level, not outcome-level",
            "No clear articulation of why it's 10x better",
        ],
        "probe_questions": [
            {"q": "If someone built this exact product tomorrow, what would make yours still win?", "format": "open_text"},
            {"q": "What's the smallest version of this that would still deliver that core value?", "format": "open_text"},
        ],
    },
    "competitive_reality": {
        "goal": "Establish honest awareness of alternatives and a defensible differentiation.",
        "core_fields": ["competition.alternatives", "competition.unfair_advantage", "competition.differentiation"],
        "seed_questions": [
            {"q": "List the top two or three things people use today to solve this problem — even if imperfect.", "format": "open_text"},
            {"q": "Why haven't those alternatives fully solved it?", "format": "multiple_choice", "options": ["Too expensive", "Too complex", "Not designed for this", "People aren't aware", "Other"]},
            {"q": "What's your unfair advantage — something genuinely hard to copy?", "format": "multiple_choice", "options": ["Domain expertise", "Proprietary data", "Network effects", "First-mover", "Team background", "Not sure yet"]},
        ],
        "probe_triggers": [
            "Claims no competitors exist",
            "Unfair advantage is vague or common",
        ],
        "probe_questions": [
            {"q": "If a well-funded startup built your exact product, what would make you still win?", "format": "open_text"},
        ],
    },
    "business_model": {
        "goal": "Establish a credible revenue hypothesis and basic unit economics thinking.",
        "core_fields": ["business_model.revenue_type", "business_model.who_pays", "business_model.price_bucket"],
        "seed_questions": [
            {"q": "How do you expect to make money — what's the most natural revenue model?", "format": "multiple_choice", "options": ["Subscription", "One-time purchase", "Commission", "Freemium", "Usage-based", "Not sure"]},
            {"q": "Who is actually paying — the end user, a business, or someone else?", "format": "multiple_choice", "options": ["The user pays directly", "A business pays", "Advertisers pay", "Not sure"]},
            {"q": "What would a realistic first customer pay per month?", "format": "multiple_choice", "options": ["Under $10", "$10-$50", "$50-$200", "$200+", "Not a paid product"]},
        ],
        "probe_triggers": [
            "Revenue model doesn't match the audience described",
            "Price hypothesis has no reasoning",
        ],
        "probe_questions": [
            {"q": "What's your biggest cost to run this — what drives your expenses?", "format": "open_text"},
            {"q": "How would you reach your first 100 customers?", "format": "open_text"},
        ],
    },
    "founder_market_fit_risk": {
        "goal": "Surface credibility signals and the riskiest unvalidated assumption.",
        "core_fields": ["founder.background_relevance", "risks[].assumption", "founder.validation_done"],
        "seed_questions": [
            {"q": "Why are you the right person to build this? What do you know or have access to that others don't?", "format": "open_text"},
            {"q": "What's the single assumption your whole idea rests on — the one thing that, if wrong, kills this?", "format": "open_text"},
            {"q": "Have you validated anything yet?", "format": "multiple_choice", "options": ["Talked to potential users", "Built a prototype", "Both", "Not yet"]},
        ],
        "probe_triggers": [
            "Founder background is generic — no specific edge articulated",
            "Riskiest assumption is vague or optimistic",
            "No validation plan mentioned",
        ],
        "probe_questions": [
            {"q": "What's your plan to test that riskiest assumption before building further?", "format": "open_text"},
            {"q": "What do you know from real evidence versus what are you currently assuming?", "format": "open_text"},
        ],
    },
}
