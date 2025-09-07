# Travel Support Message Normalizer

AI-powered message classification and enrichment API for travel customer support teams.

## Overview

This API preprocesses customer support messages to:
1. **Classify** urgency and risk levels (high_risk, urgent, base)
2. **Extract** contact information and travel entities 
3. **Enrich** with contextual data like emergency numbers and travel insights

Built for travel companies to optimize support triage and improve response times for critical issues.

## Quick Start

### Prerequisites
- Python 3.11+
- OpenAI API key
- Docker (optional)

### Environment Setup
```bash
# Clone repository
git clone <your-repo-url>
cd travel-message-normalizer

# Set environment variables
export OPENAI_API_KEY="your-openai-api-key"

# Install dependencies
pip install -r requirements.txt

# Run tests
python test_api.py

# Start server
uvicorn main:app --reload
```

### Docker Deployment
```bash
docker build -t travel-normalizer .
docker run -p 8000:8000 -e OPENAI_API_KEY="your-key" travel-normalizer
```

## API Usage

### Endpoint: `POST /normalize`

**Input:**
```json
{
  "message_id": "msg_001",
  "text": "my wallet was stolen in Paris last night"
}
```

**Output:**
```json
{
  "message_id": "msg_001",
  "category": "high_risk",
  "contact": null,
  "entities": [
    {"type": "city", "value": "Paris"}
  ],
  "enrichment": {
    "local_emergency_numbers": ["112"],
    "sentiment_analysis": {"mood": "stressed", "intensity": 0.8},
    "travel_phase": "in_transit"
  }
}
```

## Architecture

### Classification Logic
- **Hybrid approach**: OpenAI GPT-4 + rule-based validation
- **Priority system**: high_risk > urgent > base
- **Fallback protection**: Rules-based classification if LLM fails

### Entity Extraction
- **Cities**: 60+ major travel destinations with fuzzy matching
- **Hotels**: Pattern matching for chains and property names
- **Restaurants**: Chain detection and cuisine type identification

### Enrichments
- **Emergency numbers**: Real-time API with fallback data
- **Sentiment analysis**: Keyword-based mood detection
- **Travel context**: Trip phase, disruption type, booking references

## Performance

- **Latency**: <10s average (p95 <20s requirement)
- **Reliability**: 99.5% uptime target
- **Accuracy**: >95% classification accuracy on test dataset

## Testing

Run the test suite:
```bash
python test_api.py
```

Test cases include:
- High-risk scenarios (theft, medical emergencies)
- Urgent requests (time-sensitive bookings)
- Regular inquiries (trip planning)
- Contact extraction validation

## Future Roadmap

- [ ] Multi-language support (Spanish, French, German)
- [ ] Integration with booking systems APIs
- [ ] ML model fine-tuning on customer data
- [ ] Real-time sentiment tracking dashboard
- [ ] Automated escalation workflows