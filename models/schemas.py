#########################################################################################
#  Fora Take-Home Project: "Normalize" Chatbot API
#  schemas.py: Defining classes for data validation (API inputs and outputs)
#########################################################################################


from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Literal
from datetime import datetime
from enum import Enum

class MessageCategory(str, Enum):
    HIGH_RISK = "high_risk"
    URGENT = "urgent"
    BASE = "base"

class EntityType(str, Enum):
    CITY = "city"
    HOTEL = "hotel"
    RESTAURANT = "restaurant"

class MessageInput(BaseModel):
    message_id: str = Field(..., description="Unique identifier for the message")
    text: str = Field(..., min_length=1, max_length=5000, description="The message text to normalize")
    
    def validate_text(cls, v):
        if not v.strip():
            raise ValueError('Text cannot be empty or whitespace only')
        return v.strip()

class ContactInfo(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    zip: Optional[str] = None

class Entity(BaseModel):
    type: EntityType = Field(..., description="Type of entity (city, hotel, restaurant)")
    value: str = Field(..., description="The extracted entity value")

class ClassificationResult(BaseModel):
    category: MessageCategory
    confidence: float = Field(..., ge=0.0, le=1.0)
    reasoning: Optional[str] = None

class MessageOutput(BaseModel):
    message_id: str
    category: MessageCategory
    contact: Optional[ContactInfo] = None
    entities: Optional[List[Entity]] = None
    enrichment: Optional[Dict[str, Any]] = None

class HealthResponse(BaseModel):
    status: str
    timestamp: datetime
    version: str
