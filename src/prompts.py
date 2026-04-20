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
