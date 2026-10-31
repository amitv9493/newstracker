from pydantic import BaseModel, Field, field_validator


class TaskCreate(BaseModel):
    message: str = Field(min_length=1, max_length=10_000)

    @field_validator("message")
    @classmethod
    def message_must_not_be_blank(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("must not be blank")
        return stripped


class TaskAccepted(BaseModel):
    task_id: str
    status: str
