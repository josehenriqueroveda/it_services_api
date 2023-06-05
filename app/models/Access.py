from pydantic import BaseModel


class Access(BaseModel):
    email: str
    group: str
    action: str