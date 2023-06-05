import pandas as pd
import os
from uvicorn import run
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from config.limiter import lim
from routers.category import category_router

limiter = lim

app = FastAPI(title="Tickets NLP API",
              description="""Natural Language Processing applied to categorize IT support tickets.
              <p><strong>Developer</strong>: Jose Henrique Roveda<br/>""",
              version="1.0.0")


app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

origins = ["*"]
methods = ["*"]
headers = ["*"]


app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=methods,
    allow_headers=headers
)


app.include_router(router=category_router)

@app.get("/", response_class=HTMLResponse, tags=["Info"])
@lim.limit("60/minute")
async def info(request: Request):
    return """
    <h2><span style="color: #339966;">Ticket Classification API</span></h2>
    <p style="font-size: 1.5em;">API developed for IT services.</p>
    <p style="font-size: 1.5em;">Access the <a href="http://0.0.0.0:8000/docs">Docs Page</a> to read the documentation.</p>
    <p><strong>Developer</strong>: Jose Henrique Roveda<br/><strong>Version</strong>: 1.0.1</p>"""


if __name__ == "__main__":
    port = int(os.environ.get('PORT', 8000))
    run(app, host="0.0.0.0", port=port)
    # uvicorn main:app --reload