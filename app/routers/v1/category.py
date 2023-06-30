import json
import re
import sys
import warnings

import openai
import pandas as pd
import spacy
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from config.limiter import lim
from data.constants import DELIMITER, OPENAI_API_KEY, TICKET_CLASSIFICATION_PROMPT
from models.Ticket import Ticket
from models.UserMessage import UserMessage
from models.CategoryResponse import CategoryResponse

sys.path.append("..")
warnings.filterwarnings("ignore")

category_router = APIRouter()

nlp = spacy.load("pt_core_news_sm")

# Sharepoint
words_model_sp = pd.read_csv(
    "data/words_model_sp.csv",
    sep=",",
    encoding="utf-8",
    usecols=["unigram", "weight", "category"],
)

categories_sp = list(words_model_sp["category"].value_counts().index)

# GLPI
words_model_glpi = pd.read_csv(
    "data/words_model_glpi.csv",
    sep=",",
    encoding="utf-8",
    usecols=["unigram", "weight", "category"],
)

categories_glpi = list(words_model_glpi["category"].value_counts().index)

# Category AI
openai.api_key = OPENAI_API_KEY
system_prompt = TICKET_CLASSIFICATION_PROMPT
delimiter = DELIMITER


def get_category_ai(messages, model="gpt-3.5-turbo", temperature=0, max_tokens=1000):
    """
    Get the category of a ticket using OpenAI's GPT-3 model.
    Args:
        messages (list): List of messages to send to the GPT-3 model.
        model (str): Name of the GPT-3 model to use. Defaults to "gpt-3.5-turbo".
        temperature (float): Sampling temperature to use when generating responses. Defaults to 0.
        max_tokens (int): Maximum number of tokens to generate in the response. Defaults to 500.
    Returns:
        dict: Primary and secondary categories of the ticket as predicted by the GPT-3 model.
    """
    response = openai.ChatCompletion.create(
        model=model, messages=messages, temperature=temperature, max_tokens=max_tokens
    )
    return response.choices[0].message["content"]


def find_keyword(keyword, word, weight) -> int:
    """Find keyword in text.
    Args:
        keyword (str): Keyword to be found.
        word (str): Word to be compared.
        weight (int): Weight of the keyword.
    Returns:
        int: Weight of the keyword if found, 0 otherwise.
    """
    return int(weight) if keyword == word else 0


def clean_text(text) -> str:
    """Clean text.
    Args:
        text (str): Text to be cleaned.
    Returns:
        str: Cleaned text.
    """
    text = text.lower()
    pattern = r"[^\w\s]"
    text = re.sub(pattern, "", text)
    pattern = r"\w*\d\w*"
    text = re.sub(pattern, "", text)
    return text


def lemmatize_text(text) -> str:
    """Lemmatize text.
    Args:
        text (str): Text to be lemmatized.
    Returns:
        str: Lemmatized text.
    """
    sent = []
    doc = nlp(text)
    for token in doc:
        sent.append(token.lemma_)
    return " ".join(sent)


@category_router.post(
    "/v1/sharepoint/category", tags=["IT Tickets"], response_model=CategoryResponse
)
@lim.limit("600/minute")
async def sharepoint_category(ticket: Ticket, request: Request) -> str:
    """Categorize Sharepoint tickets.
    Args:
        ticket (Ticket): Ticket to be categorized.
    Returns:
        str: Category of the ticket.
    """
    try:
        text = lemmatize_text(
            clean_text(ticket.title + " " + ticket.description)
        ).split()
        scores = [
            {
                "category": cat,
                "score": sum(
                    find_keyword(row["unigram"], w, row["weight"])
                    for w in text
                    for _, row in words_model_sp[
                        words_model_sp["category"] == cat
                    ].iterrows()
                ),
            }
            for cat in categories_sp
        ]
        max_score = max(scores, key=lambda x: x["score"])
        return max_score["category"] if max_score["score"] > 0 else "Others..."
    except Exception as e:
        return str(e)


@category_router.post("/v1/glpi/category", tags=["IT Tickets"])
@lim.limit("600/minute")
async def glpi_category(ticket: Ticket, request: Request) -> str:
    """Categorize GLPI tickets.
    Args:
        ticket (Ticket): Ticket to be categorized.
    Returns:
        str: Category of the ticket.
    """
    try:
        text = lemmatize_text(
            clean_text(ticket.title + " " + ticket.description)
        ).split()
        scores = [
            {
                "category": cat,
                "score": sum(
                    find_keyword(row["unigram"], w, row["weight"])
                    for w in text
                    for _, row in words_model_glpi[
                        words_model_glpi["category"] == cat
                    ].iterrows()
                ),
            }
            for cat in categories_glpi
        ]
        max_score = max(scores, key=lambda x: x["score"])
        return max_score["category"] if max_score["score"] > 0 else "Others..."
    except Exception as e:
        return str(e)


@category_router.post(
    "/v1/tickets/category", tags=["IT Tickets"], response_model=CategoryResponse
)
@lim.limit("60/minute")
async def tickets_category(user_message: UserMessage, request: Request):
    """Categorize tickets.
    Args:
        user_message (UserMessage): Description of the ticket.
    Returns:
        json: Primary and secondary categories of the ticket.
    """
    try:
        messages = [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": f"{delimiter}{user_message.message}{delimiter}",
            },
        ]
        response = get_category_ai(messages)
        response = json.loads(response)
        return response
    except Exception as e:
        return {"error": str(e)}
