from pydantic import BaseModel

class CategoryResponse(BaseModel):
    primary: str
    secondary: str