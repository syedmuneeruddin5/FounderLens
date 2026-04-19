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

`conversation_history` is an array field that lives inside the FounderCanvas. It is not a separate structure. It is built up incrementally during Stage 2: every time the founder answers a question, one entry is appended to this array. By the end of Stage 2, it contains the complete record of the interview.

It exists for one primary purpose: the synthesis call after Stage 2 takes the full `conversation_history` as its input and extracts all FounderCanvas fields from it. Nothing else reads from it directly.

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

    "stage3_edits": [
        # Audit trail of founder corrections in Stage 3.
        # {
        #   "card": str,            — which card was edited
        #   "original_value": str,
        #   "corrected_value": str
        # }
    ],

    "artifacts_generated": {
        "lean_canvas": False,
        "risk_register": False,
        "one_pager": False
    }
}
```

### Field Population Timeline

| Field Group | Populated In | Used In |
|---|---|---|
| `idea.raw_input` | Stage 1 | Stage 2 prompt context |
| `idea.one_liner`, `idea.problem` | Stage 1 (quick AI pre-fill) | Stage 2 starting context |
| `conversation_history` | Stage 2 — one entry appended per exchange | Synthesis call |
| `dimensions_covered` | Stage 2 — updated after each answer evaluation | Stage 2 exit condition |
| All other field groups | Synthesis call (post-Stage-2, pre-Stage-3) | Stage 3 cards, Stage 4 artifacts |
| `stage3_edits` | Stage 3 — on each founder correction | Audit trail |
| `artifacts_generated` | Stage 4 — flipped to True on generation | UI download status |

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
│Question│  │ .docx x3 │   │ 3 persona  │
│picking │  │          │   │   clips    │
│Synthesis   └──────────┘   └────────────┘
│ call   │
└────────┘
```

### Module Responsibilities

| File | Responsibility |
|---|---|
| `app.py` | Entry point. Initializes `session_state.canvas` if absent. Reads `stage`, calls matching render function. |
| `llm_client.py` | All OpenRouter API calls. Model-agnostic. Accepts prompt + optional JSON schema. Returns text or parsed dict. |
| `interview_engine.py` | Stage 2 logic. Evaluates answers, picks next question, updates `dimensions_covered`, detects exit condition. |
| `synthesis_engine.py` | Single LLM call after Stage 2. Extracts all FounderCanvas fields from `conversation_history`. |
| `artifact_generator.py` | Generates all three `.docx` files from FounderCanvas using `python-docx`. |
| `audio_engine.py` | Stretch. Generates persona scripts and synthesizes audio via TTS provider. |
| `ui/intake.py` | `render_intake()` — Stage 1 UI |
| `ui/interview.py` | `render_interview()` — Stage 2 UI. One question at a time. |
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
- Clean landing page with app name and a one-line description
- Single large text area: *"Describe your startup idea. Don't worry about being perfect — just tell us what you're trying to build and who it's for."*
- Submit button: "Start My Validation Session"

**On Submit:**
1. Initialize the full FounderCanvas dict in `st.session_state.canvas` with all fields at their defaults
2. Set `canvas["idea"]["raw_input"]` to the submitted text
3. Call LLM to pre-fill `idea.one_liner` and `idea.problem` from the raw input (temperature 0.2, quick extraction)
4. Set `canvas["stage"] = "interview"`
5. Streamlit reruns → Stage 2 renders

**Exit Condition:** Founder submits non-empty text.

---

### Stage 2 — AI Mentor Interview

**Purpose:** Conduct a directed, adaptive interview across all 7 dimensions. Build `conversation_history`. Mark `dimensions_covered` as coverage is achieved. Exit when all 7 are `True`.

**UX Feel:** Guided interview. One question at a time. Not a chat UI — each question is a distinct panel. The founder sees no dimension labels or progress percentage — it simply feels like a mentor working through topics naturally.

**How the Loop Works (per submission):**

