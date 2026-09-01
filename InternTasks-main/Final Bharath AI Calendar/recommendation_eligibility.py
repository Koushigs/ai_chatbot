"""
recommendation_eligibility.py - Recommendation Eligibility Engine
Decides whether affiliate product recommendations should be generated for a query/session.
"""

from typing import Dict, Any, Optional
import re


DEFAULT_CONFIG: Dict[str, Any] = {
    "minimum_score": 50,
    "cooldown_replies": 2,
    "maximum_products": 3,
    "enable_intent_detection": True,
    "enable_context_rules": True,
    "enable_payment_suppression": True,
    "enable_frequency_control": True,
}


class RecommendationEligibilityEngine:
    """
    Recommendation Eligibility Engine
    Solely responsible for determining if product recommendations are eligible to be generated.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = {**DEFAULT_CONFIG, **(config or {})}
        # Stores session turn counts for last recommendation: {conversation_hash: last_rec_turn_index}
        self._session_last_rec_turn: Dict[str, int] = {}

    def update_config(self, new_config: Dict[str, Any]) -> None:
        """Update configuration dynamically."""
        self.config.update(new_config)

    def record_recommendation_served(self, conversation_hash: str, turn_index: int) -> None:
        """Record that a recommendation was served in a given session turn."""
        if conversation_hash:
            self._session_last_rec_turn[conversation_hash] = turn_index

    def evaluate(
        self,
        user_query: str,
        tool_type: Optional[str],
        extracted_entities: Dict[str, Any],
        ai_response: str,
        session_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Evaluates eligibility for product recommendations.

        Returns:
            Dict containing:
                - "should_recommend": bool
                - "reason": str
                - "score": int
                - "max_products": int
        """
        user_query_clean = (user_query or "").strip()
        user_lower = user_query_clean.lower()
        conversation_hash = session_context.get("conversation_hash", "")
        current_turn = session_context.get("message_count", 0)
        pending_payments = session_context.get("pending_payments", {})

        # ========================================================
        # RULE 1: PAYMENT STATE SUPPRESSION
        # ========================================================
        if self.config.get("enable_payment_suppression", True):
            user_id = session_context.get("user_id", "")
            # Suppress if conversation or user is currently in a pending payment state
            if (conversation_hash and conversation_hash in pending_payments) or (user_id and user_id in pending_payments):
                return {
                    "should_recommend": False,
                    "reason": "Affiliate recommendations suppressed during active payment flow.",
                    "score": 0,
                    "max_products": 0
                }
            # Suppress if tool detected is kundali or janmarashi awaiting payment confirmation
            if tool_type in ["kundali", "janmarashi"]:
                return {
                    "should_recommend": False,
                    "reason": f"Recommendations suppressed for {tool_type} payment flow.",
                    "score": 0,
                    "max_products": 0
                }

        # ========================================================
        # RULE 2: GREETINGS / GENERIC CONVERSATION SUPPRESSION
        # ========================================================
        generic_patterns = [
            r"^hi\s*$", r"^hi[,!?.\s]*$", r"^hello\s*$", r"^hello[,!?.\s]*$",
            r"^thanks\s*$", r"^thank\s+you\s*$", r"^ok\s*$", r"^okay\s*$",
            r"^bye\s*$", r"^good\s+morning\s*$", r"^good\s+evening\s*$"
        ]
        for pattern in generic_patterns:
            if re.search(pattern, user_lower):
                return {
                    "should_recommend": False,
                    "reason": "Generic greeting or conversational query.",
                    "score": 0,
                    "max_products": 0
                }

        # ========================================================
        # RULE 2b: HOROSCOPE MISSING RASHI SUPPRESSION
        # ========================================================
        if tool_type == "horoscope":
            has_rashi_in_query = extracted_entities.get("rashi_in_query", False)
            if not has_rashi_in_query:
                return {
                    "should_recommend": False,
                    "reason": "Horoscope query missing explicit Rashi sign in user request.",
                    "score": 10,
                    "max_products": 0
                }

        # ========================================================
        # RULE 2c: MUHURTA / VEHICLE / PROPERTY TIMING SCORING
        # ========================================================
        muhurta_or_asset_keywords = [
            "muhurat", "muhurtham", "subha muruth", "shubh muhurat", "auspicious time",
            "good time to buy", "best time to buy", "car", "vehicle", "bike", "scooter",
            "house", "property", "flat", "land", "plot", "automobile", "griha pravesh",
            "pooja", "puja", "business", "shop", "machinery", "machine", "shubh timing"
        ]
        remedy_explicit_keywords = [
            "gemstone", "rudraksha", "yantra", "rashi stone", "lucky stone", "ring",
            "pendant", "mala", "pyramid", "idol", "statue", "रत्न", "रुद्राक्ष"
        ]
        
        has_asset_or_muhurta = any(kw in user_lower for kw in muhurta_or_asset_keywords)
        has_explicit_remedy = any(kw in user_lower for kw in remedy_explicit_keywords)

        # ========================================================
        # RULE 3: SESSION FREQUENCY / COOLDOWN CONTROL
        # ========================================================
        if self.config.get("enable_frequency_control", True) and conversation_hash:
            last_turn = self._session_last_rec_turn.get(conversation_hash)
            cooldown = self.config.get("cooldown_replies", 2)
            user_turn_index = (current_turn + 1) // 2
            if last_turn is not None:
                last_user_turn = (last_turn + 1) // 2
                turns_since_last = user_turn_index - last_user_turn
                if turns_since_last <= cooldown:
                    return {
                        "should_recommend": False,
                        "reason": f"Recommendation cooldown active ({turns_since_last} <= {cooldown} turns).",
                        "score": 10,
                        "max_products": 0,
                        "is_muhurat_asset_query": has_asset_or_muhurta,
                        "has_explicit_remedy": has_explicit_remedy
                    }

        # ========================================================
        # RULE 4: USER INTENT SCORING
        # ========================================================
        score = 0
        reasons = []

        if self.config.get("enable_intent_detection", True):
            # Muhurat / Vehicle / Property / Asset timing request (+40 score for high purchase intent)
            if has_asset_or_muhurta:
                score += 40
                reasons.append("Muhurat/asset timing query (high purchase intent)")

            # Explicit product/shopping purchase request (+40)
            product_keywords = [
                "buy", "purchase", "price", "shop", "store", "recommend product",
                "where to get", "cost of", "item", "kit", "mala", "ring", "yantra",
                "खरीदें", "कीमत", "सामग्री"
            ]
            if any(kw in user_lower for kw in product_keywords):
                score += 40
                reasons.append("Explicit product/shopping query")

            # Festival preparation (+35)
            festival_keywords = [
                "festival", "diwali", "dussehra", "holi", "navratri", "ganesh",
                "rakhi", "sankranti", "pooja", "puja", "त्योहार", "पूजा"
            ]
            if any(kw in user_lower for kw in festival_keywords) or extracted_entities.get("festivals"):
                score += 35
                reasons.append("Festival or pooja preparation")

            # Gemstone / Rudraksha / Remedy selection (+35)
            remedy_keywords = [
                "gemstone", "rudraksha", "yantra", "rashi stone", "lucky stone",
                "remedy", "dosha", "gem", "रत्न", "रुद्राक्ष"
            ]
            if any(kw in user_lower for kw in remedy_keywords):
                score += 35
                reasons.append("Gemstone/Rudraksha/Remedy selection")

            # Horoscope / Panchang / Festival / Predictive tool context (+50)
            if tool_type in ["horoscope", "panchang", "monthly_festivals", "holidays"] or (tool_type and tool_type.startswith("predictive")):
                score += 50
                reasons.append(f"Tool context matched: {tool_type}")

        # ========================================================
        # RULE 5: CONTEXT & ENTITIES EVALUATION
        # ========================================================
        if self.config.get("enable_context_rules", True):
            if extracted_entities.get("rashi"):
                score += 15
                reasons.append(f"Extracted Rashi: {extracted_entities['rashi']}")
            if extracted_entities.get("lucky_number") or extracted_entities.get("lucky_color"):
                score += 10
                reasons.append("Extracted lucky attributes")

        min_score = self.config.get("minimum_score", 50)
        should_recommend = score >= min_score

        reason_str = "; ".join(reasons) if reasons else "General query"
        if not should_recommend:
            reason_str = f"Score ({score}) below threshold ({min_score}): " + reason_str

        return {
            "should_recommend": should_recommend,
            "reason": reason_str,
            "score": score,
            "max_products": self.config.get("maximum_products", 3),
            "is_muhurat_asset_query": has_asset_or_muhurta,
            "has_explicit_remedy": has_explicit_remedy
        }
