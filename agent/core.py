import json
from openai import OpenAI
from agent.prompts import (
    SYSTEM_PROMPT,
    PLANNING_PROMPT,
    SUMMARY_PROMPT,
    CHAT_PROMPT
)
from config import settings

client = OpenAI(api_key=settings.OPENAI_API_KEY)

class Agent:
    def process_request(self, message: str, user_id: str, context: list, mode: str = "plan"):
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
        elif mode == "summarize":
            prompt = SUMMARY_PROMPT.format(context=json.dumps(safe_context, ensure_ascii=True))
        elif mode == "chat":
            prompt = CHAT_PROMPT.format(message=message)
        else:
            prompt = message

        response = client.chat.completions.create(
            model="gpt-4.1",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                *safe_context,
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_object"},
        )

        content = response.choices[0].message.content or "{}"
        return json.loads(content)