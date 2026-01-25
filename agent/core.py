import json
from openai import OpenAI
from agent.prompts import SYSTEM_PROMPT, PLANNING_PROMPT
from config import settings

client = OpenAI(api_key=settings.OPENAI_API_KEY)

class Agent:
    def process_request(
        self,
        message: str,
        user_id: str,
        context: list,
        mode: str = "plan"
    ):
        if mode == "plan":
            prompt = f"""
            This is the user message:
            {message}

            Break it down into precise backend actions.
            No redundant steps.
            """
        elif mode == "summarize":
            prompt = f"""
            We are preparing a final response to the user.
            Here is the full context:
            {context}

            Be polite and concise.
            """
        elif mode == "create_email":
            prompt = f"""
            Write an email.
            Must start with 'Dear ...'
            Must end politely.
            Content:
            {message}
            """
        else:
            prompt = message

        response = client.chat.completions.create(
            model="gpt-4.1",                                    # which model
            messages=[                                          # full conversation context
                {"role": "system", "content": SYSTEM_PROMPT},
                *context,
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"}             # json output
        )

        return json.loads(response.choices[0].message.content)