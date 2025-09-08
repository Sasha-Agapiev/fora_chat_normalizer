#########################################################################################
#  Fora Take-Home Project: "Normalize" Chatbot API
#  entity_serivce.py: Service for extracting restaurant, hotel, city entities from 
#                     the client message. Made using an OpenAI API call, with fallback
#                     to SpaCy NER logic in case of invalid LLM output.
#########################################################################################


import re
import logging
from typing import List, Dict, Set
from models.schemas import Entity, EntityType
import spacy
import json
import openai
import os

logger = logging.getLogger(__name__)

class EntityService:
    def __init__(self):
        # Load spaCy model - using small model for speed
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            logger.warning("spaCy model not found. Install with: python -m spacy download en_core_web_sm")
            self.nlp = None
        
        # Major cities commonly mentioned in travel
        self.cities = {
            'paris', 'london', 'tokyo', 'new york', 'nyc', 'new york city', 'rome', 'barcelona',
            'amsterdam', 'berlin', 'madrid', 'vienna', 'prague', 'budapest', 'lisbon',
            'florence', 'venice', 'milan', 'naples', 'athens', 'istanbul', 'dublin',
            'edinburgh', 'copenhagen', 'stockholm', 'oslo', 'helsinki', 'reykjavik',
            'zurich', 'geneva', 'munich', 'hamburg', 'cologne', 'frankfurt', 'brussels',
            'antwerp', 'porto', 'seville', 'valencia', 'bilbao', 'nice', 'lyon',
            'marseille', 'bordeaux', 'strasbourg', 'bologna', 'palermo',
            'catania', 'bari', 'split', 'dubrovnik', 'zagreb', 'ljubljana',
            'bratislava', 'krakow', 'warsaw', 'gdansk', 'tallinn', 'riga', 'vilnius'
        }
        
        # Hotel name patterns - improved for "Chapter Roma" style names
        self.hotel_patterns = [
            # Major hotel chains
            r'\b(marriott|hilton|hyatt|sheraton|westin|ritz[-\s]?carlton|four\s+seasons)\b',
            r'\b(intercontinental|crowne\s+plaza|holiday\s+inn|hampton\s+inn)\b',
            r'\b(doubletree|embassy\s+suites|homewood\s+suites|residence\s+inn)\b',
            r'\b(fairmont|sofitel|novotel|mercure|ibis|accor)\b',
            r'\b(radisson|ramada|wyndham|best\s+western|comfort\s+inn)\b',
            # Boutique/branded hotel patterns - catches "Chapter Roma"
            r'\b(chapter|w|edition|aloft|moxy|citizen|kimpton)\s+[A-Z][a-z]+\b',
            r'\b[A-Z][a-z]+\s+(hotel|resort|inn|lodge|suites?)\b',
            r'\b(hotel|resort|inn)\s+[A-Z][a-z]+\b',
            # Generic hotel terms with modifiers
            r'\b(grand|luxury|boutique|historic|palace|royal)\s+(hotel|resort)\b',
            r'\b(hotel|resort|inn|lodge|suites?)\s+[\w\s]{1,30}\b'
        ]
        
        # Restaurant patterns
        self.restaurant_patterns = [
            # Restaurant chains
            r'\b(mcdonalds|mcdonald\'s|burger\s+king|kfc|subway|starbucks)\b',
            r'\b(pizza\s+hut|dominos|domino\'s|taco\s+bell|olive\s+garden)\b',
            # Generic restaurant terms
            r'\b(restaurant|cafe|bistro|brasserie|trattoria|pizzeria|taverna)\s+[\w\s]{1,30}\b',
            r'\b[\w\s]{1,30}\s+(restaurant|cafe|bistro|brasserie|trattoria|pizzeria)\b',
            # Cuisine types as restaurant indicators
            r'\b(italian|french|chinese|japanese|thai|indian|mexican|greek)\s+(restaurant|cuisine|food)\b'
        ]

    def extract_entities(self, text: str) -> List[Entity]:
        """Extract cities, hotels, and restaurants using OpenAI + spaCy fallback"""
        try:
            entities = []
            
            # Try OpenAI first for better accuracy
            openai_entities = self._extract_entities_with_openai(text)
            if openai_entities:
                entities = openai_entities
                logger.info(f"OpenAI extracted {len(entities)} entities: {[f'{e.type.value}:{e.value}' for e in entities]}")
            else:
                # Fallback to spaCy + patterns if OpenAI fails
                logger.warning("OpenAI entity extraction failed, using spaCy fallback")
                entities = self._extract_entities_with_spacy(text)
                logger.info(f"spaCy extracted {len(entities)} entities: {[f'{e.type.value}:{e.value}' for e in entities]}")
            
            # Remove duplicates while preserving order
            unique_entities = []
            seen = set()
            for entity in entities:
                entity_key = (entity.type, entity.value.lower())
                if entity_key not in seen:
                    unique_entities.append(entity)
                    seen.add(entity_key)
            
            return unique_entities
            
        except Exception as e:
            logger.error(f"Entity extraction failed: {str(e)}")
            return []

    def _extract_entities_with_openai(self, text: str) -> List[Entity]:
        """Extract entities using OpenAI with structured output"""
        try:
            client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            
            system_prompt = """You are an expert at extracting travel-related entities from text.
            Extract cities, hotels, and restaurants mentioned in the message.
            
            Return ONLY valid JSON in this exact format:
            {
              "entities": [
                {"type": "city", "value": "Paris"},
                {"type": "hotel", "value": "Ritz Carlton"},
                {"type": "restaurant", "value": "Le Jules Verne"}
              ]
            }

            For example, given the input: "Booked Aman Venice for our honeymoon"
            Return: 
            {
              "entities": [
                {"type": "hotel", "value": "Aman Venice"},
                {"type": "city", "value": "Venice"}
              ]
            }

            For example, given the input: "booked the marriot marquis in NYC"
            Return:
            {
              "entities": [
                {"type": "hotel", "value": "Marriot Marquis"},
                {"type": "city", "value": "NYC"}
              ]
            }

            Important Rules:
            - ONLY extract entities that are clearly mentioned
            - ONLY extract entities with type "city", "hotel", or "restaurant"
            - ONLY include valid extracted entities in your JSON response
            - Use valid JSON formatting for your response
            - Use proper capitalization
            - Include "The" in hotel names if present
            - If there is overlap between types, make sure to list each type/value explicitly
            """
            
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Extract entities from: {text}"}
                ],
                temperature=0.0,
                max_tokens=300,
                timeout=10.0
            )
            
            result_text = response.choices[0].message.content.strip()
            result = json.loads(result_text)
            
            entities = []
            for entity_data in result.get("entities", []):
                entity_type = EntityType(entity_data["type"])
                entity_value = entity_data["value"]
                entities.append(Entity(type=entity_type, value=entity_value))
            
            return entities
            
        except Exception as e:
            logger.error(f"OpenAI entity extraction failed: {str(e)}")
            return []

    def _extract_entities_with_spacy(self, text: str) -> List[Entity]:
        """Fallback spaCy + pattern extraction (existing implementation)"""
        entities = []
        
        # Extract cities using spaCy + manual patterns
        cities_found = self._extract_cities_with_spacy(text)
        entities.extend([Entity(type=EntityType.CITY, value=city) for city in cities_found])
        
        # Extract hotels using spaCy + patterns
        hotels_found = self._extract_hotels_with_spacy(text)
        entities.extend([Entity(type=EntityType.HOTEL, value=hotel) for hotel in hotels_found])
        
        # Extract restaurants using spaCy + patterns
        restaurants_found = self._extract_restaurants_with_spacy(text)
        entities.extend([Entity(type=EntityType.RESTAURANT, value=restaurant) for restaurant in restaurants_found])
        
        return entities

    def _extract_cities_with_spacy(self, text: str) -> List[str]:
        """Extract cities using spaCy NER + manual patterns"""
        found_cities = set()
        
        # Use spaCy NER if available
        if self.nlp:
            doc = self.nlp(text)
            for ent in doc.ents:
                if ent.label_ in ["GPE", "LOC"]:  # Geopolitical entity or location
                    city_name = ent.text.strip()
                    if len(city_name) > 2:  # Filter out very short matches
                        found_cities.add(self._capitalize_city_name(city_name))
        
        # Also check against our known cities list
        text_lower = text.lower()
        for city in self.cities:
            if city in text_lower:
                found_cities.add(self._capitalize_city_name(city))
        
        return list(found_cities)

    def _extract_hotels_with_spacy(self, text: str) -> List[str]:
        """Extract hotels using spaCy NER + pattern matching"""
        found_hotels = set()
        
        # Use spaCy NER to find organizations/facilities
        if self.nlp:
            doc = self.nlp(text)
            for ent in doc.ents:
                if ent.label_ in ["ORG", "FAC"]:  # Organization or facility
                    entity_text = ent.text.strip()
                    # Check if it looks like a hotel name
                    if self._looks_like_hotel(entity_text):
                        found_hotels.add(self._clean_entity_name(entity_text))
        
        # Use pattern matching as backup
        for pattern in self.hotel_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                hotel_name = match.group().strip()
                cleaned_name = self._clean_entity_name(hotel_name)
                if len(cleaned_name) > 3:
                    found_hotels.add(cleaned_name)
        
        return list(found_hotels)

    def _extract_restaurants_with_spacy(self, text: str) -> List[str]:
        """Extract restaurants using spaCy NER + pattern matching"""
        found_restaurants = set()
        
        # Use spaCy NER to find organizations
        if self.nlp:
            doc = self.nlp(text)
            for ent in doc.ents:
                if ent.label_ == "ORG":
                    entity_text = ent.text.strip()
                    # Check if it looks like a restaurant name
                    if self._looks_like_restaurant(entity_text):
                        found_restaurants.add(self._clean_entity_name(entity_text))
        
        # Use pattern matching as backup
        for pattern in self.restaurant_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                restaurant_name = match.group().strip()
                cleaned_name = self._clean_entity_name(restaurant_name)
                if len(cleaned_name) > 3:
                    found_restaurants.add(cleaned_name)
        
        return list(found_restaurants)

    def _looks_like_hotel(self, text: str) -> bool:
        """Heuristic to determine if an entity looks like a hotel"""
        text_lower = text.lower()
        hotel_indicators = [
            'hotel', 'resort', 'inn', 'lodge', 'suites', 'chapter', 'w hotel',
            'marriott', 'hilton', 'hyatt', 'sheraton', 'westin', 'ritz',
            'four seasons', 'intercontinental', 'crowne plaza', 'holiday inn'
        ]
        return any(indicator in text_lower for indicator in hotel_indicators)

    def _looks_like_restaurant(self, text: str) -> bool:
        """Heuristic to determine if an entity looks like a restaurant"""
        text_lower = text.lower()
        restaurant_indicators = [
            'restaurant', 'cafe', 'bistro', 'brasserie', 'trattoria', 'pizzeria',
            'taverna', 'mcdonald', 'burger king', 'kfc', 'subway', 'starbucks',
            'pizza hut', 'domino', 'taco bell', 'olive garden'
        ]
        return any(indicator in text_lower for indicator in restaurant_indicators)

    def _capitalize_city_name(self, city: str) -> str:
        """Properly capitalize city names"""
        special_cases = {
            'new york': 'New York',
            'new york city': 'New York City', 
            'nyc': 'NYC',
            'los angeles': 'Los Angeles',
            'san francisco': 'San Francisco'
        }
        
        city_lower = city.lower()
        if city_lower in special_cases:
            return special_cases[city_lower]
        
        return city.title()

    def _clean_entity_name(self, name: str) -> str:
        """Clean and properly format entity names"""
        # Remove extra whitespace
        name = ' '.join(name.split())
        
        # Capitalize properly
        name = name.title()
        
        # Handle special cases
        replacements = {
            'Mcdonald\'S': 'McDonald\'s',
            'Mcdonalds': 'McDonald\'s',
            'Domino\'S': 'Domino\'s',
            'Ritz-Carlton': 'Ritz-Carlton',
            'Four Seasons': 'Four Seasons',
            'Burger King': 'Burger King',
            'Pizza Hut': 'Pizza Hut',
            'Taco Bell': 'Taco Bell',
            'Olive Garden': 'Olive Garden'
        }
        
        for old, new in replacements.items():
            if old.lower() in name.lower():
                name = re.sub(re.escape(old), new, name, flags=re.IGNORECASE)
        
        return name
