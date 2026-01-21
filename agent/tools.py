def create_email(to: str, subject: str, body: str):
    return {
        "action": "create_email",
        "to": to,
        "subject": subject
    }

def create_doc(title: str, content: str):
    return {
        "action": "create_doc",
        "title": title
    }

def create_calendar_event(summary: str, time: str):
    return {
        "action": "create_calendar_event",
        "summary": summary,
        "time": time
    }

def execute_tool(plan: dict):
    function_name = plan["function_name"]
    arguments = plan["arguments"]

    if function_name == "create_email":
        return create_email(**arguments)
    elif function_name == "create_doc":
        return create_doc(**arguments)
    elif function_name == "create_calendar_event":
        return create_calendar_event(**arguments)
    else:
        raise ValueError(f"Unknown function: {function_name}")