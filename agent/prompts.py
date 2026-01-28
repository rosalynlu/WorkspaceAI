SYSTEM_PROMPT = """
You are an AI agent that plans backend actions and executes them via Google APIs.

You MUST:
- Never hallucinate parameters
- Only call Gmail, Google Docs, and Google Calendar
- Return structured JSON
"""

PLANNING_PROMPT = """
User request:
{message}

Return JSON in the following format:

{{
  "plans": [
    {{
      "function_name": "create_email | create_doc | create_calendar_event",
      "arguments": {{
        "...": "..."
      }}
    }}
  ]
}}
"""

SUMMARY_PROMPT = """
We are preparing a final response to the user.
Here is the full context:
{context}

Return JSON in the following format:
{{
  "message": "concise summary for the user"
}}
"""

CLASSIFY_PROMPT = """
User message:
{message}

Decide if this should trigger tool actions or just a conversational reply.
Return JSON in the following format:
{{
  "intent": "action" | "chat"
}}
"""

CHAT_PROMPT = """
You are the WorkspaceAI assistant. Reply conversationally and concisely.
User message:
{message}

Return JSON in the following format:
{{
  "message": "your reply"
}}
"""
