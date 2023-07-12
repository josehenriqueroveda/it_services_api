import json
import re
import sys
import warnings

import pandas as pd
import spacy
from fastapi import APIRouter, Request, Response

from config.limiter import lim
from models.Ticket import Ticket
from models.TicketClassifier import TicketClassifier
from models.UserMessage import UserMessage

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


# Helper functions
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


# API routes
@category_router.post(
    "/v1/sharepoint/category", tags=["IT Tickets"])
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
    "/v1/ai/tickets/category", tags=["IT Tickets"])
@lim.limit("60/minute")
async def tickets_category(user_message: UserMessage, request: Request):
    """Categorize tickets.
    Args:
        user_message (UserMessage): Description of the ticket.F
    Returns:
        json: Category of the ticket.
    """
    try:
        ticket_classifier = TicketClassifier()
        response = ticket_classifier.classify_ticket(user_message.message)
        if response:
            return json.loads(response)
        else:
            return Response(
                content=json.dumps({"error": "No category found."}),
                media_type="application/json",
            )
    except Exception as e:
        return Response(content=json.dumps({"error": str(e)}), media_type="application/json")
