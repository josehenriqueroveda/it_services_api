import pandas as pd
from fastapi import APIRouter, Request
from config.limiter import lim
from data.constants import DESTINIATION_PATH, MSSQL_CONN, USERS_QUERY, GROUPS_QUERY, PBI_GROUPS_QUERY
from sqlalchemy import create_engine
from typing import List
from models.Access import Access
import warnings

warnings.filterwarnings("ignore")


adgroups_router = APIRouter()
engine = create_engine(MSSQL_CONN)


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
        body = [
            {"email": item.email, "group": item.group, "action": item.action}
            for item in accesses
            if item.email and item.group
        ]
        df = pd.DataFrame(body, columns=["email", "group", "action"])
        df.to_csv(csv_path, sep=";", index=False)
        return {"message": "Groups updated successfully!"}
    except Exception as e:
        return {"message": f"Error: {e}"}


@adgroups_router.get("/v1/groups/users", tags=["AD Groups"])
@lim.limit("60/minute")
async def get_users(request: Request):
    """Get all users from AD.
    Returns:
        dict: Email and names of the users.
    """
    try:
        query = USERS_QUERY
        df = pd.read_sql(query, engine)
        users = [
            {"email": email, "name": name}
            for email, name in zip(df["EMAIL"], df["USER_NAME"])
        ]
        return users
    except Exception as e:
        return {"message": f"Error: {e}"}


@adgroups_router.get("/v1/groups/groups", tags=["AD Groups"])
@lim.limit("60/minute")
async def get_groups(request: Request):
    """Get all groups from AD.
    Returns:
        dict: Names of the groups.
    """
    try:
        query = GROUPS_QUERY
        df = pd.read_sql(query, engine)
        group_names = [{"group": group_name} for group_name in df["GROUP_NAME"]]
        return group_names
    except Exception as e:
        return {"message": f"Error: {e}"}


@adgroups_router.get("/v1/groups/pbi-groups", tags=["AD Groups"])
@lim.limit("60/minute")
async def get_pbi_groups(request: Request):
    """Get PowerBI groups from AD.
    Returns:
        list: Names of the PowerBI groups.
    """
    try:
        query = PBI_GROUPS_QUERY
        df = pd.read_sql(query, engine)
        return df["GROUP_NAME"].tolist()
    except Exception as e:
        return {"message": f"Error: {e}"}
