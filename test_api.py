import sys
import os
from dotenv import load_dotenv
from typing import Dict, Any

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Load application .env 
load_dotenv()

from services.classification_service import ClassificationService
from services.entity_service import EntityService
from services.contact_service import ContactService
from services.enrichment_service import EnrichmentService
from models.schemas import MessageCategory


class TestRunner:
    def __init__(self):
        self.classification_service = ClassificationService()
        self.entity_service = EntityService()
        self.contact_service = ContactService()
        self.enrichment_service = EnrichmentService()
        
        # Test cases from the requirements
        self.test_cases = [
            {
                "message_id": "test_1",
                "text": "my wallet was stolen in Paris last night",
                "expected_category": MessageCategory.HIGH_RISK,
                "expected_entities": [{"type": "city", "value": "Paris"}],
                "expected_enrichments": {"local_emergency_numbers": ["112"]}
            },
            {
                "message_id": "test_2", 
                "text": "flight in 3 h, need assistance",
                "expected_category": MessageCategory.URGENT,
                "expected_entities": [], 
                "expected_enrichments": {}
            },
            {
                "message_id": "test_3",
                "text": "planning Rome in October with a stay at Chapter Roma and maybe NYC",
                "expected_category": MessageCategory.BASE,
                "expected_entities": [
                    {"type": "city", "value": "Rome"},
                    {"type": "hotel", "value": "Chapter Roma"},
                    {"type": "city", "value": "NYC"}
                ],
                "expected_enrichments": {"local_emergency_numbers": ["112", "911"]}
            },
            {
                "message_id": "test_4",
                "text": "Hi Fora, I'm Alex Smith (917-555-1234) in 10003. My client flies to Rome next week and just lost her passport—help!",
                "expected_category": MessageCategory.HIGH_RISK,
                "expected_entities": [{"type": "city", "value": "Rome"}],
                "expected_contact": {
                    "first_name": "Alex",
                    "last_name": "Smith",
                    "phone": "917-555-1234",
                    "zip": "10003"
                }, 
                "expected_enrichments": {"local_emergency_numbers": ["112"]}
            }, 
            {
                "message_id": "test_5",
                "text": "my bag was stolen in London last night",
                "expected_category": MessageCategory.HIGH_RISK,
                "expected_entities": [{"type": "city", "value": "London"}],
                "expected_enrichments": {"local_emergency_numbers": ["999"]}
            },
            {
                "message_id": "test_6",
                "text": "Landing in Toronto in 2 hours, need assistance with a tight connection",
                "expected_category": MessageCategory.URGENT,
                "expected_entities": [{"type": "city", "value": "Toronto"}],
                "expected_enrichments": {"local_emergency_numbers": ["911"]}
            },
            {
                "message_id": "test_7",
                "text": "Staying at The Ned and dinner at Dishoom while in London",
                "expected_category": MessageCategory.BASE,
                "expected_entities": [
                    {"type": "hotel", "value": "The Ned"},
                    {"type": "restaurant", "value": "Dishoom"},
                    {"type": "city", "value": "London"}
                ],
                "expected_enrichments": {"local_emergency_numbers": ["999"]}
            },
            {
                "message_id": "test_8",
                "text": "table at Joe's Pizza NYC at 7?",
                "expected_category": MessageCategory.BASE,
                "expected_entities": [
                    {"type": "restaurant", "value": "Joe's Pizza"},
                    {"type": "city", "value": "NYC"}
                ],
                "expected_enrichments": {"local_emergency_numbers": ["911"]}
            },
            {
                "message_id": "test_9",
                "text": "Booked Aman Venice for our honeymoon ❤️",
                "expected_category": MessageCategory.BASE,
                "expected_entities": [
                    {"type": "hotel", "value": "Aman Venice"}, 
                    {"type": "city", "value": "Venice"}
                ],
                "expected_enrichments": {"local_emergency_numbers": ["112"]}
            },
            {
                "message_id": "test_10",
                "text": "Thinking Paris first, then Toronto in June",
                "expected_category": MessageCategory.BASE,
                "expected_entities": [
                    {"type": "city", "value": "Paris"},
                    {"type": "city", "value": "Toronto"}
                ],
                "expected_enrichments": {"local_emergency_numbers": ["112", "911"]}
            },
            {
                "message_id": "test_11",
                "text": "Maybe London or Dublin for a quick weekend trip?",
                "expected_category": MessageCategory.BASE,
                "expected_entities": [
                    {"type": "city", "value": "London"},
                    {"type": "city", "value": "Dublin"}
                ],
                "expected_enrichments": {"local_emergency_numbers": ["112", "999"]}
            },
            {
                "message_id": "test_12",
                "text": "Hotel check-in at the Standard — any upgrades available?",
                "expected_category": MessageCategory.BASE,
                "expected_entities": [{"type": "hotel", "value": "The Standard"}],
                "expected_enrichments": {}
            },
            {
                "message_id": "test_13",
                "text": "Restaurant: Osteria Francescana in Modena, can you book for Friday?",
                "expected_category": MessageCategory.BASE,
                "expected_entities": [
                    {"type": "restaurant", "value": "Osteria Francescana"},
                    {"type": "city", "value": "Modena"}
                ],
                "expected_enrichments": {"local_emergency_numbers": ["112"]}
            },
            {
                "message_id": "test_14",
                "text": "my phone got stolen near Madrid metro",
                "expected_category": MessageCategory.HIGH_RISK,
                "expected_entities": [{"type": "city", "value": "Madrid"}],
                "expected_enrichments": {"local_emergency_numbers": ["112"]}
            },
            {
                "message_id": "test_15",
                "text": "urgent: client lost passport in Mexico City, need help now",
                "expected_category": MessageCategory.HIGH_RISK,
                "expected_entities": [{"type": "city", "value": "Mexico City"}],
                "expected_enrichments": {"local_emergency_numbers": ["911"]}
            },
            {
                "message_id": "test_16",
                "text": "staying at the hoxton, paris — any suite availability?",
                "expected_category": MessageCategory.BASE,
                "expected_entities": [
                    {"type": "hotel", "value": "The Hoxton"},
                    {"type": "city", "value": "Paris"}
                ],
                "expected_enrichments": {"local_emergency_numbers": ["112"]}
            },
            {
                "message_id": "test_17",
                "text": "please book a stay at Four Seasons Hotel des Bergues in Geneva",
                "expected_category": MessageCategory.BASE,
                "expected_entities": [
                    {"type": "hotel", "value": "Four Seasons Hotel des Bergues"},
                    {"type": "city", "value": "Geneva"}
                ],
                "expected_enrichments": {"local_emergency_numbers": ["112"]}
            },
            {
                "message_id": "test_18",
                "text": "Dinner at Noma in Copenhagen tomorrow, any luck with a table?",
                "expected_category": MessageCategory.URGENT,
                "expected_entities": [
                    {"type": "restaurant", "value": "Noma"},
                    {"type": "city", "value": "Copenhagen"}
                ],
                "expected_enrichments": {"local_emergency_numbers": ["112"]}
            },
            {
                "message_id": "test_19",
                "text": "table at Bottega in Napa for Saturday night",
                "expected_category": MessageCategory.BASE,
                "expected_entities": [
                    {"type": "restaurant", "value": "Bottega"},
                    {"type": "city", "value": "Napa"}
                ],
                "expected_enrichments": {"local_emergency_numbers": ["911"]}
            },
            {
                "message_id": "test_20",
                "text": "need wheelchair assistance on arrival in Berlin in 3h",
                "expected_category": MessageCategory.URGENT,
                "expected_entities": [{"type": "city", "value": "Berlin"}],
                "expected_enrichments": {"local_emergency_numbers": ["112"]}
            },
            {
                "message_id": "test_21",
                "text": "Emergency!!! car accident near Lisbon",
                "expected_category": MessageCategory.HIGH_RISK,
                "expected_entities": [{"type": "city", "value": "Lisbon"}],
                "expected_enrichments": {"local_emergency_numbers": ["112"]}
            },
            {
                "message_id": "test_22",
                "text": "I'm Jamie Lee, 310-555-0099, 94105. Staying at The St. Regis San Francisco.",
                "expected_category": MessageCategory.BASE,
                "expected_entities": [
                    {"type": "hotel", "value": "The St. Regis San Francisco"},
                    {"type": "city", "value": "San Francisco"}
                ],
                "expected_contact": {
                    "first_name": "Jamie",
                    "last_name": "Lee",
                    "phone": "310-555-0099",
                    "zip": "94105"
                },
                "expected_enrichments": {"local_emergency_numbers": ["911"]}
            },
            {
                "message_id": "test_23",
                "text": "Hi it's John (212 555 1212). Lost wallet in NYC subway. pls call me back",
                "expected_category": MessageCategory.HIGH_RISK,
                "expected_entities": [{"type": "city", "value": "NYC"}],
                "expected_contact": {
                    "first_name": "John",
                    "phone": "212-555-1212"
                    },
                "expected_enrichments": {"local_emergency_numbers": ["911"]}
            },
            {
                "message_id": "test_24",
                "text": "Need a visa support letter for a trip to Cape Town tomorrow",
                "expected_category": MessageCategory.URGENT,
                "expected_entities": [{"type": "city", "value": "Cape Town"}],
                "expected_enrichments": {"local_emergency_numbers": ["112"]}
            },
            {
                "message_id": "test_25",
                "text": "reservation at 'Le Bernardin' in New York City for Tuesday",
                "expected_category": MessageCategory.BASE,
                "expected_entities": [
                    {"type": "restaurant", "value": "Le Bernardin"},
                    {"type": "city", "value": "New York City"}
                ],
                "expected_enrichments": {"local_emergency_numbers": ["911"]}
            },
            {
                "message_id": "test_26",
                "text": "booked the marriot marquis in NYC — can you confirm breakfast?",
                "expected_category": MessageCategory.BASE,
                "expected_entities": [
                    {"type": "hotel", "value": "Marriot Marquis"},
                    {"type": "city", "value": "NYC"}
                ],
                "expected_enrichments": {"local_emergency_numbers": ["911"]}
            },
            {
                "message_id": "test_27",
                "text": "my purse was stolen at Toronto Pearson",
                "expected_category": MessageCategory.HIGH_RISK,
                "expected_entities": [{"type": "city", "value": "Toronto"}],
                "expected_enrichments": {"local_emergency_numbers": ["911"]}
            },
            {
                "message_id": "test_28",
                "text": "staying at Baur au Lac, Zurich",
                "expected_category": MessageCategory.BASE,
                "expected_entities": [
                    {"type": "hotel", "value": "Baur au Lac"},
                    {"type": "city", "value": "Zurich"}
                ],
                "expected_enrichments": {"local_emergency_numbers": ["112"]}
            },
            {
                "message_id": "test_29",
                "text": "family trip to Amsterdam, maybe Delft too, hotel undecided",
                "expected_category": MessageCategory.BASE,
                "expected_entities": [
                    {"type": "city", "value": "Amsterdam"},
                    {"type": "city", "value": "Delft"}
                ],
                "expected_enrichments": {"local_emergency_numbers": ["112"]}
            },
            {
                "message_id": "test_30",
                "text": "I'm Maya Patel, 617-555-8080 in 02139 — flight in 1h, connecting in Chicago",
                "expected_category": MessageCategory.URGENT,
                "expected_entities": [{"type": "city", "value": "Chicago"}],
                "expected_contact": {
                    "first_name": "Maya",
                    "last_name": "Patel",
                    "phone": "617-555-8080",
                    "zip": "02139"
                },
                "expected_enrichments": {"local_emergency_numbers": ["911"]}
            }
        ]

    def run_tests(self):
        """Run all test cases"""
        print("Running API Tests...\n")
        
        passed = 0
        total = len(self.test_cases)
        
        for i, test_case in enumerate(self.test_cases, 1):
            print(f"Test {i}/{total}: {test_case['message_id']}")
            print(f"Input: {test_case['text']}")
            
            try:
                result = self.process_message(test_case)
                if self.validate_result(test_case, result):
                    print("PASSED\n")
                    passed += 1
                else:
                    print("FAILED\n")
            except Exception as e:
                print(f"ERROR: {str(e)}\n")
        
        print(f"Results: {passed}/{total} tests passed")
        return passed == total

    def process_message(self, test_case: Dict[str, Any]) -> Dict[str, Any]:
        """Process a single message through all services"""
        text = test_case["text"]
        
        # Classification
        classification_result = self.classification_service.classify_message(text)
        
        # Contact extraction
        contact_info = self.contact_service.extract_contact(text)
        
        # Entity extraction
        entities = self.entity_service.extract_entities(text)
        
        # Enrichments
        enrichments = self.enrichment_service.generate_enrichments(
            text, entities, classification_result.category
        )
        
        return {
            "category": classification_result.category,
            "confidence": classification_result.confidence,
            "contact": contact_info,
            "entities": entities,
            "enrichments": enrichments
        }

    def validate_result(self, test_case: Dict[str, Any], result: Dict[str, Any]) -> bool:
        """Validate the result against expected outcomes"""
        success = True

        display_full_enrichment = True      ## Debug flag for displaying entire enrichment
        
        # Check category
        expected_category = test_case["expected_category"]
        actual_category = result["category"]
        if actual_category != expected_category:
            print(f"  ❌ Category: expected {expected_category}, got {actual_category}")
            success = False
        else:
            print(f"  ✅ Category: {actual_category}")
        
        # Check entities
        if "expected_entities" in test_case:
            expected_entities = test_case["expected_entities"]
            actual_entities = result["entities"] or []
            
            for expected_entity in expected_entities:
                found = any(
                    e.type.value == expected_entity["type"] and 
                    e.value.lower() == expected_entity["value"].lower()
                    for e in actual_entities
                )
                if not found:
                    print(f"  ❌ Missing entity: {expected_entity}")
                    success = False
                else:
                    print(f"  ✅ Found entity: {expected_entity}")
        
        # Check contact info
        if "expected_contact" in test_case:
            expected_contact = test_case["expected_contact"]
            actual_contact = result["contact"]
            
            if not actual_contact:
                print(f"  ❌ No contact info extracted")
                success = False
            else:
                for field, expected_value in expected_contact.items():
                    actual_value = getattr(actual_contact, field, None)
                    if actual_value != expected_value:
                        print(f"  ❌ Contact {field}: expected {expected_value}, got {actual_value}")
                        success = False
                    else:
                        print(f"  ✅ Contact {field}: {actual_value}")
        
        # Check enrichments
        if "expected_enrichments" in test_case:
            expected_enrichments = test_case["expected_enrichments"]
            actual_enrichments = result["enrichments"] or {}

            for key, expected_value in expected_enrichments.items():
                if key not in actual_enrichments:
                    print(f"  ❌ Missing enrichment key: {key}")
                    success = False
                elif actual_enrichments[key] != expected_value:
                    print(f"  ❌ Enrichment {key}: expected {expected_value}, got {actual_enrichments[key]}")
                    success = False 
                else:
                    print(f"  ✅ Enrichment {key}: {actual_enrichments[key]}")
            
            if display_full_enrichment:
                print(f"  🔎 Full Enrichment: {actual_enrichments}")
        
        return success

def main(): 
    """Main test runner"""
    # Set up environment
    if not os.getenv("OPENAI_API_KEY"):
        print("Warning: OPENAI_API_KEY not set. Classification will use fallback logic only.")
    
    runner = TestRunner()
    success = runner.run_tests()
    
    if success:
        print("SUCCESS: All tests passed!")
        return 0
    else:
        print("FAILURE: Some tests failed!")
        return 1

if __name__ == "__main__":
    exit_code = main()