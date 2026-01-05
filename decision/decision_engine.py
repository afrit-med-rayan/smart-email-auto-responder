def decide_action(intent, urgency, tone):
    # Hard safety rule
    if tone["tone"] == "AGGRESSIVE":
        return {
            "action": "ESCALATE",
            "reason": "Aggressive tone detected"
        }

    intent_type = intent["intent"]
    min_confidence = min(
        intent["confidence"],
        urgency["confidence"],
        tone["confidence"]
    )

    thresholds = {
        "academic": 0.8,
        "internship": 0.75,
        "meeting": 0.7,
        "spam": 0.0
    }

    threshold = thresholds.get(intent_type, 0.85)

    if min_confidence < threshold:
        return {
            "action": "ESCALATE",
            "reason": f"Low confidence ({min_confidence})"
        }

    if intent_type == "spam":
        return {
            "action": "IGNORE",
            "reason": "Spam detected"
        }

    return {
        "action": "DRAFT_REPLY",
        "reason": "Safe to draft response"
    }
