def classify_intent(email):
    text = (email["subject"] + " " + email["body"]).lower()
    sender = email["sender"].lower()

    if "unsubscribe" in text or "discount" in text:
        return {"intent": "spam", "confidence": 0.95}

    if sender.endswith(".edu") or "professor" in sender:
        return {"intent": "academic", "confidence": 0.85}

    if "interview" in text or "hr" in sender:
        return {"intent": "internship", "confidence": 0.8}

    if "meeting" in text or "schedule" in text:
        return {"intent": "meeting", "confidence": 0.75}

    return {"intent": "unknown", "confidence": 0.5}