```
Founder submits an answer
  → Answer appended to canvas["conversation_history"]
  → LLM Call 1 — Answer Evaluation:
      Input:  current canvas state + the answer just submitted
      Output: { "covered": bool, "probe_needed": bool, "probe_question": str | null }
  → If covered: dimensions_covered[dimension] = True
  → Check exit: all 7 dimensions True? → stage = "synthesis" → st.rerun()
  → LLM Call 2 — Next Question:
      Input:  updated canvas state
      Output: { "question": str, "format": str, "options": list | null, "dimension": str }
  → Next question stored in session_state
  → st.rerun() → renders next question
```

**Question Formats:**
- `multiple_choice` — rendered as radio buttons or button group. Used when the answer space is bounded.
- `scale` — segmented control (e.g. Daily / Weekly / Monthly / Rarely). Used for frequency or intensity.
- `open_text` — multi-line text area. Used when evidence, narrative, or nuance is needed.
- `yes_no` — two buttons. Always followed by a probe based on the answer.

---

#### The 7 Dimensions — Full Question Bank

Each dimension has seed questions (asked first) and probe questions (triggered when answers are vague, hypothetical, or contradictory). The AI selects the next question based on what has been covered and the quality of recent answers.

---

**Dimension 1 — Problem Discovery**
Goal: Establish that the problem is real, painful, frequent, and observable — not assumed.

| # | Question | Format | Field Targeted |
|---|---|---|---|
| 1.1 | "How would you describe the core problem your idea solves, in one sentence?" | open_text | `idea.problem` |
| 1.2 | "How often does your target customer run into this problem?" | scale: Daily / Weekly / Monthly / Rarely | `audience.pain_description` |
| 1.3 | "What's the real cost of this problem not being solved — what actually happens to them?" | open_text | `audience.pain_description` |
| 1.4 (probe) | "You mentioned [X] — is that something you've seen directly, or is it an assumption?" | multiple_choice: Seen it myself / Heard from others / Logical assumption | `founder.known_vs_guessed` |
| 1.5 (probe) | "Can you describe a specific moment when this problem caused someone a real frustration?" | open_text | `audience.pain_description` |

Covered when: `idea.problem` and `audience.pain_description` are populated with specific, non-hypothetical content.

---

**Dimension 2 — Target Audience**
Goal: Narrow from a broad group to a specific, nameable early adopter.

| # | Question | Format | Field Targeted |
|---|---|---|---|
| 2.1 | "If you could only sell to 10 people first, who would they be? What do they have in common?" | open_text | `audience.early_adopter_profile` |
| 2.2 | "Are these people currently paying for any solution to this problem?" | multiple_choice: Yes, paying / Yes, using free tools / No, nothing / Not sure | `audience.willingness_to_pay` |
| 2.3 (probe) | "You described [X group] — within that group, who feels this pain most acutely?" | open_text | `audience.primary_segment` |
| 2.4 (probe) | "How does your target customer currently describe this problem to themselves, in their own words?" | open_text | `audience.pain_description` |

Covered when: `audience.primary_segment` and `audience.early_adopter_profile` are specific and distinct from a generic demographic.

---

**Dimension 3 — Market & Timing**
Goal: Establish market size signal and a credible "why now" rationale.

| # | Question | Format | Field Targeted |
|---|---|---|---|
| 3.1 | "What's changed recently — in technology, behavior, or regulation — that makes this problem solvable now when it wasn't before?" | open_text | `market.timing_signal` |
| 3.2 | "How many people do you think have this problem, roughly?" | multiple_choice: Thousands / Hundreds of thousands / Millions / Not sure | `market.size_bucket` |
| 3.3 (probe) | "Is there a specific trend or recent event you're riding, or has this problem always existed?" | open_text | `market.timing_signal` |
| 3.4 (probe) | "What would need to be true about the market for this to be a significant company in 5 years?" | open_text | `market.tam_estimate` |

Covered when: `market.timing_signal` is specific (not generic like "AI is growing") and `market.size_bucket` is set.

