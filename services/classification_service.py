import openai
import logging
import json
import re
from typing import Tuple
from models.schemas import ClassificationResult, MessageCategory
import os

logger = logging.getLogger(__name__)

class ClassificationService:
    def __init__(self):
        self.client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        # High-risk keywords (safety, medical, legal, fraud threats)
        self.high_risk_keywords = [
            'lost passport', 'stolen', 'hospital', 'police', 'arrested', 'scam',
            'credit card stolen', 'medical emergency', 'kidnapped', 'visa denied',
            'robbery', 'assault', 'accident', 'injured', 'fraud', 'theft',
            'embassy', 'consulate', 'detained', 'lost documents', 'stranded'
        ]
        
        # Urgent keywords (time-sensitive but not necessarily dangerous)
        self.urgent_keywords = [
            'today', 'tonight', 'tomorrow', 'in two hours', 'asap', 'immediately',
            'first thing', 'urgent', 'emergency', 'right now', 'within hours',
            'this morning', 'this afternoon', 'flight in', 'leaving soon',
            'check out', 'missed flight', 'cancelled', 'delayed'
        ]

    def classify_message(self, text: str) -> ClassificationResult:
        """
        Classify message using hybrid approach: LLM + rule-based validation
        """
        try:
            # First, try LLM classification
            llm_result = self._classify_with_llm(text)
            
            # Validate with rule-based approach
            rule_result = self._classify_with_rules(text)
            
            # Combine results with priority logic
            final_category, confidence, reasoning = self._combine_classifications(
                llm_result, rule_result
            )
            
            logger.info(f"Classification result: {final_category} (confidence: {confidence:.2f})")
            
            return ClassificationResult(
                category=final_category,
                confidence=confidence,
                reasoning=reasoning
            )
            
        except Exception as e:
            logger.error(f"LLM classification failed: {str(e)}")
            # Fallback to rule-based classification
            category, confidence = self._classify_with_rules(text)
            return ClassificationResult(
                category=category,
                confidence=confidence,
                reasoning="Fallback to rule-based classification due to LLM error"
            )

    def _classify_with_llm(self, text: str) -> Tuple[MessageCategory, float, str]:
        """Use OpenAI GPT-4 for intelligent classification"""
        
        system_prompt = """You are an AI assistant for a travel company's customer support system. 
        Classify customer messages into three categories:

        1. HIGH_RISK: Safety, medical, legal, or fraud threats - regardless of timing. Takes precedence over urgent.
           Examples: lost passport, hospital, police, arrested, scam, credit card stolen, medical emergency, kidnapped, visa denied

        2. URGENT: Caller needs a reply or action ≤ 24 h. Detect explicit time windows or urgency keywords.
           Examples: today, tonight, tomorrow, in two hours, ASAP, immediately, first thing

        3. BASE: None of the above. Regular inquiries and planning.
           Examples: booking next week, baggage allowance, suggest kid-friendly tours

        Respond with JSON: {"category": "high_risk|urgent|base", "confidence": 0.0-1.0, "reasoning": "brief explanation"}"""

        user_prompt = f"Classify this travel support message: \"{text}\""

        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.0,    
            max_tokens=200,
            timeout=15.0
        )
        
        result_text = response.choices[0].message.content.strip()
        result = json.loads(result_text)
        
        category = MessageCategory(result["category"])
        confidence = float(result["confidence"])
        reasoning = result.get("reasoning", "LLM classification")
        
        return category, confidence, reasoning

    def _classify_with_rules(self, text: str) -> Tuple[MessageCategory, float]:
        """Rule-based classification as fallback and validation"""
        text_lower = text.lower()
        
        # Check for high-risk indicators first (highest priority)
        high_risk_matches = sum(1 for keyword in self.high_risk_keywords if keyword in text_lower)
        if high_risk_matches > 0:
            confidence = min(0.9, 0.6 + (high_risk_matches * 0.1))
            return MessageCategory.HIGH_RISK, confidence
        
        # Check for urgent indicators
        urgent_matches = sum(1 for keyword in self.urgent_keywords if keyword in text_lower)
        
        # Also check for time patterns
        time_patterns = [
            r'\bin \d+\s*(hour|hr|h)\b',  # "in 3 hours"
            r'\bwithin \d+\s*(hour|day|hr|h)\b',  # "within 2 hours"
            r'\b(this|tonight|today|tomorrow)\b',  # time indicators
            r'\bflight\s*(in|at|leaves)\b',  # flight timing
        ]
        
        time_matches = sum(1 for pattern in time_patterns if re.search(pattern, text_lower))
        
        total_urgent_score = urgent_matches + time_matches
        if total_urgent_score > 0:
            confidence = min(0.8, 0.5 + (total_urgent_score * 0.1))
            return MessageCategory.URGENT, confidence
        
        # Default to base
        return MessageCategory.BASE, 0.7

    def _combine_classifications(
        self, 
        llm_result: Tuple[MessageCategory, float, str], 
        rule_result: Tuple[MessageCategory, float]
    ) -> Tuple[MessageCategory, float, str]:
        """
        Combine LLM and rule-based results with validation logic
        Priority: high_risk > urgent > base
        """
        llm_category, llm_confidence, llm_reasoning = llm_result
        rule_category, rule_confidence = rule_result
        
        # If both agree, use higher confidence
        if llm_category == rule_category:
            confidence = max(llm_confidence, rule_confidence)
            return llm_category, confidence, f"LLM + Rules agree: {llm_reasoning}"
        
        # Priority logic: high_risk trumps everything
        if rule_category == MessageCategory.HIGH_RISK or llm_category == MessageCategory.HIGH_RISK:
            if rule_category == MessageCategory.HIGH_RISK:
                return MessageCategory.HIGH_RISK, rule_confidence, "Rules detected high-risk (overrides LLM)"
            else:
                return MessageCategory.HIGH_RISK, llm_confidence, f"LLM detected high-risk: {llm_reasoning}"
        
        # If one says urgent and other says base, prefer urgent if confidence is reasonable
        if (llm_category == MessageCategory.URGENT and rule_category == MessageCategory.BASE):
            if llm_confidence > 0.6:
                return MessageCategory.URGENT, llm_confidence, f"LLM detected urgency: {llm_reasoning}"
            else:
                return MessageCategory.BASE, 0.6, "Low confidence urgency, defaulting to base"
        
        if (rule_category == MessageCategory.URGENT and llm_category == MessageCategory.BASE):
            if rule_confidence > 0.6:
                return MessageCategory.URGENT, rule_confidence, "Rules detected time-sensitive urgency"
            else:
                return MessageCategory.BASE, 0.6, "Low confidence urgency, defaulting to base"
        
        # For other disagreements, prefer higher confidence
        if llm_confidence > rule_confidence:
            return llm_category, llm_confidence, f"LLM higher confidence: {llm_reasoning}"
        else:
            return rule_category, rule_confidence, "Rules higher confidence"