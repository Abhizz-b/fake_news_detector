from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import uvicorn
import os
import sys
from datetime import datetime
import json
import asyncio

# Import your FactChecker class
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from fact_checker import FactChecker

# Create FastAPI app
app = FastAPI(
    title="AI Fake News Detection API",
    description="REST API providing fake news detection services",
    version="2.0.0",
)

# Configure CORS, allow requests from Chrome extension
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Should be restricted to your extension ID in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request model
class FactCheckRequest(BaseModel):
    text: str
    api_base: Optional[str] = "http://localhost:8000/v1"
    model: Optional[str] = "jan-v1-4b"
    temperature: Optional[float] = 0.0
    max_tokens: Optional[int] = 1000


# Response model
class FactCheckResponse(BaseModel):
    claim: str
    verdict: str
    reasoning: str
    evidence: List[Dict[str, Any]]
    timestamp: str


# Active task cache
active_tasks = {}


@app.post("/check", response_model=FactCheckResponse)
async def check_fact(request: FactCheckRequest, background_tasks: BackgroundTasks):
    """
    Check the accuracy of a piece of news text
    """
    try:
        # Initialize FactChecker
        fact_checker = FactChecker(
            request.api_base, request.model, request.temperature, request.max_tokens
        )

        # Extract claim
        claim = fact_checker.extract_claim(request.text)
        # Process claim string, extract content after "claim:"
        if "claim:" in claim.lower():
            claim = claim.split("claim:")[-1].strip()

        # Search for evidence
        evidence_docs = fact_checker.search_evidence(claim)

        # Get relevant evidence chunks
        evidence_chunks = fact_checker.get_evidence_chunks(evidence_docs, claim)

        # Evaluate the claim
        evaluation = fact_checker.evaluate_claim(claim, evidence_chunks)

        # Build response
        response = {
            "claim": claim,
            "verdict": evaluation["verdict"],
            "reasoning": evaluation["reasoning"],
            "evidence": evidence_chunks,
            "timestamp": datetime.now().isoformat(),
        }

        return response

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error during fact-checking: {str(e)}")


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


# Entry point for running the server (used for development)
if __name__ == "__main__":
    uvicorn.run("api:app", host="0.0.0.0", port=8080, reload=True)