---

**Dimension 4 — Solution Pressure**
Goal: Establish that the solution is meaningfully better, not incrementally different.

| # | Question | Format | Field Targeted |
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

| # | Question | Format | Field Targeted |
|---|---|---|---|
| 5.1 | "List the top two or three things people use today to solve this problem — even if they're imperfect." | open_text | `competition.alternatives` |
| 5.2 | "Why haven't those alternatives fully solved it?" | multiple_choice: Too expensive / Too complex / Not designed for this / People aren't aware / Other | `competition.alternatives_shortfall` |
| 5.3 | "What's your unfair advantage — something that would be genuinely hard to copy?" | multiple_choice: Domain expertise / Proprietary data / Network effects / First-mover / Team background / Not sure yet | `competition.advantage_type` |
| 5.4 (probe) | "If a well-funded startup built your exact product, what would make you still win?" | open_text | `competition.unfair_advantage` |

Covered when: `competition.alternatives` has at least two entries and `competition.differentiation` is populated.

---

**Dimension 6 — Business Model**
Goal: Establish a credible revenue hypothesis and basic unit economics thinking.

| # | Question | Format | Field Targeted |
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

| # | Question | Format | Field Targeted |
|---|---|---|---|
| 7.1 | "Why are you the right person to build this? What do you know or have access to that others don't?" | open_text | `founder.background_relevance` |
| 7.2 | "What's the single assumption your whole idea rests on — the one thing that, if wrong, kills this?" | open_text | `risks[]` (is_riskiest: True) |
| 7.3 | "Have you validated anything yet?" | multiple_choice: Talked to potential users / Built a prototype / Both / Not yet | `founder.validation_done` |
| 7.4 (probe) | "What's your plan to test that riskiest assumption before building further?" | open_text | `founder.validation_plan` |
| 7.5 (probe) | "What do you know from real evidence versus what are you currently assuming?" | open_text | `founder.known_vs_guessed` |

Covered when: `founder.background_relevance`, at least one `risks[]` entry, and `founder.validation_done` are populated.

---

#### Stage 2 Exit Condition
All 7 values in `dimensions_covered` are `True`. Checked after every answer evaluation. Minimum ~12 exchanges, maximum ~20. Coverage quality — not question count — is the trigger.

#### Stage 2 Adaptive Rules (enforced in system prompt)
- If a founder gives a hypothetical answer → probe for evidence before marking covered
- If a founder contradicts an earlier answer → surface the contradiction before moving on
- If a dimension is already clearly addressed by a prior answer → skip its seed question and mark it covered
- Never ask two questions in one turn
- Never refer to "dimensions", "frameworks", or "Lean Canvas" by name — the founder should feel like they're speaking with a mentor, not filling a rubric

---

### Stage 3 — Synthesis Review

**Purpose:** Extract the full FounderCanvas from the conversation in one structured LLM call. Render it as 7 editable cards. Let the founder correct any misunderstandings before artifact generation.

**Synthesis Call (runs immediately when stage becomes "synthesis" — no UI shown during this):**
- Input: full `conversation_history` array + FounderCanvas schema
- Prompt: "Extract all fields from this conversation into this exact schema. Use null where absent — do not invent."
- Output: fully populated FounderCanvas field groups
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
- Edit logged to `stage3_edits[]`
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


STAGE 2 — INTERVIEW (Streamlit rerun loop)
────────────────────────────────────────────────
UI renders current question from session_state

Founder submits answer
→ Answer appended to conversation_history
→ LLM Call 1 — Answer Evaluation:
    Input:  canvas state + answer
    Output: { covered, probe_needed, probe_question }
→ If covered: dimensions_covered[dimension] = True
→ Check: all 7 True? → stage = "synthesis" → st.rerun() → exits loop
→ LLM Call 2 — Next Question:
    Input:  updated canvas state
    Output: { question, format, options, dimension }
→ Next question stored in session_state
→ st.rerun() → renders next question


