import logging
from typing import List
from contextlib import contextmanager

import pandas as pd
from fastapi import APIRouter, Request
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from config.limiter import lim
from data.constants import (
    DESTINIATION_PATH,
    GROUPS_QUERY,
    MSSQL_CONN,
    PBI_GROUPS_QUERY,
    USERS_QUERY,
)
from models.Access import Access
from models.User import User
from models.Group import Group


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

adgroups_router = APIRouter()
engine = create_engine(MSSQL_CONN)
Session = sessionmaker(bind=engine)


@contextmanager
def open_file(file_path: str, mode: str):
    """Open a file.
    Args:
        file_path (str): Path to the file.
        mode (str): Mode to open the file.
    Yields:
        file: File object.
    """
    try:
        file = open(file_path, mode)
        yield file
    finally:
        file.close()


@adgroups_router.post("/v1/groups/users", tags=["AD Groups"])
@lim.limit("600/minute")
async def update_groups(accesses: List[Access], request: Request):
    """Update AD Groups.
    Args:
        accesses (List[Access]): List of accesses.
    Returns:
        dict: Response status message.
    """
    try:
        with open_file(DESTINIATION_PATH, "w") as f:
            body = [
                {"email": item.email, "group": item.group, "action": item.action}
                for item in accesses
                if item.email and item.group and item.action
            ]
            df = pd.DataFrame(body, columns=["email", "group", "action"])
            df.dropna(inplace=True)
            df.to_csv(f, sep=";", index=False)
        return {"message": "Groups updated successfully."}
    except Exception as e:
        logger.error(f"Error updating groups: {e}")
        return {"message": f"Error updating groups: {e}"}


@adgroups_router.get("/v1/groups/users", tags=["AD Groups"], response_model=List[User])
@lim.limit("60/minute")
async def get_users(request: Request):
    """Get all users from AD.
    Returns:
        List[User]: Email and names of the users.
    """
    try:
        query = text(USERS_QUERY)
        with Session() as session:
            result = session.execute(query)
            users = [
                {"email": email, "name": name} for email, name in result.fetchall()
            ]
        return users
    except Exception as e:
        return {"message": f"Error: {e}"}


@adgroups_router.get(
    "/v1/groups/groups", tags=["AD Groups"], response_model=List[Group]
)
@lim.limit("60/minute")
async def get_groups(request: Request):
    """Get all groups from AD.
    Returns:
        List[Group]: Names of the groups.
    """
    try:
        query = text(GROUPS_QUERY)
        with Session() as session:
            result = session.execute(query)
            group_names = [{"group": group[0]} for group in result.fetchall()]
        return group_names
    except Exception as e:
        logger.error(f"Error getting groups: {e}")
        return {"message": "Error getting groups."}


@adgroups_router.get(
    "/v1/groups/pbi-groups", tags=["AD Groups"], response_model=List[Group]
)
@lim.limit("60/minute")
async def get_pbi_groups(request: Request):
    """Get PowerBI groups from AD.
    Returns:
        List[Group]: Names of the PowerBI groups.
    """
    try:
        query = text(PBI_GROUPS_QUERY)
        with Session() as session:
            result = session.execute(query)
            group_names = [{"group": group[0]} for group in result.fetchall()]
        return group_names
    except Exception as e:
        logger.error(f"Error getting groups: {e}")
        return {"message": "Error getting PowerBI groups."}
