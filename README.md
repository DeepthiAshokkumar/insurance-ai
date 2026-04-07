# Motor Insurance Claim AI System

This project is an AI-based application that processes motor insurance claim documents using the Gemini API. It provides an interface to upload data, send it to a FastAPI backend, and return AI-generated responses.

## Setup

Install dependencies:
pip install -r requirements.txt

Create a `.env` file:
GEMINI_API_KEY=your_api_key

Run the application:
uvicorn backend.main:app --reload
