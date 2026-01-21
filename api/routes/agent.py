from fastapi import APIRouter
from agent.core import Agent
from agent.tools import execute_tool

router = APIRouter()

@router.post("/respond")
def execute_command(message: str, user_id: str):
    agent = Agent()

    result_context = []
    result_context.append({"role": "user", "content": message})

    plan_response = agent.process_request(
        message=message,
        user_id=user_id,
        context=result_context
    )

    plans = plan_response["plans"]

    for plan in plans:
        result = execute_tool(plan)
        result_context.append({
            "role": "tool",
            "content": result
        })

    final_response = agent.process_request(
        message="Generate a summary of actions taken",
        user_id=user_id,
        context=result_context
    )

    return {
        "status": "completed",
        "summary": final_response["message"]
    }
