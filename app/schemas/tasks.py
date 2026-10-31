from pydantic import BaseModel
class TaskCreate(BaseModel):
    task_id: str
    status: str

class TaskAccepted(BaseModel):
    task_id: str
    status: str