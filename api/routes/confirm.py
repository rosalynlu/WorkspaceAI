from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from dependencies.auth import get_current_user_id
from agent.tools import execute_tool
from agent.core import Agent
from services.action_requests import get_action_request, mark_action_request
from services.messages import create_message

router = APIRouter()

class ConfirmRequest(BaseModel):
    action_request_id: str
    approved: bool

@router.post("/confirm")
def confirm_action(payload: ConfirmRequest, user_id: str = Depends(get_current_user_id)):
    req = get_action_request(user_id=user_id, action_request_id=payload.action_request_id)
    if not req:
        raise HTTPException(status_code=404, detail="Action request not found")

    if req.get("status") != "pending":
        raise HTTPException(status_code=400, detail=f"Action request is not pending (status={req.get('status')})")

    if not payload.approved:
        mark_action_request(payload.action_request_id, user_id, "canceled")
        create_message(user_id, "assistant", "Okay — I won’t do that.")
        return {"status": "canceled", "summary": "Okay — I won’t do that."}

    # approved -> execute
    mark_action_request(payload.action_request_id, user_id, "approved")

    plans = req.get("plans") or []
    results = []
    context = [{"role": "user", "content": req.get("user_message", "")}]

    for plan in plans:
        try:
            res = execute_tool(plan, user_id=user_id)
            results.append({"plan": plan, "result": res})
            context.append({"role": "assistant", "content": {"tool_result": res}})
            create_message(user_id, "tool", {"plan": plan, "result": res})
        except Exception as e:
            results.append({"plan": plan, "error": str(e)})
            mark_action_request(payload.action_request_id, user_id, "failed", {"error": str(e)})
            raise HTTPException(status_code=500, detail=f"Tool execution failed: {e}")

    agent = Agent()
    final_summary = agent.process_request(
        message="Summarize actions taken",
        user_id=user_id,
        context=context,
        mode="summarize",
    )
    summary_text = final_summary.get("message", "Done.")
    create_message(user_id, "assistant", summary_text)
    mark_action_request(payload.action_request_id, user_id, "executed", {"results": results})

    return {"status": "completed", "results": results, "summary": summary_text}