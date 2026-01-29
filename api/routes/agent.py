from fastapi import APIRouter, HTTPException
from agent.core import Agent
from agent.tools import execute_tool
from agent.schemas import ExecuteRequest
from db import users_collection

router = APIRouter()

@router.post("/respond")
def execute_command(request: ExecuteRequest):
    message = request.message
    user_id = request.user_id

    # Security concern: anyone can use your /respond as long as they have your user_id. 

    # user signs in (username/password, sign in with Google/Apple -> once verified -> have a new API /token that issues Bearer token returned 
    # back to the client/frontend) -> frontend should save that token as a cookie, or session or whatever -> fronted will use the token
    # to make ant authorized API call such asthe /respond. Bearer token 

    # token: should contain user info such as user_id

    # http_request: Request
    # http_request.headers.get("authorization") -> returns the token that contains user_id info. 

    # DROP ExecuteRequest

    # validate user exists
    user = users_collection.find_one({"user_id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail=f"User '{user_id}' not found")

    # initialize agent and context
    agent = Agent()
    result_context = [{"role": "user", "content": message}]

    # get planning response from AI
    # 2a️⃣ Decide between chat vs action
    try:
        intent_payload = agent.process_request(
            message=message,
            user_id=user_id,
            context=result_context,
            mode="classify",
        )
    except Exception:
        intent_payload = {}

    if intent_payload.get("intent") == "chat":
        chat_reply = agent.process_request(
            message=message,
            user_id=user_id,
            context=result_context,
            mode="chat",
        )
        return {
            "status": "completed",
            "results": [],
            "summary": chat_reply.get("message", ""),
        }

    # 3️⃣ Get planning response from AI
    try:
        plan_response = agent.process_request(
            message=message,
            user_id=user_id,
            context=result_context,
            mode="plan"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent planning failed: {str(e)}")

    # validate plans
    plans = plan_response.get("plans", [])
    if not isinstance(plans, list):
        raise HTTPException(status_code=500, detail="Agent returned invalid 'plans' format")

    results = []

    # TODO: need confirmation for take action chat response
    # if plan mode gives back a list of actions, we should ask the user first? 
    
    for plan in plans:
        # validate each plan
        if not isinstance(plan, dict):
            results.append({"plan": plan, "error": "Plan is not a dictionary"})
            continue

        fn = plan.get("function_name")
        args = plan.get("arguments", {})

        if not fn:
            results.append({"plan": plan, "error": "Missing function_name"})
            continue

        if not isinstance(args, dict):
            results.append({"plan": plan, "error": "Arguments must be a dictionary"})
            continue

        # execute tool safely
        try:
            res = execute_tool(plan, user_id=user_id)
            results.append({"plan": plan, "result": res})
            # Add tool output to context as assistant text (no tool_calls in this flow)
            result_context.append({"role": "assistant", "content": {"tool_result": res}})
        except Exception as e:
            results.append({"plan": plan, "error": str(e)})

    # final summary from AI
    try:
        final_summary = agent.process_request(
            message="Summarize actions taken",
            user_id=user_id,
            context=result_context,
            mode="summarize"
        )
        summary_text = final_summary.get("message", "")
    except Exception as e:
        summary_text = f"Summary generation failed: {str(e)}"

    return {
        "status": "completed",
        "results": results,
        "summary": summary_text
    }