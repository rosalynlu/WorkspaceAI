from fastapi import APIRouter, HTTPException, Depends
from agent.core import Agent
from agent.tools import execute_tool
from agent.schemas import ExecuteRequest
from dependencies.auth import get_current_user_id
from services.messages import create_message
from services.action_requests import create_action_request

router = APIRouter()

# any tool here causes real side effects -> ALWAYS require confirmation server-side
SIDE_EFFECT_TOOLS = {"create_email", "create_doc", "create_calendar_event"}


def _needs_confirmation(plans: list) -> bool:
    """Enforce confirmation for any side-effect tool, regardless of what the model says."""
    for plan in plans:
        if isinstance(plan, dict) and plan.get("function_name") in SIDE_EFFECT_TOOLS:
            return True
    return False


@router.post("/respond")
def execute_command(request: ExecuteRequest, user_id: str = Depends(get_current_user_id)):
    message = request.message.strip()
    if not message:
        raise HTTPException(status_code=400, detail="Message is required")

    # log user message (audit trail)
    create_message(user_id, "user", message)

    agent = Agent()
    context = [{"role": "user", "content": message}]

    # single plan call (no classify)
    try:
        plan_response = agent.process_request(
            message=message,
            user_id=user_id,
            context=context,
            mode="plan",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent planning failed: {e}")

    intent = plan_response.get("intent")
    if intent == "chat":
        reply = plan_response.get("message", "") or ""
        create_message(user_id, "assistant", reply)
        return {"status": "completed", "results": [], "summary": reply}

    if intent != "action":
        raise HTTPException(status_code=500, detail="Agent returned invalid intent")

    plans = plan_response.get("plans", [])
    if not isinstance(plans, list) or not plans:
        raise HTTPException(status_code=500, detail="Agent returned no plans")

    # SERVER-ENFORCED CONFIRMATION: do not trust the model to decide this.
    requires_confirmation = _needs_confirmation(plans)

    confirmation_message = (
        plan_response.get("confirmation_message")
        or "I’m ready to do that. Do you want me to proceed?"
    )

    # confirmation path (store pending action request, do not execute yet)
    if requires_confirmation:
        action_request_id = create_action_request(
            user_id=user_id,
            user_message=message,
            plans=plans,
            confirmation_message=confirmation_message,
        )

        create_message(
            user_id,
            "assistant",
            f"{confirmation_message}\n\nReply with /confirm {action_request_id} to proceed, or /cancel {action_request_id}.",
        )

        return {
            "status": "needs_confirmation",
            "action_request_id": action_request_id,
            "confirmation_message": confirmation_message,
            "plans": plans,
        }

    # execute immediately (only for non-side-effect actions; can add read-only tools later)
    results = []
    for plan in plans:
        if not isinstance(plan, dict):
            results.append({"plan": plan, "error": "Plan is not a dictionary"})
            continue

        fn = plan.get("function_name")
        args = plan.get("arguments", {})
        if not fn or not isinstance(args, dict):
            results.append({"plan": plan, "error": "Invalid plan shape"})
            continue

        try:
            res = execute_tool(plan, user_id=user_id)
            results.append({"plan": plan, "result": res})
            create_message(user_id, "tool", {"plan": plan, "result": res})
            context.append({"role": "assistant", "content": {"tool_result": res}})
        except Exception as e:
            results.append({"plan": plan, "error": str(e)})

    # summarize
    try:
        final_summary = agent.process_request(
            message="Summarize actions taken",
            user_id=user_id,
            context=context,
            mode="summarize",
        )
        summary_text = final_summary.get("message", "") or ""
    except Exception as e:
        summary_text = f"Summary generation failed: {e}"

    create_message(user_id, "assistant", summary_text)
    return {"status": "completed", "results": results, "summary": summary_text}