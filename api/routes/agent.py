from fastapi import APIRouter
from agent.core import Agent
from agent.tools import execute_tool
from agent.schemas import ExecuteRequest

router = APIRouter()

@router.post("/respond")
def execute_command(request: ExecuteRequest):
    message = request.message
    user_id = request.user_id

    agent = Agent()
    result_context = [{"role": "user", "content": message}]

    plan_response = agent.process_request(
        message=message,
        user_id=user_id,
        context=result_context,
        mode="plan"
    )

    plans = plan_response.get("plans", [])
    results = []

    for plan in plans:
        try:
            res = execute_tool(plan)
            results.append({"plan": plan, "result": res})
            result_context.append({"role": "tool", "content": res})
        except Exception as e:
            results.append({"plan": plan, "error": str(e)})

    final_summary = agent.process_request(
        message="Summarize actions taken",
        user_id=user_id,
        context=result_context,
        mode="summarize"
    )

    return {
        "status": "completed",
        "results": results,
        "summary": final_summary.get("message", "")
    }