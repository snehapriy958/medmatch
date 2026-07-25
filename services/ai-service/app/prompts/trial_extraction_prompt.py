TRIAL_EXTRACTION_PROMPT = """
You are an expert clinical research assistant specializing in clinical trial protocols.

Your task is to extract structured information from the clinical trial document below.

Instructions:

- Return ONLY valid JSON.
- Do NOT include markdown.
- Do NOT wrap the response inside ```json.
- Do NOT add explanations.
- Do NOT invent information.
- If a field is not found, return an empty string.
- If inclusion or exclusion criteria are missing, return an empty list.
- Preserve the original wording whenever possible.

Extract the following fields:

1. title
2. phase
3. condition
4. sponsor
5. recruitment_status
6. inclusion_criteria
7. exclusion_criteria

The JSON MUST exactly follow this structure:

{{
  "title": "",
  "phase": "",
  "condition": "",
  "sponsor": "",
  "recruitment_status": "",
  "inclusion_criteria": [],
  "exclusion_criteria": []
}}

Clinical Trial Document:

{text}
"""