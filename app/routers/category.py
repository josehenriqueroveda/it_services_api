import pandas as pd
import re
import spacy
from datetime import datetime
from fastapi import APIRouter, Request
from config.limiter import lim
from models.Ticket import Ticket
import sys
sys.path.append("..")
import warnings
warnings.filterwarnings('ignore')

nlp = spacy.load('pt_core_news_sm')

category_router = APIRouter()

words_model = pd.read_csv('data/words_model.csv',
                          sep=',', encoding='utf-8', usecols=['unigram', 'weight', 'category'])

categories = list(words_model['category'].value_counts().index)


def _find_keyword(keyword, word, weight):
    return int(weight) if keyword == word else 0


def _clean_text(text):
    text = text.lower()
    pattern = r'[^\w\s]'
    text = re.sub(pattern, '', text)
    pattern = r'\w*\d\w*'
    text = re.sub(pattern, '', text)
    return text


def _lemmatize_text(text):
    sent = []
    doc = nlp(text)
    for token in doc:
        sent.append(token.lemma_)
    return " ".join(sent)


@category_router.post("/category", tags=['IT Tickets'])
@lim.limit("600/minute")
async def ticket_category(t: Ticket, request: Request):
    try:
        scores = []
        text = t.title + ' ' + t.description
        text = _clean_text(text)
        text = _lemmatize_text(text)
        text = text.split()
        for cat in categories:
            score = 0
            temp = words_model[words_model['category'] == cat]
            for _, row in temp.iterrows():
                for w in text:
                    score += _find_keyword(row['unigram'], w, row['weight'])
            scores.append({'category': cat, 'score': score})
        max_score = max(scores, key=lambda x: x['score'])
        return max_score['category'] if max_score['score'] > 0 else 'Others...'
    except Exception as e:
        return str(e)
