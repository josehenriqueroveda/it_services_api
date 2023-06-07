import pandas as pd
from fastapi import APIRouter, Request
from config.limiter import lim
from data.constants import DESTINIATION_PATH
from typing import List
from models.Access import Access
import warnings

warnings.filterwarnings("ignore")

adgroups_router = APIRouter()


@adgroups_router.post("/v1/groups/users", tags=["AD Groups"])
@lim.limit("600/minute")
async def update_groups(request: Request, accesses: List[Access]):
    """Update AD Groups.
    Args:
        accesses (List[Access]): List of accesses.
    Returns:
        dict: Response status message.
    """
    try:
        csv_path = DESTINIATION_PATH
        body = [{"email": item.email, "group": item.group, "action": item.action} for item in accesses if item.email and item.group]
        df = pd.DataFrame(body, columns=["email", "group", "action"])
        df.to_csv(csv_path, sep=';', index=False)
        return {"message": "Groups updated successfully!"}
    except Exception as e:
        return {"message": f"Error: {e}"}
