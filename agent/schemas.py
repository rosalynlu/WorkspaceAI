from pydantic import BaseModel

class ExecuteRequest(BaseModel):
    message: str