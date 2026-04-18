from typing import Annotated
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI()

# initializes middleware to allow requests into endpoints
def initialize():
    # Probably initialize all routes + handlers in here
    # Will also need function for posting requests
    pass

@app.get("/test")
def test():
    return {"message": "test message"}

@app.get("/some_endpoint")
def some_logic():
    payload = {}
    # do some logic
    return payload


# tests all routing/related functionality 
def testing():
    pass


# This is the entry point for the code/application
if __name__ == "__main__":
    initialize()