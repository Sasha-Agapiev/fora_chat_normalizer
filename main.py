#########################################################################################
#  Fora Take-Home Project: "Normalize" Chatbot API
#  main.py: FastAPI Application for Routing API Requests
#########################################################################################

# Import key libraries
from fastapi import FastAPI, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import logging
import time
import uuid
from datetime import datetime, timezone
from dotenv import load_dotenv

# Import our custom modules
from services.classification_service import ClassificationService
from services.entity_service import EntityService
from services.contact_service import ContactService
from services.enrichment_service import EnrichmentService
from models.schemas import MessageInput, MessageOutput, HealthResponse

# Load application .env 
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Fora Travel ChatBot Normalize API",
    description="AI-powered message classification and enrichment for client/advisor communications",
    version="1.0.0"
)

# Initialize services
classification_service = ClassificationService()
entity_service = EntityService()
contact_service = ContactService()
enrichment_service = EnrichmentService()

@app.get("/health", response_model=HealthResponse)
def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now(timezone.utc),
        version="1.0.0",
    )

@app.post("/normalize", response_model=MessageOutput)
def normalize_message(message: MessageInput):
    """
    Normalize a customer support message by:
    1. Classifying urgency/risk level
    2. Extracting contact information and entities
    3. Adding contextual enrichments
    """
    try:
        logger.info(f"Processing message {message.message_id}")
        
        # Step 1: Classify the message
        classification_result = classification_service.classify_message(message.text)
        
        # Step 2: Extract contact information
        contact_info = contact_service.extract_contact(message.text)
        
        # Step 3: Extract entities (cities, hotels, restaurants)
        entities = entity_service.extract_entities(message.text)
        
        # Step 4: Generate enrichments
        enrichments = enrichment_service.generate_enrichments(
            message.text, entities, classification_result.category
        )
        
        # Construct response
        response = MessageOutput(
            message_id=message.message_id,
            category=classification_result.category,
            contact=contact_info,
            entities=entities,
            enrichment=enrichments
        )
        
        logger.info(f"Successfully processed message {message.message_id}")
        return response
        
    except Exception as e:
        logger.error(f"Error processing message {message.message_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
def root():
    """Root endpoint with API information"""
    return {
        "message": "Fora Travel Message Normalizer API",
        "version": "1.0.0"
    }

def simple_test(test_input, test_id="test_01"):
    test_message = MessageInput(
        message_id=test_id,
        text=test_input
    )
    response = normalize_message(test_message)
    print(response)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)


    # simple_test("client lost passport in Mexico City, need help now")
