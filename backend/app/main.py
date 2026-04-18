from typing import Annotated
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
from pytrends.request import TrendReq
import requests

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/fda-substances")
def get_fda_substances():
    url = "https://www.hfpappexternal.fda.gov/scripts/fdcc/index.cfm?set=FoodSubstances"
    response = requests.get(url)
    if response.status_code == 200:
        # Parse the HTML for tables
        tables = pd.read_html(response.text)
        if tables:
            # Assume the first table contains the substances
            df = tables[0]
            # Assuming the table has a column with substance names, e.g., 'Substance'
            substances = df.get('Substance', df.iloc[:, 0]).tolist()
            return {"substances": substances}
        else:
            return {"error": "No tables found on the page"}
    else:
        return {"error": f"Failed to fetch data, status code: {response.status_code}"}
