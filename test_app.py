from fastapi import FastAPI
from fastapi.testclient import TestClient
from backend.app import app

client = TestClient(app)
response = client.get("/")
print("Response Root:", response.status_code, response.text)
response2 = client.get("/health")
print("Response Health:", response2.status_code, response2.text)
