import json
from openai import OpenAI
from agent.prompts import (
    SYSTEM_PROMPT,
    PLANNING_PROMPT,
    SUMMARY_PROMPT,
    CLASSIFY_PROMPT,
    CHAT_PROMPT,
)
from config import settings

client = OpenAI(api_key=settings.OPENAI_API_KEY)

# TODO: need confirmation for take action chat response
# if plan mode gives back a list of actions, we should ask the user first? 
class Agent:
    def process_request(
        self,
        message: str,
        user_id: str,
        context: list,
        mode: str = "plan"
    ):
        safe_context = []
        for item in context:
            if not isinstance(item, dict):
                safe_context.append({"role": "user", "content": json.dumps(item, ensure_ascii=True)})
                continue
            content = item.get("content")
            if not isinstance(content, str):
                content = json.dumps(content, ensure_ascii=True)
            safe_context.append({"role": item.get("role", "user"), "content": content})
        if mode == "plan":
            prompt = PLANNING_PROMPT.format(message=message)
        elif mode == "classify":
            prompt = CLASSIFY_PROMPT.format(message=message)
        elif mode == "summarize":
            prompt = SUMMARY_PROMPT.format(context=json.dumps(safe_context, ensure_ascii=True))
        elif mode == "chat":
            prompt = CHAT_PROMPT.format(message=message)
        elif mode == "create_email":
            # Move all prompts into the prompts.py file unless it can NOT be moved.
            prompt = f"""
            Write an email.
            Must start with 'Dear ...'
            Must end politely.
            Content:
            {message}
            """
        else:
            prompt = message

        # stateless
        response = client.chat.completions.create(
            model="gpt-4.1",                                    # which model
            messages=[                                          # full conversation context
                {"role": "system", "content": SYSTEM_PROMPT},
                *safe_context,
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"}             # json output
        )

        content = response.choices[0].message.content or "{}"
        return json.loads(content)