def analyze_tone(email):
    text = email["body"]

    if text.isupper() or "!!!" in text:
        return {"tone": "AGGRESSIVE", "confidence": 0.9}

    if "please" in text.lower() or "kindly" in text.lower():
        return {"tone": "FORMAL", "confidence": 0.8}

    return {"tone": "NEUTRAL", "confidence": 0.7}
