import json
from nlp.intent_classifier import classify_intent
from nlp.urgency_detector import detect_urgency
from nlp.tone_analyzer import analyze_tone
from decision.decision_engine import decide_action
from responder.draft_generator import generate_draft

with open("data/sample_emails.json", encoding="utf-8") as f:
    emails = json.load(f)

for email in emails:
    intent = classify_intent(email)
    urgency = detect_urgency(email)
    tone = analyze_tone(email)
    decision = decide_action(intent, urgency, tone)

    print("\n Email ID:", email["id"])
    print("Intent:", intent)
    print("Urgency:", urgency)
    print("Tone:", tone)
    print("Decision:", decision)

    if decision["action"] == "DRAFT_REPLY":
        draft = generate_draft(email, intent)
        print("\n Draft Reply:\n")
        print(draft)
