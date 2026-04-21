# FounderLens — Product Requirements Document

---

## Table of Contents

1. [Product Overview](#1-product-overview)
2. [Target User](#2-target-user)
3. [Framework Foundation](#3-framework-foundation)
4. [FounderCanvas — The Central Data Model](#4-foundercanvas--the-central-data-model)
5. [Application Architecture](#5-application-architecture)
6. [Stage-by-Stage Specification](#6-stage-by-stage-specification)
   - [Stage 1 — Idea Intake](#stage-1--idea-intake)
   - [Stage 2 — AI Mentor Interview](#stage-2--ai-mentor-interview)
   - [Stage 3 — Synthesis Review](#stage-3--synthesis-review)
   - [Stage 4 — Artifact Generation](#stage-4--artifact-generation)
   - [Stage 5 — Audio Perspectives (Stretch)](#stage-5--audio-perspectives-stretch)
7. [Information Flow](#7-information-flow)
8. [Codebase Structure](#8-codebase-structure)
9. [LLM Interface Specification](#9-llm-interface-specification)
10. [Prompt Engineering Specification](#10-prompt-engineering-specification)
11. [Development Phases](#11-development-phases)
12. [Open Decisions & Constraints](#12-open-decisions--constraints)

---

## 1. Product Overview

**FounderLens** is an AI-powered startup idea validation tool for early-stage founders. It guides a founder through a structured mentor-style interview, extracts a validated business model, and generates three professional artifacts — all grounded in frameworks used by real accelerators and investors.

### What It Is Not
- Not a chatbot or open-ended AI assistant
- Not a static form or survey
- Not an AI that cheerleads ideas — it challenges assumptions

### What It Is
A directed, adaptive interview engine that feels like a session with a knowledgeable mentor. Every question serves a purpose. Every answer feeds a downstream artifact. Nothing is generated that wasn't discussed.

### Tagline
*"The honest look your idea needs before anyone else sees it."*

### Core Value Proposition
A first-time founder can input a rough idea and walk away with a filled Lean Canvas, a structured risk register, and an investor-ready one-pager — all generated from a 15–20 minute guided session, grounded in YC, Mom Test, and Lean Canvas frameworks.

---

## 2. Target User

**Primary:** Early-stage founders — students, hackathon participants, first-time entrepreneurs with an idea but no structured validation process.

**Secondary:** Somewhat serious founders who want to stress-test an idea before pitching or building.

**User State at Entry:** Has an idea in their head. Has not necessarily spoken to customers, written a business plan, or applied to any accelerator. May not know what a Lean Canvas is.

**User State at Exit:** Has a structured understanding of their idea's strengths and weaknesses, three professional documents they can share, and a clear view of their riskiest assumptions.

---

## 3. Framework Foundation

FounderLens is built on three layered frameworks. Each layer serves a distinct purpose. They do not conflict — they stack.

---

### Layer 1 — Mom Test (Rob Fitzpatrick)
**Purpose:** Governs how questions are asked throughout Stage 2.

The Mom Test principle: most founders ask questions that invite validation rather than truth. Good questions are about the customer's life and existing behavior, not hypotheticals about your solution.

**Rules applied in FounderLens:**
- Questions are specific, not hypothetical ("How do you solve this today?" not "Would you use this?")
- Questions seek disconfirming evidence — designed to find weaknesses, not confirm assumptions
- Questions are about evidence, not opinion ("Have you seen this?" not "Do you think this is a problem?")
- Follow-up probes trigger when answers are vague, hypothetical, or optimistic

---

### Layer 2 — YC Application Framework
**Purpose:** Defines the dimensions (topics) the interview must cover.

Y Combinator's application questions are the most battle-tested founder interrogation in the world. They force articulation of things that actually matter. FounderLens maps its 7 interview dimensions directly to YC's core questions:

| YC Question | FounderLens Dimension |
|---|---|
| What are you building? | Problem Discovery |
| Who is your customer? | Target Audience |
| Why now? | Market & Timing |
| Why is this better? | Solution Pressure |
| Who are the competitors? | Competitive Reality |
| What's the business model? | Business Model |
| Why you? What could kill this? | Founder-Market Fit & Risk |

---

### Layer 3 — Lean Canvas (Ash Maurya)
**Purpose:** Defines where answers go — the artifact structure.

The Lean Canvas is the single most recognized one-page business model framework for early-stage startups. Its 9 blocks map directly to the FounderCanvas data model, ensuring every artifact field was earned through the interview.

| Lean Canvas Block | FounderCanvas Field |
|---|---|
| Problem | `idea.problem` |
| Customer Segments | `audience.primary_segment` |
| Unique Value Proposition | `solution.key_differentiator` |
| Solution | `solution.description` |
| Channels | `business_model.channels` |
| Revenue Streams | `business_model.revenue_type` |
| Cost Structure | `business_model.cost_structure` |
| Key Metrics | `business_model.key_metrics` |
| Unfair Advantage | `competition.unfair_advantage` |
| Existing Alternatives | `competition.alternatives` |

---

## 4. FounderCanvas — The Central Data Model

The FounderCanvas is the single Python dictionary stored in `st.session_state.canvas`. It carries all information through the entire application. It is created at Stage 1, progressively populated through Stage 2, corrected in Stage 3, and consumed in Stage 4 and Stage 5.

Every module reads from and writes to this object. There is no other source of truth.

### Why session_state

All FounderCanvas data lives in `st.session_state` for the duration of a session. This means:
- No file I/O during normal operation
- State is automatically scoped to the user's browser session
- On page rerun (which Streamlit does after every interaction), `session_state` persists
- If the user closes the browser tab, the session is lost — this is acceptable for the current scope

### conversation_history — What It Is and How It's Built

`conversation_history` is an array field that lives inside the FounderCanvas. It is built incrementally during Stage 2 — every time the founder answers a question in a cluster, one entry is appended. By the end of Stage 2 it contains the complete record of the interview.

Its primary purpose is to serve as the authoritative input to the synthesis call, which extracts all FounderCanvas fields from it. Draft field values written during Stage 2 are treated as warm cache — the synthesis call always overwrites them with authoritative values.

### Draft Population During Stage 2

As each cluster is evaluated, `extracted_signals` returned by the evaluation call are merged into the relevant canvas field groups immediately. These are draft values — useful for context in later cluster generation prompts, but not final. The synthesis call is authoritative and overwrites all draft values.

### Full Schema

```python
canvas = {
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
        # One entry appended per founder answer per question in a cluster.
        # Primary and authoritative input to the synthesis extraction call.
        # {
        #   "dimension": str,        — which of the 7 dimensions this exchange targets
        #   "question": str,         — exact question shown to the founder
        #   "question_format": str,  — open_text | multiple_choice | scale | yes_no
        #   "answer": str,           — founder's exact answer
        #   "probe_triggered": bool  — whether this question was part of a probe cluster
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
```

### Field Population Timeline

| Field Group | Populated In | Used In |
|---|---|---|
| `idea.raw_input` | Stage 1 | Stage 2 prompt context |
| `idea.one_liner`, `idea.problem` | Stage 1 (quick AI pre-fill) | Stage 2 starting context |
| `conversation_history` | Stage 2 — one entry per answer per cluster question | Synthesis call |
| `dimensions_covered` | Stage 2 — updated after each cluster evaluation | Stage 2 exit condition |
| All field groups (draft) | Stage 2 — from `extracted_signals` per cluster evaluation | Later cluster generation prompts |
| All field groups (authoritative) | Synthesis call (post-Stage-2) | Stage 3 cards, Stage 4 artifacts |
| `artifacts_generated` | Stage 4 — flipped to True on generation | UI download status |
| `audio_generated` | Stage 5 — flipped to True on generation | UI audio player status |

---

## 5. Application Architecture

### Overview

```
┌──────────────────────────────────────────────────────┐
│                     app.py                            │
│   Reads canvas["stage"] from st.session_state        │
│   Calls the matching render function                  │
└──────────────┬───────────────────────────────────────┘
               │
       st.session_state.canvas
       (single FounderCanvas dict,
        lives for the browser session)
               │
    ┌──────────┼──────────────────┐
    │          │                  │
┌───▼────┐  ┌──▼───────┐   ┌─────▼──────┐
│  LLM   │  │ Artifact │   │   Audio    │
│ Engine │  │Generator │   │  Engine    │
│        │  │          │   │ (stretch)  │
│Cluster │  │ .docx x3 │   │ 3 persona  │
│generate│  │          │   │   clips    │
│evaluate│  └──────────┘   └────────────┘
│Synthesis   
│ call   │
└────────┘
```

### Module Responsibilities

| File | Responsibility |
|---|---|
| `app.py` | Entry point. Initializes `session_state.canvas` if absent. Reads `stage`, calls matching render function. |
| `llm_client.py` | All LLM API calls. Model-agnostic. Accepts prompt + optional JSON schema. Returns text or parsed dict. |
| `interview_engine.py` | Stage 2 logic. Generates clusters, evaluates cluster answers, applies extracted signals, updates `dimensions_covered`, detects exit condition. |
| `synthesis_engine.py` | Single LLM call after Stage 2. Extracts authoritative FounderCanvas fields from full `conversation_history`. |
| `artifact_generator.py` | Generates all three `.docx` files from FounderCanvas using `python-docx`. |
| `audio_engine.py` | Stretch. Generates persona scripts and synthesizes audio via TTS provider. |
| `ui/intake.py` | `render_intake()` — Stage 1 UI |
| `ui/interview.py` | `render_interview()` — Stage 2 UI. Cluster-driven, one question at a time. |
| `ui/review.py` | `render_review()` — Stage 3 UI. 7 cards + edit flow. |
| `ui/artifacts.py` | `render_artifacts()` — Stage 4 UI. Download buttons. |
| `ui/audio.py` | `render_audio()` — Stage 5 UI (stretch). Audio players. |
| `prompts.py` | All prompt templates as Python string constants. Never defined inline in logic files. |

---

## 6. Stage-by-Stage Specification

---

### Stage 1 — Idea Intake

**Purpose:** Capture the founder's idea in their own words. Initialize the FounderCanvas in session_state.

**UI:**
- Clean landing page with app name and tagline
- Single large text area: *"Describe your startup idea. Don't worry about being perfect — just tell us what you're trying to build and who it's for."*
- Submit button: "Start My Validation Session"

**On Submit:**
1. Initialize the full FounderCanvas dict in `st.session_state.canvas` with all fields at their defaults
2. Set `canvas["idea"]["raw_input"]` to the submitted text
3. Call LLM to pre-fill `idea.one_liner` and `idea.problem` from the raw input (temperature 0.2, quick extraction)
4. Set `canvas["stage"] = "interview"`
5. Streamlit reruns — Stage 2 renders

**Exit Condition:** Founder submits non-empty text.

---

### Stage 2 — AI Mentor Interview

**Purpose:** Conduct a directed, adaptive interview across all 7 dimensions using a cluster-based approach. Build `conversation_history`. Draft-populate canvas fields from cluster evaluations. Mark `dimensions_covered` as coverage is achieved. Exit when all 7 are `True`.

**UX Feel:** Guided interview. One question at a time. Not a chat UI — each question is a distinct panel. The founder sees no dimension labels or progress percentage — it simply feels like a mentor working through topics naturally.

---

#### The Cluster Model

Questions are grouped into **clusters** — thematic batches of 2–4 questions that together cover one dimension. The AI generates a full cluster upfront in one LLM call. The founder answers questions one at a time. When the last answer in a cluster is submitted, the entire cluster is evaluated together in one LLM call.

This approach reduces total API calls significantly compared to per-question evaluation, and allows the AI to compose questions that are thematically coherent within a dimension rather than generating them in isolation.

**Cluster types:**
- **Main cluster:** 2–4 questions covering one dimension. Generated at the start of each new dimension.
- **Probe cluster:** 1–2 follow-up questions for a dimension that wasn't sufficiently covered. Generated only when the evaluation call returns `probe_needed: True`.

**Cluster size rules (enforced in generation prompt):**
- Format is decided by what the question is asking — not for variety
- If a dimension is already partially covered by prior answers, generate fewer questions focused on the gaps only
- Questions must feel like a natural continuation of the conversation, personalized to this founder's specific idea

---

#### Session State for Stage 2

Beyond the canvas, Stage 2 maintains UI-layer state in `session_state` (not in the canvas):

```python
st.session_state.current_cluster = {
    "dimension": str,           # dimension this cluster covers
    "questions": [ ... ],       # full list of question dicts from generation call
    "answers": [ ... ],         # parallel list, filled as founder answers
    "current_index": int,       # which question is currently shown (0-based)
    "is_probe": bool            # True if this is a probe cluster
}
# None on first load — triggers first cluster generation

st.session_state.completed_clusters = []
# List of all completed cluster dicts — used for question number tracking
```

---

#### The Cluster Object

```python
cluster = {
    "dimension": "problem_discovery",
    "is_probe": False,
    "questions": [
        {
            "id": "q1",
            "question": str,           # personalized question text
            "format": str,             # open_text | multiple_choice | scale | yes_no
            "options": list | None,    # for multiple_choice and scale only
            "placeholder": str | None, # example answer to clarify expected input
            "helper_text": str | None, # sub-text shown below question
            "yes_label": str | None,   # for yes_no only — replaces "Yes"
            "no_label": str | None,    # for yes_no only — replaces "No"
            "targets": str             # canvas field this answer maps to
        }
        # ... 1-3 more questions
    ],
    "answers": [None, None, None],     # same length as questions
    "current_index": 0
}
```

**Helper text and placeholder rules (enforced in generation prompt):**
- Add `helper_text` when the question risks a vague or buzzword-heavy answer
- Add `placeholder` when a concrete example would clarify the expected answer format — make it feel real and specific to their idea
- For `yes_no`, write `yes_label` and `no_label` that are specific to the question context (e.g. "Seen it firsthand" / "Based on assumption") — not generic "Yes" / "No"
- Omit `helper_text` and `placeholder` when the question is clear without them — do not overuse

---

#### Cluster Lifecycle

```
GENERATING
  One LLM call produces the full cluster dict.
  UI shows loading state.
  Cluster stored in session_state.current_cluster → st.rerun()
        ↓
PRESENTING
  UI reads current_index from cluster.
  Renders the question at that index using correct render_* function.
  Founder submits answer → stored in cluster["answers"][current_index].
  current_index incremented.
  If more questions remain → st.rerun() (stay in PRESENTING).
  If all answered → move to EVALUATING.
        ↓
EVALUATING
  One LLM call evaluates all answers in the completed cluster.
  Returns: covered, confidence, probe_needed, probe_reason, extracted_signals.
  extracted_signals merged into canvas draft fields.
  dimensions_covered[dimension] updated.
  All cluster Q&A pairs appended to conversation_history.
  UI shows loading state during this call.
        ↓
DONE — three possible paths:

  1. All 7 dimensions covered:
     canvas["stage"] = "synthesis" → st.rerun() → exits Stage 2

  2. Probe needed:
     generate_probe_cluster() called (1-2 questions).
     Result set as session_state.current_cluster.
     Current cluster appended to completed_clusters.
     → st.rerun() → back to PRESENTING

  3. Next dimension:
     generate_cluster() called for next uncovered dimension.
     Current cluster appended to completed_clusters.
     → st.rerun() → back to GENERATING
```

---

#### The 7 Dimensions — Question Bank

The question bank is the reference framework for cluster generation. The AI uses it to understand what needs to be covered per dimension and what question styles work well — but does **not** copy questions verbatim. Every question is personalized to the founder's specific idea.

---

**Dimension 1 — Problem Discovery**
Goal: Establish that the problem is real, painful, frequent, and observable — not assumed.

| # | Reference Question | Format | Field Targeted |
|---|---|---|---|
| 1.1 | "How would you describe the core problem your idea solves, in one sentence?" | open_text | `idea.problem` |
| 1.2 | "How often does your target customer run into this problem?" | scale: Daily / Weekly / Monthly / Rarely | `audience.pain_description` |
| 1.3 | "What's the real cost of this problem not being solved — what actually happens to them?" | open_text | `audience.pain_description` |
| 1.4 (probe) | "Is that something you've seen directly, or is it an assumption?" | yes_no | `founder.known_vs_guessed` |
| 1.5 (probe) | "Can you describe a specific moment when this problem caused someone a real frustration?" | open_text | `audience.pain_description` |

Covered when: `idea.problem` and `audience.pain_description` are populated with specific, non-hypothetical content.

---

**Dimension 2 — Target Audience**
Goal: Narrow from a broad group to a specific, nameable early adopter.

| # | Reference Question | Format | Field Targeted |
|---|---|---|---|
| 2.1 | "If you could only sell to 10 people first, who would they be? What do they have in common?" | open_text | `audience.early_adopter_profile` |
| 2.2 | "Are these people currently paying for any solution to this problem?" | multiple_choice: Yes, paying / Yes, using free tools / No, nothing / Not sure | `audience.willingness_to_pay` |
| 2.3 (probe) | "Within that group, who feels this pain most acutely?" | open_text | `audience.primary_segment` |
| 2.4 (probe) | "How does your target customer currently describe this problem to themselves, in their own words?" | open_text | `audience.pain_description` |

Covered when: `audience.primary_segment` and `audience.early_adopter_profile` are specific and distinct from a generic demographic.

---

**Dimension 3 — Market & Timing**
Goal: Establish market size signal and a credible "why now" rationale.

| # | Reference Question | Format | Field Targeted |
|---|---|---|---|
| 3.1 | "What's changed recently — in technology, behavior, or regulation — that makes this problem solvable now?" | open_text | `market.timing_signal` |
| 3.2 | "How many people do you think have this problem, roughly?" | multiple_choice: Thousands / Hundreds of thousands / Millions / Not sure | `market.size_bucket` |
| 3.3 (probe) | "Is there a specific trend or recent event you're riding, or has this problem always existed?" | open_text | `market.timing_signal` |
| 3.4 (probe) | "What would need to be true about the market for this to be a significant company in 5 years?" | open_text | `market.tam_estimate` |

Covered when: `market.timing_signal` is specific (not generic like "AI is growing") and `market.size_bucket` is set.

---

**Dimension 4 — Solution Pressure**
Goal: Establish that the solution is meaningfully better, not incrementally different.

| # | Reference Question | Format | Field Targeted |
|---|---|---|---|
| 4.1 | "Describe your solution in two or three sentences — what does it actually do?" | open_text | `solution.description` |
| 4.2 | "Compared to what people do today, why is your solution meaningfully better — not slightly better?" | open_text | `solution.ten_x_claim` |
| 4.3 | "What's the one thing your solution does that nothing else does?" | open_text | `solution.key_differentiator` |
| 4.4 (probe) | "If someone built this exact product tomorrow, what would make yours still win?" | open_text | `competition.unfair_advantage` |
| 4.5 (probe) | "What's the smallest version of this that would still deliver that core value?" | open_text | `solution.mvp_scope` |

Covered when: `solution.description`, `solution.key_differentiator`, and `solution.ten_x_claim` are populated with specific claims.

---

**Dimension 5 — Competitive Reality**
Goal: Establish honest awareness of alternatives and a defensible differentiation.

| # | Reference Question | Format | Field Targeted |
|---|---|---|---|
| 5.1 | "List the top two or three things people use today to solve this problem — even if they're imperfect." | open_text | `competition.alternatives` |
| 5.2 | "Why haven't those alternatives fully solved it?" | multiple_choice: Too expensive / Too complex / Not designed for this / People aren't aware / Other | `competition.alternatives_shortfall` |
| 5.3 | "What's your unfair advantage — something genuinely hard to copy?" | multiple_choice: Domain expertise / Proprietary data / Network effects / First-mover / Team background / Not sure yet | `competition.advantage_type` |
| 5.4 (probe) | "If a well-funded startup built your exact product, what would make you still win?" | open_text | `competition.unfair_advantage` |

Covered when: `competition.alternatives` has at least two entries and `competition.differentiation` is populated.

---

**Dimension 6 — Business Model**
Goal: Establish a credible revenue hypothesis and basic unit economics thinking.

| # | Reference Question | Format | Field Targeted |
|---|---|---|---|
| 6.1 | "How do you expect to make money — what's the most natural revenue model?" | multiple_choice: Subscription / One-time purchase / Commission / Freemium / Usage-based / Not sure | `business_model.revenue_type` |
| 6.2 | "Who is actually paying — the end user, a business, or someone else?" | multiple_choice: The user pays / A business pays / Advertisers pay / Not sure | `business_model.who_pays` |
| 6.3 | "What would a realistic first customer pay per month?" | multiple_choice: Under $10 / $10–$50 / $50–$200 / $200+ / Not a paid product | `business_model.price_bucket` |
| 6.4 (probe) | "What's your biggest cost to run this — what drives your expenses?" | open_text | `business_model.cost_structure` |
| 6.5 (probe) | "How would you reach your first 100 customers?" | open_text | `business_model.channels` |

Covered when: `business_model.revenue_type`, `business_model.who_pays`, and `business_model.price_bucket` are all set.

---

**Dimension 7 — Founder-Market Fit & Risk**
Goal: Surface credibility signals and the riskiest unvalidated assumption.

| # | Reference Question | Format | Field Targeted |
|---|---|---|---|
| 7.1 | "Why are you the right person to build this? What do you know or have access to that others don't?" | open_text | `founder.background_relevance` |
| 7.2 | "What's the single assumption your whole idea rests on — the one thing that, if wrong, kills this?" | open_text | `risks[]` (is_riskiest: True) |
| 7.3 | "Have you validated anything yet?" | multiple_choice: Talked to potential users / Built a prototype / Both / Not yet | `founder.validation_done` |
| 7.4 (probe) | "What's your plan to test that riskiest assumption before building further?" | open_text | `founder.validation_plan` |
| 7.5 (probe) | "What do you know from real evidence versus what are you currently assuming?" | open_text | `founder.known_vs_guessed` |

Covered when: `founder.background_relevance`, at least one `risks[]` entry, and `founder.validation_done` are populated.

---

#### Stage 2 Exit Condition
All 7 values in `dimensions_covered` are `True`. Checked after every cluster evaluation. Total questions across all clusters: minimum ~12, maximum ~20. Coverage quality — not question count — is the trigger.

#### Stage 2 Adaptive Rules (enforced in system prompt)
- Personalize every question to this founder's specific idea — do not copy reference questions verbatim
- If a dimension is already partially covered by prior cluster answers, generate fewer questions focused only on gaps
- If answers are vague or hypothetical, mark `probe_needed: True` in evaluation — do not mark a dimension covered on weak signal
- Never refer to "dimensions", "clusters", "frameworks", or "Lean Canvas" by name
- Questions must feel like a natural continuation of the conversation

---

#### LLM Calls in Stage 2

| Call | When | Temperature | Input | Output |
|---|---|---|---|---|
| Generate cluster | Start of each new dimension | 0.7 | canvas summary, dimensions_covered, conversation history, question bank | Full cluster dict with questions |
| Generate probe cluster | When evaluation returns `probe_needed: True` | 0.7 | dimension, probe_reason, prior exchanges for that dimension | Small cluster dict (1-2 questions) |
| Evaluate cluster | After all answers in a cluster are submitted | 0.3 | All Q&A pairs from cluster, prior signals for that dimension | covered, confidence, probe_needed, probe_reason, extracted_signals |

**Total API calls — worst case (all dimensions probe once):** 3 calls × 7 dimensions + 1 synthesis = 22 calls
**Total API calls — best case (no probes):** 2 calls × 7 dimensions + 1 synthesis = 15 calls

Both are well within a 30 requests/minute rate limit even if the interview runs quickly.

---

#### Cluster Evaluation Output Schema

```json
{
  "dimension": "problem_discovery",
  "covered": true,
  "confidence": "high",
  "probe_needed": false,
  "probe_reason": null,
  "extracted_signals": {
    "idea": {
      "problem": "str | null",
      "why_now": "str | null"
    },
    "audience": {
      "primary_segment": "str | null",
      "early_adopter_profile": "str | null",
      "pain_description": "str | null",
      "current_alternatives": "str | null",
      "willingness_to_pay": "str | null"
    },
    "market": {
      "tam_estimate": "str | null",
      "size_bucket": "str | null",
      "timing_signal": "str | null",
      "market_signal_strength": "str | null"
    },
    "solution": {
      "description": "str | null",
      "key_differentiator": "str | null",
      "ten_x_claim": "str | null",
      "mvp_scope": "str | null"
    },
    "competition": {
      "alternatives": "list | null",
      "alternatives_shortfall": "str | null",
      "differentiation": "str | null",
      "unfair_advantage": "str | null",
      "advantage_type": "str | null"
    },
    "business_model": {
      "revenue_type": "str | null",
      "who_pays": "str | null",
      "price_bucket": "str | null",
      "cost_structure": "str | null",
      "channels": "str | null",
      "key_metrics": "str | null"
    },
    "founder": {
      "background_relevance": "str | null",
      "known_vs_guessed": "str | null",
      "validation_done": "str | null",
      "validation_plan": "str | null"
    },
    "risks": [
      {
        "assumption": "str",
        "risk_level": "high | medium | low",
        "validation_method": "str | null",
        "is_riskiest": "bool"
      }
    ]
  }
}
```

`extracted_signals` uses only non-null values to update canvas draft fields. The nested structure mirrors the canvas field groups exactly, making the merge a direct recursive update.

---

### Stage 3 — Synthesis Review

**Purpose:** Extract the authoritative FounderCanvas from the full conversation in one structured LLM call. Render it as 7 editable cards. Let the founder correct any misunderstandings before artifact generation.

**Synthesis Call (runs immediately when stage becomes "synthesis" — no UI shown during this):**
- Input: full `conversation_history` array + FounderCanvas schema
- Prompt: "Extract all fields from this conversation into this exact schema. Use null where absent — do not invent."
- Output: fully populated FounderCanvas field groups — overwrites all draft values from Stage 2
- Canvas updated in session_state, `stage = "review"`, Streamlit reruns into Stage 3 UI

**Stage 3 UI — 7 Cards:**

| Card | Fields Displayed |
|---|---|
| The Problem | `idea.problem`, `audience.pain_description`, `idea.why_now` |
| Target Audience | `audience.primary_segment`, `audience.early_adopter_profile`, `audience.willingness_to_pay` |
| Market & Timing | `market.size_bucket`, `market.timing_signal`, `market.tam_estimate` |
| Your Solution | `solution.description`, `solution.key_differentiator`, `solution.ten_x_claim` |
| Competition | `competition.alternatives`, `competition.differentiation`, `competition.unfair_advantage` |
| Business Model | `business_model.revenue_type`, `business_model.who_pays`, `business_model.price_bucket`, `business_model.channels` |
| Risks & Assumptions | `risks[]` — each shown with assumption, risk_level, validation_method |

**Edit Mechanism:**
- Each card has an Edit button
- Founder types correction in a text input below the card
- LLM call interprets the correction, returns updated field values for that card only
- Canvas updated in session_state for the relevant fields
- Card re-renders immediately — no confirmation step

**Exit Condition:** Founder clicks "Looks good — generate my artifacts."

---

### Stage 4 — Artifact Generation

**Purpose:** Generate all three `.docx` files from the finalized FounderCanvas. No LLM calls for Lean Canvas or Risk Register — pure field mapping. One LLM call per section for the One-Pager to produce polished prose.

---

#### Artifact 1 — Lean Canvas (.docx)
**Framework:** Ash Maurya's Lean Canvas
**Format:** Structured 9-block table inside a `.docx`

| Canvas Block | Source Field |
|---|---|
| Problem | `idea.problem` |
| Customer Segments | `audience.primary_segment` + `audience.early_adopter_profile` |
| Unique Value Proposition | `solution.key_differentiator` |
| Solution | `solution.description` |
| Channels | `business_model.channels` |
| Revenue Streams | `business_model.revenue_type` + `business_model.price_bucket` |
| Cost Structure | `business_model.cost_structure` |
| Key Metrics | `business_model.key_metrics` |
| Unfair Advantage | `competition.unfair_advantage` |
| Existing Alternatives | `competition.alternatives` |

---

#### Artifact 2 — Assumption & Risk Register (.docx)
**Framework:** Validation Stack
**Format:** Structured table, one row per entry in `risks[]`

| Column | Source |
|---|---|
| Assumption | `risks[].assumption` |
| Risk Level | `risks[].risk_level` (High / Medium / Low) |
| How to Validate | `risks[].validation_method` |
| Status | Static: "Not yet tested" |

Sorted High → Medium → Low. The `is_riskiest: True` entry is visually highlighted.

---

#### Artifact 3 — One-Page Pitch (.docx)
**Framework:** YC Application Framework
**Format:** Single-page narrative document, 7 named sections

| Section | Source Fields | Generated Via |
|---|---|---|
| The Problem | `idea.problem`, `audience.pain_description` | LLM prose call |
| Our Solution | `solution.description`, `solution.ten_x_claim` | LLM prose call |
| Why Now | `market.timing_signal`, `idea.why_now` | LLM prose call |
| Market Size | `market.tam_estimate`, `market.size_bucket` | LLM prose call |
| Business Model | `business_model.revenue_type`, `who_pays`, `price_bucket` | LLM prose call |
| Why Us | `founder.background_relevance`, `competition.unfair_advantage` | LLM prose call |
| Biggest Risk & Plan | `risks[is_riskiest=True].assumption`, `founder.validation_plan` | LLM prose call |

Each section prompt takes raw field values and returns 2–4 sentences of polished founder-voice prose.

---

#### Stage 4 UI
- Three download buttons, one per artifact
- Each shows status: Generating → Ready to Download
- Generated in sequence: Lean Canvas → Risk Register → One-Pager
- `artifacts_generated` flags updated in canvas as each completes

---

### Stage 5 — Audio Perspectives (Stretch Goal)

**Purpose:** Generate three short audio clips voicing distinct perspectives on the validated idea. Founder listens — not interactive.

**Three Personas:**

| Persona | Perspective Focus |
|---|---|
| The Skeptical VC | Challenges market size, unfair advantage, and business model viability |
| The Target Customer | Reacts to whether the pain is real and the solution fits their life |
| The Fellow Founder / Mentor | Reflects on founder-market fit and the riskiest assumption |

**Generation Process:**
1. LLM call per persona generates a 45–60 second monologue script from the full FounderCanvas
2. Script passed to TTS provider (provider selected in Phase 6)
3. Audio returned as bytes, stored in `st.session_state` for playback
4. Streamlit `st.audio()` widget plays each clip
5. `audio_generated[persona]` flag flipped to `True` in canvas on completion

**Stage 5 UI:**
- Three persona cards, each with a name, brief description, and an audio player
- "Generate All Perspectives" button triggers all three in sequence

---

## 7. Information Flow

```
STAGE 1 — INTAKE
────────────────────────────────────────────────
Founder submits raw idea text
→ FounderCanvas initialized in st.session_state
→ idea.raw_input set
→ LLM pre-fill: idea.one_liner, idea.problem
→ stage = "interview"
→ st.rerun()


STAGE 2 — INTERVIEW (cluster loop)
────────────────────────────────────────────────
On first load:
→ generate_cluster(canvas) → first cluster stored in session_state
→ st.rerun()

Per question render:
→ UI reads current_index from current_cluster
→ Renders question using correct render_* function
→ Founder submits answer
→ Answer stored in cluster["answers"][current_index]
→ current_index incremented
→ If more questions remain → st.rerun() (next question)
→ If cluster complete → move to evaluation

Per cluster evaluation:
→ evaluate_cluster(canvas, cluster) called
→ extracted_signals merged into canvas draft fields
→ dimensions_covered[dimension] updated
→ All Q&A pairs appended to conversation_history
→ cluster appended to completed_clusters

→ is_complete(canvas)?
    True  → canvas["stage"] = "synthesis" → st.rerun()
    False → probe_needed?
        True  → generate_probe_cluster() → st.rerun()
        False → generate_cluster() (next dimension) → st.rerun()


SYNTHESIS — INTERNAL (no UI)
────────────────────────────────────────────────
Single LLM call:
  Input:  full conversation_history + FounderCanvas schema
  Output: all field groups authoritatively populated
          (overwrites Stage 2 draft values)
→ Canvas updated in session_state
→ stage = "review"
→ st.rerun()


STAGE 3 — REVIEW
────────────────────────────────────────────────
UI renders 7 cards from canvas field groups

For each founder edit:
→ LLM call: interpret correction → updated fields for that card
→ Relevant canvas fields updated in session_state
→ Card re-renders

Founder confirms → stage = "complete" → st.rerun()


STAGE 4 — ARTIFACT GENERATION
────────────────────────────────────────────────
Lean Canvas:
  → field mapping → python-docx table → bytes → download button
  → artifacts_generated["lean_canvas"] = True

Risk Register:
  → risks[] array → python-docx table → bytes → download button
  → artifacts_generated["risk_register"] = True

One-Page Pitch:
  → LLM prose call per section → python-docx narrative → bytes → download button
  → artifacts_generated["one_pager"] = True


STAGE 5 — AUDIO (STRETCH)
────────────────────────────────────────────────
For each of 3 personas:
→ LLM call generates 45–60 second script
→ TTS provider synthesizes audio → bytes stored in session_state
→ audio_generated[persona] = True
→ st.audio() widget renders player
```

---

## 8. Codebase Structure

```
founderlens/
│
├── app.py                    # Entry point. Initializes session_state.canvas.
│                             # Reads stage, calls matching render function.
│
├── llm_client.py             # All LLM API calls. Model-agnostic.
│                             # call_llm(prompt, schema=None, temperature=0.7)
│                             # Returns str (free text) or dict (parsed JSON).
│
├── interview_engine.py       # Stage 2 logic.
│                             # generate_cluster(canvas) → dict
│                             # generate_probe_cluster(canvas, dimension, probe_reason) → dict
│                             # evaluate_cluster(canvas, cluster) → dict
│                             # is_complete(canvas) → bool
│                             # apply_extracted_signals(canvas, signals) → None
│                             # build_canvas_summary(canvas) → str
│
├── synthesis_engine.py       # Post-Stage-2 authoritative extraction.
│                             # extract_canvas(canvas) → updated canvas dict
│
├── artifact_generator.py     # All .docx generation.
│                             # generate_lean_canvas(canvas) → bytes
│                             # generate_risk_register(canvas) → bytes
│                             # generate_one_pager(canvas) → bytes
│
├── audio_engine.py           # Stretch. Persona script + TTS synthesis.
│                             # generate_script(persona, canvas) → str
│                             # synthesize(script) → bytes
│
├── prompts.py                # All prompt templates as string constants.
│                             # INTERVIEW_SYSTEM
│                             # GENERATE_CLUSTER_PROMPT
│                             # GENERATE_PROBE_CLUSTER_PROMPT
│                             # EVALUATE_CLUSTER_PROMPT
│                             # QUESTION_BANK
│                             # SYNTHESIS
│                             # CARD_CORRECTION
│                             # ONE_PAGER_SECTION
│                             # PERSONA_SKEPTICAL_VC
│                             # PERSONA_TARGET_CUSTOMER
│                             # PERSONA_FELLOW_FOUNDER
│
├── ui/
│   ├── intake.py             # render_intake()
│   ├── interview.py          # render_interview()
│   ├── review.py             # render_review()
│   ├── artifacts.py          # render_artifacts()
│   └── audio.py              # render_audio() — stretch
│
├── requirements.txt
└── .env                      # API keys (gitignored)
```

**Routing in app.py:**

```python
import streamlit as st
from ui.intake import render_intake
from ui.interview import render_interview
from ui.review import render_review
from ui.artifacts import render_artifacts
from ui.audio import render_audio
from synthesis_engine import extract_canvas

def initialize_canvas():
    return {
        "stage": "intake",
        "idea": { "raw_input": None, "one_liner": None, "problem": None,
                  "solution": None, "why_now": None },
        "audience": { ... },
        # ... all field groups at defaults
        "conversation_history": [],
        "dimensions_covered": { ... all False },
        "artifacts_generated": { "lean_canvas": False, "risk_register": False, "one_pager": False },
        "audio_generated": { "skeptical_vc": False, "target_customer": False, "fellow_founder": False }
    }

if "canvas" not in st.session_state:
    st.session_state.canvas = initialize_canvas()

stage = st.session_state.canvas["stage"]

if stage == "intake":
    render_intake()
elif stage == "interview":
    render_interview()
elif stage == "synthesis":
    st.session_state.canvas = extract_canvas(st.session_state.canvas)
    st.session_state.canvas["stage"] = "review"
    st.rerun()
elif stage == "review":
    render_review()
elif stage == "complete":
    render_artifacts()
    render_audio()  # conditionally shown if stretch is implemented
```

---

## 9. LLM Interface Specification

FounderLens is model-agnostic. All LLM calls route through `llm_client.py`. The model is set via environment variable — swapping models requires no code changes.

### Interface

```python
def call_llm(
    prompt: str,
    schema: dict | None = None,  # If provided, instructs model to return JSON
    temperature: float = 0.7,
    max_tokens: int = 1000
) -> str | dict:
    """
    Returns str if schema is None (free text).
    Returns parsed dict if schema is provided (validated JSON).
    Raises on API error or JSON parse failure.
    Retries once with JSON-only instruction on parse failure.
    """
```

### Call Types and Settings

| Call | Temperature | Output | Used In |
|---|---|---|---|
| Stage 1 pre-fill | 0.2 | dict | Stage 1 on submit |
| Generate cluster | 0.7 | dict (full cluster) | Stage 2 per dimension |
| Generate probe cluster | 0.7 | dict (small cluster) | Stage 2 when probe needed |
| Evaluate cluster | 0.3 | dict (evaluation result + extracted_signals) | Stage 2 per cluster completion |
| Canvas extraction | 0.2 | dict (full canvas fields) | Synthesis |
| Card correction | 0.3 | dict (partial canvas fields) | Stage 3 per edit |
| One-pager prose | 0.8 | str (2–4 sentence paragraph) | Stage 4 per section |
| Persona script | 0.9 | str (45–60 second monologue) | Stage 5 per persona |

### Environment Configuration

```
API_KEY=your_key_here
MODEL=model-id          # any OpenAI-compatible model string
BASE_URL=https://...    # provider base URL
TTS_PROVIDER=gtts       # set during Phase 6
```

---

## 10. Prompt Engineering Specification

All prompt text lives in `prompts.py` as string constants. Logic files import and use constants — never define prompt strings inline anywhere else.

---

### INTERVIEW_SYSTEM — Stage 2 Mentor Persona
**Used in:** Every Stage 2 LLM call as the system prompt.

Must establish:
- AI is a startup mentor — direct, challenging, curious, never cheerleading
- Tone follows Mom Test principles: specific, evidence-seeking, about customer life
- Personalize every question to this founder's specific idea — never copy templates verbatim
- Never mention "Lean Canvas", "Mom Test", "YC", "dimensions", or "clusters" by name
- Never ask for information already present in the conversation history

---

### GENERATE_CLUSTER_PROMPT — Cluster Generation
**Used in:** `generate_cluster()` at the start of each new dimension.

Input context: canvas summary, dimensions_covered, conversation history, question bank

Must output: full cluster dict with 2–4 personalized questions, correct formats, helper text and placeholders only where warranted, specific yes/no labels

---

### GENERATE_PROBE_CLUSTER_PROMPT — Probe Generation
**Used in:** `generate_probe_cluster()` when evaluation returns `probe_needed: True`.

Input context: dimension, probe_reason, prior Q&A exchanges for that dimension

Must output: small cluster dict with 1–2 focused probe questions that directly address the gap

---

### EVALUATE_CLUSTER_PROMPT — Cluster Evaluation
**Used in:** `evaluate_cluster()` after all cluster answers are submitted.

Input context: all Q&A pairs from the cluster, prior signals already known for that dimension

Must output: evaluation result with `covered`, `confidence`, `probe_needed`, `probe_reason`, and `extracted_signals` nested by canvas field group

Must enforce: use `null` for absent fields — never invent; extract only what was actually said

---

### SYNTHESIS — Canvas Extraction
**Used in:** Once, immediately after Stage 2 completes.

Input context: full `conversation_history` + FounderCanvas schema

Must output: all FounderCanvas field groups authoritatively populated.

Must enforce: use `null` for absent fields — never invent. Overwrite any draft values. Extract what was actually said — do not reframe into a more optimistic version.

**This is the most critical prompt in the application.** Errors here cascade to every artifact. It requires the most iteration and testing time of any prompt in the system.

---

### CARD_CORRECTION — Stage 3 Field Update
**Used in:** Stage 3, once per founder edit.

Input context: card name, current field values for that card, founder's correction text.

Must output: updated field values for that card only. No other fields touched.

---

### ONE_PAGER_SECTION — Prose Generation
**Used in:** Stage 4, once per section of the One-Pager.

Input context: section name, relevant raw field values.

Must output: 2–4 sentences of polished prose in founder's voice.

Must enforce: do not add claims not in the source fields; do not write in corporate or generic language.

---

### PERSONA_* — Audio Monologue Scripts
**Used in:** Stage 5, once per persona.

Input context: persona brief (character + speaking style) + full FounderCanvas.

Must output: a 45–60 second spoken monologue reacting to the idea from that persona's perspective.

Constants: `PERSONA_SKEPTICAL_VC`, `PERSONA_TARGET_CUSTOMER`, `PERSONA_FELLOW_FOUNDER`

---

## 11. Development Phases

### Phase 1 — Foundation
**Goal:** Project scaffold working. FounderCanvas initializes correctly in session_state. Stage routing functional.

Deliverables:
- `app.py` with stage routing and `initialize_canvas()`
- All `ui/*.py` files with placeholder render functions
- `prompts.py` created with empty constant placeholders
- `.env` configured, `requirements.txt` complete

---

### Phase 2 — Conversation Engine
**Goal:** Stage 2 fully functional end-to-end using cluster architecture. A complete interview can be run in the app.

Deliverables:
- `INTERVIEW_SYSTEM`, `GENERATE_CLUSTER_PROMPT`, `GENERATE_PROBE_CLUSTER_PROMPT`, `EVALUATE_CLUSTER_PROMPT`, and `QUESTION_BANK` constants written and iterated
- `interview_engine.py`: `generate_cluster()`, `generate_probe_cluster()`, `evaluate_cluster()`, `apply_extracted_signals()`, `is_complete()`, `build_canvas_summary()` all working
- `ui/interview.py`: cluster-driven question rendering, one question at a time, correct render_* function per format
- Full interview loop completes across all 7 dimensions and transitions to synthesis stage
- Error handling: JSON parse retry, empty cluster guard

---

### Phase 3 — Synthesis & Review
**Goal:** Canvas extraction working correctly. Stage 3 cards render and edit flow functions.

Deliverables:
- `SYNTHESIS` and `CARD_CORRECTION` prompt constants written and iterated
- `synthesis_engine.py`: extraction call populates canvas authoritatively, overwrites draft values
- `ui/review.py`: 7 cards render from canvas fields, edit flow calls correction LLM and re-renders card
- Retry logic on synthesis call in case of JSON parse failure (up to 2 retries)

---

### Phase 4 — Artifact Generation
**Goal:** All three `.docx` files generate correctly from a completed canvas.

Deliverables:
- `ONE_PAGER_SECTION` prompt constant
- `artifact_generator.py`: all three generation functions returning valid `.docx` bytes
- `ui/artifacts.py`: download buttons wired to generated bytes, `artifacts_generated` flags updated
- Tested against at least two different completed canvases

---

### Phase 5 — Integration, Polish & Deployment
**Goal:** Full end-to-end flow working on Streamlit Cloud. Edge cases handled.

Deliverables:
- End-to-end session tested: Stage 1 through Stage 4
- Edge cases handled: very short answers, single-word answers, contradictions, null fields after synthesis
- UI polished: consistent styling, loading spinners, error messages
- Session loss warning shown in UI once artifacts are ready
- Deployed to Streamlit Cloud with API key in Streamlit Secrets

---

### Phase 6 — Audio Perspectives (Stretch)
**Goal:** Three audio personas generate and play in the app.

Deliverables:
- TTS provider selected and integrated in `audio_engine.py`
- Three persona prompt constants written
- `ui/audio.py`: three audio players rendering and playing correctly
- `audio_generated` flags updated in canvas as each clip is generated

---

## 12. Open Decisions & Constraints

### Open Decisions

| Decision | Status | Due |
|---|---|---|
| Primary model | Open — interface is model-agnostic | Before Phase 2 |
| TTS provider (gTTS vs ElevenLabs vs other) | Intentionally deferred | Phase 6 |

### Known Constraints

- **Rate limits:** Cluster architecture reduces Stage 2 to 15–22 total LLM calls across the full interview (best case: 15, worst case with all probes: 22). This is well within a 30 requests/minute limit even for fast sessions.
- **Synthesis call is a single point of failure:** If the extraction prompt fails to produce valid JSON, Stage 3 cannot render. Build retry logic (up to 2 retries) and a fallback partial-extraction path that renders cards with whatever fields were successfully extracted.
- **Draft vs authoritative values:** Canvas field groups are partially populated during Stage 2 as draft values from `extracted_signals`. The synthesis call always overwrites these. Nothing in Stage 3 or Stage 4 should read from canvas fields before synthesis has completed.
- **Session loss on tab close:** All state lives in `st.session_state`. Closing the browser tab loses the session permanently. Show a persistent reminder once artifacts are available to download before leaving.
- **Artifact bytes in session_state:** Generated `.docx` bytes and audio bytes are held in session_state for download and playback buttons. Fine for typical sizes. If memory becomes a concern, generate on-demand rather than caching.

---

*FounderLens PRD — Concept locked. Build begins Phase 1.*