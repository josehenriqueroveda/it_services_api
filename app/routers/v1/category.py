import pandas as pd
import re
import spacy
from fastapi import APIRouter, Request
from config.limiter import lim
from models.Ticket import Ticket
import sys
import warnings

sys.path.append("..")
warnings.filterwarnings("ignore")

nlp = spacy.load("pt_core_news_sm")

category_router = APIRouter()

# Sharepoint
words_model_sp = pd.read_csv(
    "data/words_model.csv",
    sep=",",
    encoding="utf-8",
    usecols=["unigram", "weight", "category"],
)

categories_sp = list(words_model_sp["category"].value_counts().index)

# GLPI
words_model_glpi = pd.read_csv(
    "data/words_model.csv",
    sep=",",
    encoding="utf-8",
    usecols=["unigram", "weight", "category"],
)

categories_glpi = list(words_model_glpi["category"].value_counts().index)


def _find_keyword(keyword, word, weight):
    """Find keyword in text.
    Args:
        keyword (str): Keyword to be found.
        word (str): Word to be compared.
        weight (int): Weight of the keyword.
        Returns:
            int: Weight of the keyword if found, 0 otherwise.
    """
    return int(weight) if keyword == word else 0


def _clean_text(text):
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


def _lemmatize_text(text):
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


@category_router.post("/v1/sharepoint/category", tags=["IT Tickets"])
@lim.limit("600/minute")
async def sharepoint_category(t: Ticket, request: Request) -> str:
    """Categorize Sharepoint tickets.
    Args:
        t (Ticket): Ticket to be categorized.
        Returns:
            str: Category of the ticket.
    """
    try:
        scores = []
        text = t.title + " " + t.description
        text = _clean_text(text)
        text = _lemmatize_text(text)
        text = text.split()
        for cat in categories_sp:
            score = 0
            temp = words_model_sp[words_model_sp["category"] == cat]
            for _, row in temp.iterrows():
                for w in text:
                    score += _find_keyword(row["unigram"], w, row["weight"])
            scores.append({"category": cat, "score": score})
        max_score = max(scores, key=lambda x: x["score"])
        return max_score["category"] if max_score["score"] > 0 else "Others..."
    except Exception as e:
        return str(e)


@category_router.post("/v1/glpi/category", tags=["IT Tickets"])
@lim.limit("600/minute")
async def glpi_category(t: Ticket, request: Request) -> str:
    """Categorize GLPI tickets.
    Args:
        t (Ticket): Ticket to be categorized.
        Returns:
            str: Category of the ticket.
    """
    try:
        scores = []
        text = t.title + " " + t.description
        text = _clean_text(text)
        text = _lemmatize_text(text)
        text = text.split()
        for cat in categories_glpi:
            score = 0
            temp = words_model_glpi[words_model_glpi["category"] == cat]
            for _, row in temp.iterrows():
                for w in text:
                    score += _find_keyword(row["unigram"], w, row["weight"])
            scores.append({"category": cat, "score": score})
        max_score = max(scores, key=lambda x: x["score"])
        return max_score["category"] if max_score["score"] > 0 else "Others..."
    except Exception as e:
        return str(e)
