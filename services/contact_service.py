#########################################################################################
#  Fora Take-Home Project: "Normalize" Chatbot API
#  contact_service.py: Service for extracting client contact information.
#                      Done using regex and phonenumbers Python library. 
#########################################################################################


import re
import logging
from typing import Optional, Tuple
from models.schemas import ContactInfo

# Optional: pass an initialized spaCy model (e.g., en_core_web_md) to the constructor
try:
    import phonenumbers
    from phonenumbers import PhoneNumberMatcher, PhoneNumberFormat, is_valid_number, region_code_for_number
except Exception:
    phonenumbers = None

logger = logging.getLogger(__name__)

class ContactService:
    def __init__(self, nlp=None, default_region: str = "US"):
        self.nlp = nlp
        self.default_region = default_region

        # Email (case-insensitive; corrected final TLD class)
        self.email_re = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b", re.IGNORECASE)

        # Zip / postal (US, CA, UK). We’ll try the “cued” ones first.
        self.us_zip_re   = re.compile(r"\b\d{5}(?:-\d{4})?\b")
        self.ca_post_re  = re.compile(r"\b[ABCEGHJ-NPRSTVXY]\d[ABCEGHJ-NPRSTV-Z]\s?\d[ABCEGHJ-NPRSTV-Z]\d\b", re.IGNORECASE)
        # Pragmatic UK postcode regex (tolerant)
        self.uk_post_re  = re.compile(r"\b(?:GIR\s?0AA|[A-Z]{1,2}\d[A-Z\d]?\s?\d[ABD-HJLNP-UW-Z]{2})\b", re.IGNORECASE)

        # Name indicators (punctuation-aware; supports O’Brien, hyphenated, initials)
        name_token = r"[A-Z][A-Za-z'’\-\.]+"
        self.name_patterns = [
            re.compile(rf"\b(?:my name is|i'm|i am|this is|it'?s)\s+(?P<name>{name_token}(?:\s+{name_token}){{0,2}})", re.IGNORECASE),
            re.compile(rf"\bfrom\s+(?P<name>{name_token}(?:\s+{name_token}){{0,2}})", re.IGNORECASE),
        ]
        # Heuristic: “Name, phone/email …” or “Name (phone) …”
        self.leading_name_re = re.compile(rf"\b(?P<name>{name_token}(?:\s+{name_token}){{0,2}})[,\s]*(?:\(\+?\d|[0-9]{2,}|[A-Za-z0-9._%+-]+@)", re.IGNORECASE)

        # When multiple codes appear, prefer ones preceded by cues
        self.zip_cues = re.compile(r"(zip|postal|postcode)\s*[:#\s]", re.IGNORECASE)

    # ----------------- public -----------------
    def extract_contact(self, text: str) -> Optional[ContactInfo]:
        """Extract email, phone, zip/postcode, first/last name from free text."""
        try:
            contact = ContactInfo()

            contact.email = self._extract_email(text)
            contact.phone = self._extract_phone(text)
            contact.zip   = self._extract_zip(text)

            first, last = self._extract_name(text)
            if first: contact.first_name = first
            if last:  contact.last_name  = last

            if not any([contact.email, contact.phone, contact.zip, contact.first_name, contact.last_name]):
                return None

            logger.info(f"Extracted contact info: {self._contact_summary(contact)}")
            return contact
        except Exception as e:
            logger.error(f"Contact extraction failed: {e}")
            return None

    # ----------------- pieces -----------------
    def _extract_email(self, text: str) -> Optional[str]:
        m = self.email_re.search(text)
        return m.group(0).lower() if m else None

    def _extract_phone(self, text: str) -> Optional[str]:
        # Prefer phonenumbers (robust, international); fall back to simple US formatting.
        if phonenumbers is not None:
            try:
                for match in PhoneNumberMatcher(text, self.default_region):
                    num = match.number
                    if is_valid_number(num):
                        region = region_code_for_number(num) or self.default_region
                        if region in ("US", "CA"):
                            # Return normalized US/CA as 999-999-9999
                            nat = phonenumbers.format_number(num, PhoneNumberFormat.NATIONAL)
                            digits = re.sub(r"\D", "", nat)
                            if len(digits) == 10:
                                return f"{digits[:3]}-{digits[3:6]}-{digits[6:]}"
                            # fall back to NATIONAL string if unexpected length
                            return nat
                        # International → E.164 (“+…”), avoids ambiguous dashes
                        return phonenumbers.format_number(num, PhoneNumberFormat.E164)
            except Exception as e:
                logger.debug(f"phonenumbers parse failed, falling back: {e}")

        # Fallback (US-like blobs)
        digits = re.sub(r"[^\d]", "", text)
        m = re.search(r"(\d{10})(?!\d)", digits)
        if m:
            seq = m.group(1)
            return f"{seq[:3]}-{seq[3:6]}-{seq[6:]}"
        return None

    def _extract_zip(self, text: str) -> Optional[str]:
        # First: look for cued segments like "zip 94105"
        cued = self.zip_cues.search(text)
        if cued:
            tail = text[cued.end():][:20]  # short window
            for rx in (self.us_zip_re, self.ca_post_re, self.uk_post_re):
                m = rx.search(tail)
                if m: return m.group(0).upper()

        # Otherwise, scan whole text (US → CA → UK order to reduce false positives)
        for rx in (self.us_zip_re, self.ca_post_re, self.uk_post_re):
            m = rx.search(text)
            if m: return m.group(0).upper()
        return None

    def _extract_name(self, text: str) -> Tuple[Optional[str], Optional[str]]:
        # 1) spaCy PERSON (if provided)
        if self.nlp is not None:
            try:
                doc = self.nlp(text)
                persons = [ent.text for ent in doc.ents if ent.label_ == "PERSON"]
                if persons:
                    first, last = self._split_name(persons[0])
                    if first or last:
                        return first, last
            except Exception as e:
                logger.debug(f"spaCy name parse failed, continuing: {e}")

        # 2) Rule-based indicators
        for rx in self.name_patterns:
            m = rx.search(text)
            if m:
                return self._split_name(m.group("name"))

        # 3) Leading-name heuristic (e.g., "Jamie Lee, 310-...")
        m = self.leading_name_re.search(text)
        if m:
            return self._split_name(m.group("name"))

        return None, None

    # ----------------- helpers -----------------
    def _split_name(self, name: str) -> Tuple[Optional[str], Optional[str]]:
        # Remove common prefixes
        name = re.sub(r"^(mr|mrs|ms|dr|prof)\.?\s+", "", name, flags=re.IGNORECASE).strip()
        parts = [p for p in re.split(r"\s+", name) if p]
        if not parts: return None, None
        if len(parts) == 1: return parts[0].replace(".", "").title(), None
        # Keep last token as last name, join the rest as first name (handles “Mary Kate O’Brien”)
        first = " ".join(parts[:-1]).replace(".", "").title()
        last  = parts[-1].replace(".", "")
        # Preserve apostrophes/hyphens in proper case
        last  = "-".join([seg.capitalize() for seg in last.split("-")])
        last  = "’".join([seg.capitalize() for seg in last.split("’")]) if "’" in last else "'".join([seg.capitalize() for seg in last.split("'")])
        return first, last

    def _contact_summary(self, contact: ContactInfo) -> str:
        parts = []
        if contact.first_name or contact.last_name:
            parts.append(f"name={(contact.first_name or '')} {(contact.last_name or '')}".strip())
        if contact.email: parts.append(f"email={contact.email}")
        if contact.phone: parts.append(f"phone={contact.phone}")
        if contact.zip:   parts.append(f"zip={contact.zip}")
        return ", ".join(parts) if parts else "no contact info"
