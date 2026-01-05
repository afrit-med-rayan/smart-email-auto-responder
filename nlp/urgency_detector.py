def detect_urgency(email):
    text = email["body"].lower()

    if any(word in text for word in ["urgent", "asap", "immediately", "today"]):
        return {"urgency": "HIGH", "confidence": 0.9}

    if any(word in text for word in ["tomorrow", "soon"]):
        return {"urgency": "MEDIUM", "confidence": 0.8}

    return {"urgency": "LOW", "confidence": 0.7}
