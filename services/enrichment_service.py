import logging
import requests
import re
import os 
import openai
import json
from typing import List, Dict, Any, Optional
from models.schemas import Entity, MessageCategory

logger = logging.getLogger(__name__)

class EnrichmentService:
    def __init__(self):
        # Cache for emergency numbers to avoid repeated API calls
        self.emergency_cache = {}
        
        # Country mappings for common cities
        self.city_to_country = {
            'madrid': 'ES', 'berlin': 'DE', 'amsterdam': 'NL', 'vienna': 'AT', 'prague': 'CZ',
            'budapest': 'HU', 'barcelona': 'ES', 'lisbon': 'PT', 'dublin': 'IE',
            'athens': 'GR', 'copenhagen': 'DK', 'stockholm': 'SE', 'oslo': 'NO',
            'zurich': 'CH', 'geneva': 'CH', 'brussels': 'BE', 'florence': 'IT',
            'venice': 'IT', 'milan': 'IT', 'naples': 'IT', 'nice': 'FR',
            'lyon': 'FR', 'marseille': 'FR', 'munich': 'DE', 'cologne': 'DE',
            'hamburg': 'DE', 'frankfurt': 'DE', 'bologna': 'IT', 'turin': 'IT',
            'valencia': 'ES', 'seville': 'ES', 'bilbao': 'ES', 'porto': 'PT'
        }

        self.city_to_country.update({
            # --- USA ---
            'new york': 'US', 'nyc': 'US', 'new york city': 'US',
            "san francisco": "US", "los angeles": "US", "chicago": "US", "boston": "US",
            "washington dc": "US", "miami": "US", "orlando": "US", "new orleans": "US",
            "houston": "US", "austin": "US", "dallas": "US", "denver": "US",
            "las vegas": "US", "phoenix": "US", "seattle": "US", "portland": "US",
            "san diego": "US", "honolulu": "US", "napa": "US",

            # --- Canada ---
            "vancouver": "CA", "montreal": "CA", "quebec city": "CA", "calgary": "CA",
            "ottawa": "CA", "edmonton": "CA", "winnipeg": "CA", "victoria": "CA", "toronto": "CA",

            # --- Mexico & Caribbean ---
            "mexico city": "MX", "guadalajara": "MX", "monterrey": "MX",
            "oaxaca": "MX", "cancun": "MX", "tulum": "MX", "playa del carmen": "MX",
            "puerto vallarta": "MX", "san miguel de allende": "MX",
            "cabo san lucas": "MX", "los cabos": "MX",
            "san juan": "PR", "nassau": "BS", "havana": "CU", "punta cana": "DO",
            "kingston": "JM", "montego bay": "JM",

            # --- South America ---
            "rio de janeiro": "BR", "sao paulo": "BR", "são paulo": "BR",
            "buenos aires": "AR", "mendoza": "AR",
            "santiago": "CL", "valparaiso": "CL",
            "lima": "PE", "cusco": "PE",
            "bogota": "CO", "medellin": "CO", "cartagena": "CO",
            "quito": "EC", "guayaquil": "EC",
            "la paz": "BO", "montevideo": "UY",

            # --- UK & Ireland (GB = United Kingdom) ---
            'london': 'GB', "edinburgh": "GB", "glasgow": "GB", "manchester": "GB",
            "liverpool": "GB", "birmingham": "GB", "cardiff": "GB", "belfast": "GB",

            # --- France ---
            'paris': 'FR', "bordeaux": "FR", "toulouse": "FR", "cannes": "FR", "strasbourg": "FR",

            # --- Spain ---
            "malaga": "ES", "granada": "ES", "ibiza": "ES", "palma de mallorca": "ES",
            "san sebastian": "ES", "san sebastián": "ES", "santiago de compostela": "ES",

            # --- Italy ---
            "rome": "IT", "sorrento": "IT", "positano": "IT", "capri": "IT", "modena": "IT",
            "bari": "IT", "genoa": "IT", "palermo": "IT", "catania": "IT",
            "verona": "IT", "como": "IT", "lake como": "IT",

            # --- Switzerland ---
            "basel": "CH", "lausanne": "CH", "lucerne": "CH", "interlaken": "CH",
            "zermatt": "CH", "st moritz": "CH", "st. moritz": "CH",

            # --- Portugal ---
            "faro": "PT", "coimbra": "PT", "madeira": "PT",

            # --- Germany ---
            "stuttgart": "DE", "leipzig": "DE", "dresden": "DE", "nuremberg": "DE",
            "nürnberg": "DE", "hannover": "DE", "heidelberg": "DE", "freiburg": "DE",
            "dusseldorf": "DE", "duesseldorf": "DE",

            # --- Austria ---
            "salzburg": "AT", "innsbruck": "AT",

            # --- Netherlands & Belgium ---
            "rotterdam": "NL", "the hague": "NL", "utrecht": "NL",
            "antwerp": "BE", "bruges": "BE", "ghent": "BE",

            # --- Nordics & Baltics ---
            "helsinki": "FI", "turku": "FI", "gothenburg": "SE", "malmo": "SE",
            "göteborg": "SE", "målmö": "SE",  # lenient spellings
            "bergen": "NO", "reykjavik": "IS", "aarhus": "DK",
            "riga": "LV", "tallinn": "EE", "vilnius": "LT",

            # --- Central & Eastern Europe ---
            "warsaw": "PL", "krakow": "PL", "kraków": "PL", "gdansk": "PL", "wroclaw": "PL",
            "wrocław": "PL", "bratislava": "SK", "ljubljana": "SI",
            "zagreb": "HR", "split": "HR", "dubrovnik": "HR",
            "belgrade": "RS", "bucharest": "RO", "cluj": "RO", "sofia": "BG",
            "sarajevo": "BA", "budva": "ME",

            # --- Greece & Turkey ---
            "thessaloniki": "GR", "mykonos": "GR", "santorini": "GR",
            "heraklion": "GR", "chania": "GR",
            "istanbul": "TR", "ankara": "TR", "antalya": "TR", "bodrum": "TR", "izmir": "TR",

            # --- Middle East ---
            "dubai": "AE", "abu dhabi": "AE", "doha": "QA",
            "muscat": "OM", "salalah": "OM",
            "amman": "JO", "petra": "JO",
            "beirut": "LB",
            "jerusalem": "IL", "tel aviv": "IL", "haifa": "IL",
            "riyadh": "SA", "jeddah": "SA",

            # --- Africa ---
            "cairo": "EG", "alexandria": "EG",
            "marrakesh": "MA", "marrakech": "MA", "casablanca": "MA", "fes": "MA", "fès": "MA",
            "rabat": "MA",
            "nairobi": "KE",
            "cape town": "ZA", "johannesburg": "ZA", "durban": "ZA",
            "tunis": "TN",

            # --- East & Southeast Asia ---
            "tokyo": "JP", "kyoto": "JP", "osaka": "JP", "sapporo": "JP", "hakone": "JP",
            "fukuoka": "JP",
            "seoul": "KR", "busan": "KR", "jeju": "KR",
            "beijing": "CN", "shanghai": "CN", "chengdu": "CN", "xian": "CN", "xi'an": "CN",
            "shenzhen": "CN", "guangzhou": "CN", "hangzhou": "CN", "suzhou": "CN",
            "hong kong": "HK", "macau": "MO",
            "taipei": "TW", "kaohsiung": "TW",
            "singapore": "SG",
            "bangkok": "TH", "phuket": "TH", "chiang mai": "TH",
            "hanoi": "VN", "ho chi minh city": "VN", "saigon": "VN",
            "kuala lumpur": "MY", "penang": "MY", "langkawi": "MY",
            "jakarta": "ID", "denpasar": "ID", "ubud": "ID", "yogyakarta": "ID", "bali": "ID",

            # --- South Asia ---
            "delhi": "IN", "new delhi": "IN", "mumbai": "IN", "bengaluru": "IN",
            "bangalore": "IN", "chennai": "IN", "kolkata": "IN", "hyderabad": "IN",
            "jaipur": "IN", "udaipur": "IN", "goa": "IN", "agra": "IN", "varanasi": "IN",
            "islamabad": "PK", "lahore": "PK", "karachi": "PK",
            "colombo": "LK", "male": "MV", "kathmandu": "NP", "dhaka": "BD",

            # --- Oceania ---
            "sydney": "AU", "melbourne": "AU", "brisbane": "AU", "perth": "AU",
            "adelaide": "AU", "hobart": "AU", "gold coast": "AU", "cairns": "AU",
            "auckland": "NZ", "queenstown": "NZ", "wellington": "NZ", "christchurch": "NZ"
        })


    def generate_enrichments(
        self, 
        text: str, 
        entities: List[Entity], 
        category: MessageCategory
    ) -> Optional[Dict[str, Any]]:
        """Generate enrichments based on extracted entities and message content"""
        
        enrichments = {}
        
        try:
            # Get emergency numbers for extracted cities  [REQUIRED]
            emergency_numbers = self._get_emergency_numbers(entities)
            if emergency_numbers:
                enrichments["local_emergency_numbers"] = emergency_numbers
            
            # Add creative enrichments
            creative_enrichments = self._generate_creative_enrichments(text, entities, category)
            if creative_enrichments:
                enrichments.update(creative_enrichments)
            
            return enrichments if enrichments else None
            
        except Exception as e:
            logger.error(f"Enrichment generation failed: {str(e)}")
            return None

    def _get_emergency_numbers(self, entities: List[Entity]) -> Optional[List[str]]:
        """Get emergency numbers for cities mentioned in the message"""
        
        city_entities = [e for e in entities if e.type.value == "city"]
        if not city_entities:
            return None
                
        emergency_numbers = set()
        
        for city_entity in city_entities:
            city_name = city_entity.value.lower()
            country_code = self.city_to_country.get(city_name)

            if country_code:
                emergency_number = self._get_emergency_number(country_code)
                if emergency_number:
                    emergency_numbers.add(emergency_number)
                            
        # Convert to sorted list for consistent output
        return sorted(list(emergency_numbers)) if emergency_numbers else None

    def _get_emergency_number(self, country_code: str) -> Optional[str]:
        """Get emergency number for a country, with caching and fallbacks"""
        
        # Check cache first
        if country_code in self.emergency_cache:
            return self.emergency_cache[country_code]
        
        # Known emergency numbers as fallback
        fallback_numbers = {
            'US': '911', 'CA': '911', 'MX': '911', 'GB': '999', 'FR': '112', 
            'IT': '112', 'ES': '112', 'NL': '112', 'AT': '112', 'CH': '112',
            'BE': '112', 'PT': '112', 'IE': '112', 'DK': '112', 'SE': '112',
            'NO': '112', 'FI': '112', 'CZ': '112', 'HU': '112', 'GR': '112',
            'PL': '112', 'SK': '112', 'SI': '112', 'HR': '112', 'LU': '112', 
            'DE': '112', "ZA": '112'
        }
        
        try:
            # Try API first with timeout
            url = f"https://emergencynumberapi.com/api/country/{country_code}"
            response = requests.get(url, timeout=3)
            
            if response.status_code == 200:
                data = response.json()
                # dispatch = data.get('data', {}).get('Dispatch', {})
                # emergency_data = (
                #     dispatch.get('All') or dispatch.get('GSM') or dispatch.get('Fixed') or []
                # )
                # if emergency_data and isinstance(emergency_data, list):
                #     number = emergency_data[0]
                #     self.emergency_cache[country_code] = number
                #     print(f"Fetched emergency number from API for {country_code}: {number}")
                #     logger.info(f"Fetched emergency number for {country_code}: {number}")
                #     return number
                info = data.get('data', {})  # API payload
                if info.get('Member_112') is True:
                    emergency_data = ['112']
                else:
                    dispatch = info.get('Dispatch', {})
                    emergency_data = (dispatch.get('All') or dispatch.get('GSM') or dispatch.get('Fixed') or [])
                    if not emergency_data:
                        police = info.get('Police', {})
                        emergency_data = (police.get('All') or police.get('GSM') or police.get('Fixed') or [])
                    if emergency_data and isinstance(emergency_data, list):
                        number = emergency_data[0]
                        self.emergency_cache[country_code] = number
                        print(f"Fetched emergency number from API for {country_code}: {number}")
                        logger.info(f"Fetched emergency number for {country_code}: {number}")
                        return number

        except Exception as e:
            logger.warning(f"Emergency API failed for {country_code}: {str(e)}")
        
        # Use fallback
        fallback = fallback_numbers.get(country_code)
        self.emergency_cache[country_code] = fallback
        logger.info(f"Using fallback emergency number for {country_code}: {fallback}")
        return fallback

    def _generate_creative_enrichments(
        self, 
        text: str, 
        entities: List[Entity], 
        category: MessageCategory
    ) -> Dict[str, Any]:
        """Generate creative enrichments as specified in requirements"""
        
        print(f"DEBUG: Generating creative enrichments ...")

        enrichments = {}
        
        # Sentiment analysis (simple keyword-based)
        sentiment = self._analyze_sentiment(text)
        if sentiment:
            enrichments["sentiment_analysis"] = sentiment
        
        # Travel phase detection
        travel_phase = self._detect_travel_phase(text)
        if travel_phase:
            enrichments["travel_phase"] = travel_phase
        
        # Travel disruption detection
        disruption_type = self._detect_travel_disruption(text)
        if disruption_type:
            enrichments["disruption_type"] = disruption_type
        
        # Plan-of-Action Recommendation 
        try:
            support_recommendations = self._generate_support_recommendations(text, entities, category)
            if support_recommendations:
                enrichments["support_recommendations"] = support_recommendations
        except Exception as e:
            logger.error(f"Could not generate plan-of-action: {str(e)}")
        
        return enrichments

    def _analyze_sentiment(self, text: str) -> Optional[Dict[str, Any]]:
        """Simple keyword-based sentiment analysis"""
        text_lower = text.lower()
        
        negative_words = ['frustrated', 'angry', 'upset', 'terrible', 'horrible', 'worst', 
                         'disappointed', 'furious', 'outraged', 'unacceptable', 'disaster']
        positive_words = ['great', 'excellent', 'wonderful', 'amazing', 'fantastic', 
                         'perfect', 'love', 'thank you', 'appreciate', 'helpful']
        urgent_words = ['urgent', 'emergency', 'asap', 'immediately', 'help', 'stuck', 'stranded']
        
        negative_count = sum(1 for word in negative_words if word in text_lower)
        positive_count = sum(1 for word in positive_words if word in text_lower)
        urgent_count = sum(1 for word in urgent_words if word in text_lower)
        
        if negative_count > positive_count and negative_count > 0:
            return {"mood": "negative", "intensity": min(negative_count / 3, 1.0)}
        elif positive_count > 0:
            return {"mood": "positive", "intensity": min(positive_count / 3, 1.0)}
        elif urgent_count > 0:
            return {"mood": "stressed", "intensity": min(urgent_count / 2, 1.0)}
        
        return {"mood": "neutral", "intensity": 0.5}

    def _detect_travel_phase(self, text: str) -> Optional[str]:
        """Detect what phase of travel the customer is in"""
        text_lower = text.lower()
        
        pre_travel = ['planning', 'booking', 'will travel', 'next month', 'next week', 
                      'planning to visit', 'want to book', 'looking for']
        in_transit = ['currently in', 'right now', 'at the airport', 'on the plane', 
                      'arrived', 'here now', 'just landed', 'checking in']
        post_travel = ['just returned', 'came back', 'was in', 'visited last', 
                       'trip was', 'during my stay']
        
        if any(phrase in text_lower for phrase in in_transit):
            return "in_transit"
        elif any(phrase in text_lower for phrase in post_travel):
            return "post_travel"
        elif any(phrase in text_lower for phrase in pre_travel):
            return "pre_travel"
        
        return None

    def _detect_travel_disruption(self, text: str) -> Optional[str]:
        """Detect type of travel disruption mentioned"""
        text_lower = text.lower()
        
        disruption_types = {
            'flight_delay': ['delayed', 'delay', 'late flight', 'postponed'],
            'cancellation': ['cancelled', 'canceled', 'cancellation'],
            'lost_luggage': ['lost luggage', 'missing bag', 'baggage'],
            'missed_connection': ['missed connection', 'missed flight', 'tight connection'],
            'weather': ['weather', 'storm', 'snow', 'fog', 'hurricane'],
            'strike': ['strike', 'industrial action', 'staff shortage']
        }
        
        for disruption, keywords in disruption_types.items():
            if any(keyword in text_lower for keyword in keywords):
                return disruption
        
        return None

    def _generate_support_recommendations(self, text: str, entities: List[Entity], category: MessageCategory) -> Optional[Dict[str, Any]]:
        """Generate intelligent support action recommendations using OpenAI"""
        try:
            client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            
            # Build context for the LLM
            entity_context = ", ".join([f"{e.type.value}: {e.value}" for e in entities])
            
            system_prompt = """You are an expert travel support advisor. Analyze customer messages and provide specific, actionable recommendations for support agents.

            Return ONLY valid JSON in this format:
            {
            "priority_actions": ["action1", "action2"],
            "recommended_resources": ["resource1", "resource2"], 
            "escalation_needed": true/false,
            "estimated_resolution_time": "15 minutes",
            "follow_up_required": true/false,
            "specialist_referral": "none|legal|medical|security|bookings"
            }

            Consider:
            - Message urgency and risk level
            - Specific travel context (locations, hotels, etc.)
            - Required immediate actions
            - Potential complications
            - Resource needs"""

            user_prompt = f"""
            Message Category: {category.value}
            Message: "{text}"
            Extracted Entities: {entity_context}

            Provide support recommendations for this travel customer message.
            """

            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.1,
                max_tokens=300,
                timeout=10.0
            )
            
            result = json.loads(response.choices[0].message.content.strip())
            return {"support_recommendations": result}
            
        except Exception as e:
            logger.error(f"Support recommendations failed: {str(e)}")
            return None