SYNTHESIS — INTERNAL (no UI)
────────────────────────────────────────────────
Single LLM call:
  Input:  full conversation_history + FounderCanvas schema
  Output: all field groups populated
→ Canvas updated with extracted fields
→ stage = "review"
→ st.rerun()


STAGE 3 — REVIEW
────────────────────────────────────────────────
UI renders 7 cards from canvas field groups

For each founder edit:
→ LLM call: interpret correction → updated fields for that card
→ Relevant canvas fields updated in session_state
→ Edit logged to stage3_edits[]
→ Card re-renders

Founder confirms → stage = "complete" → st.rerun()


STAGE 4 — ARTIFACT GENERATION
────────────────────────────────────────────────
Lean Canvas:
  → field mapping → python-docx table → bytes → download button

Risk Register:
  → risks[] array → python-docx table → bytes → download button

One-Page Pitch:
  → LLM prose call per section → python-docx narrative → bytes → download button

artifacts_generated flags updated as each completes


STAGE 5 — AUDIO (STRETCH)
────────────────────────────────────────────────
For each of 3 personas:
→ LLM call generates 45–60 second script
→ TTS provider synthesizes audio → bytes stored in session_state
→ st.audio() widget renders player
```

---

## 8. Codebase Structure

```
FounderLens/
│
├── app.py                    # Entry point. Initializes session_state.canvas.
│                             # Reads stage, calls matching render function.
│
├── llm_client.py             # All OpenRouter API calls.
│                             # call_llm(prompt, schema=None, temperature=0.7)
│                             # Returns str (free text) or dict (parsed JSON).
│
├── interview_engine.py       # Stage 2 logic.
│                             # evaluate_answer(canvas, answer) → dict
│                             # get_next_question(canvas) → dict
│                             # is_interview_complete(canvas) → bool
│
├── synthesis_engine.py       # Post-Stage-2 extraction.
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
│                             # INTERVIEW_SYSTEM, NEXT_QUESTION, SYNTHESIS,
│                             # CARD_CORRECTION, ONE_PAGER_SECTION,
│                             # PERSONA_SKEPTICAL_VC, PERSONA_TARGET_CUSTOMER,
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
└── .env                      # OPENROUTER_API_KEY, OPENROUTER_MODEL (gitignored)
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
    """
```

### Call Types and Settings

| Call | Temperature | Output | Used In |
|---|---|---|---|
| Stage 1 pre-fill | 0.2 | dict | Stage 1 on submit |
| Answer evaluation | 0.3 | dict `{covered, probe_needed, probe_question}` | Stage 2 per answer |
| Next question | 0.5 | dict `{question, format, options, dimension}` | Stage 2 per turn |
| Canvas extraction | 0.2 | dict (full canvas fields) | Synthesis |
| Card correction | 0.3 | dict (partial canvas fields) | Stage 3 per edit |
| One-pager prose | 0.8 | str (2–4 sentence paragraph) | Stage 4 per section |
| Persona script | 0.9 | str (45–60 second monologue) | Stage 5 per persona |

### Environment Configuration

```
OPENROUTER_API_KEY=your_key_here
OPENROUTER_MODEL=anthropic/claude-sonnet-4   # any OpenRouter-compatible model ID
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
TTS_PROVIDER=gtts                             # set during Phase 6
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
- One question per turn — no exceptions
- Never mention "Lean Canvas", "Mom Test", "YC", or "dimensions" by name
- Never ask for information already present in the conversation history
- Probe when answers are vague or hypothetical before marking a dimension covered

---

### NEXT_QUESTION — Question Selection
**Used in:** Stage 2, after each answer evaluation.

Input context: current canvas state, conversation_history, dimensions_covered

Must output: `{ "question": str, "format": str, "options": list | null, "dimension": str, "is_probe": bool }`

Must enforce: never repeat a question; prioritize dimensions with no coverage; never combine two questions into one.

---

### SYNTHESIS — Canvas Extraction
**Used in:** Once, immediately after Stage 2 completes.

Input context: full `conversation_history` + FounderCanvas schema

Must output: all FounderCanvas field groups as a valid dict matching the schema.

Must enforce: use `null` for absent fields — never invent. Extract what was actually said. Do not reframe answers into a more optimistic version.

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
**Goal:** Stage 2 fully functional end-to-end. A complete interview can be run in the app.

Deliverables:
- `llm_client.py` working against OpenRouter
- `INTERVIEW_SYSTEM` and `NEXT_QUESTION` prompt constants written and iterated
- `interview_engine.py`: `evaluate_answer()`, `get_next_question()`, `is_interview_complete()` all working
- `ui/interview.py`: question renders correctly per format type
- Full interview loop completes and transitions to synthesis stage

Note: Two LLM calls per answer (evaluate + next question) may be combined into one call returning both outputs, to reduce latency. Evaluate during Phase 2.

---

### Phase 3 — Synthesis & Review
**Goal:** Canvas extraction working correctly. Stage 3 cards render and edit flow functions.

Deliverables:
- `SYNTHESIS` and `CARD_CORRECTION` prompt constants written and iterated
- `synthesis_engine.py`: extraction call populates canvas correctly from conversation
- `ui/review.py`: 7 cards render from canvas; edit flow updates canvas and re-renders the relevant card
- Retry logic on synthesis call in case of JSON parse failure

---

### Phase 4 — Artifact Generation
**Goal:** All three `.docx` files generate correctly from a completed canvas.

Deliverables:
- `ONE_PAGER_SECTION` prompt constant
- `artifact_generator.py`: all three generation functions returning valid `.docx` bytes
- `ui/artifacts.py`: download buttons wired to generated bytes
- Tested against at least two different completed canvases

---

### Phase 5 — Integration, Polish & Deployment
**Goal:** Full end-to-end flow working on Streamlit Cloud. Edge cases handled.

Deliverables:
- End-to-end session tested: Stage 1 → Stage 4
- Edge cases handled: very short answers, single-word answers, contradictions, null fields after synthesis
- UI polished: consistent styling, loading spinners, error messages
- Session loss warning shown in UI: "Don't close this tab until you've downloaded your artifacts"
- Deployed to Streamlit Cloud with API key in Streamlit Secrets

---

### Phase 6 — Audio Perspectives (Stretch)
**Goal:** Three audio personas generate and play in the app.

Deliverables:
- TTS provider selected and integrated in `audio_engine.py`
- Three persona prompt constants written
- `ui/audio.py`: three audio players rendering and playing correctly

---

## 12. Open Decisions & Constraints

### Open Decisions

| Decision | Status | Due |
|---|---|---|
| Primary OpenRouter model | Open — interface is model-agnostic | Before Phase 2 |
| TTS provider (gTTS vs ElevenLabs vs other) | Intentionally deferred | Phase 6 |
| Combine evaluate + next-question into single LLM call | To be evaluated for latency | Phase 2 |

### Known Constraints

- **Two LLM calls per Stage 2 answer:** Each answer triggers an evaluation call and a next-question call. On slower models this may feel sluggish. Consider merging into one call that returns `{ covered, probe_needed, next_question, format, options, dimension }` — reduces latency by half per turn.
- **Synthesis call is a single point of failure:** If the extraction prompt fails to produce valid JSON matching the schema, Stage 3 cannot render. Build retry logic (up to 2 retries) and a fallback partial-extraction path that renders cards with whatever fields were successfully extracted.
- **Session loss on tab close:** All state lives in `st.session_state`. Closing the browser tab loses the session permanently. Communicate this clearly in the UI — show a persistent reminder once artifacts are available to download before leaving.
- **Artifact bytes in session_state:** Generated `.docx` bytes are held in session_state for the download buttons. This is fine for typical document sizes. If memory becomes a concern in later phases, generate on-demand rather than caching.

---

*FounderLens PRD — Concept locked. Build begins Phase 1.*
