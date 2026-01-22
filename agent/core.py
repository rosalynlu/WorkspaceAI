import json
from openai import OpenAI
from agent.prompts import SYSTEM_PROMPT, PLANNING_PROMPT
from config import settings

client = OpenAI(api_key=settings.OPENAI_API_KEY)

class Agent:
    def process_request(self, message: str, user_id: str, context: list):
        """
        Send user message + context to OpenAI and parse JSON plan
        """
        prompt = PLANNING_PROMPT.format(message=message)

        response = client.chat.completions.create(
            model="gpt-4.1",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                *context,
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"}
        )

        return json.loads(response.choices[0].message.content)