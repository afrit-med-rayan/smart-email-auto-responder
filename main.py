import json
from nlp.intent_classifier import classify_intent
from nlp.urgency_detector import detect_urgency
from nlp.tone_analyzer import analyze_tone
from decision.decision_engine import decide_action
from responder.draft_generator import generate_draft

from store.shared import pending_drafts  

with open("data/sample_emails.json", encoding="utf-8") as f:
    emails = json.load(f)

for email in emails:
    intent = classify_intent(email)
    urgency = detect_urgency(email)
    tone = analyze_tone(email)
    decision = decide_action(intent, urgency, tone)

    print("\n==============================")
    print("Email ID:", email["id"])
    print("Intent:", intent)
    print("Urgency:", urgency)
    print("Tone:", tone)
    print("Decision:", decision)

    if decision["action"] == "DRAFT_REPLY":
        draft = generate_draft(email, intent)
        print("\nDraft Reply:\n", draft)

        pending_drafts[str(email["id"])] = {
            "draft": draft,
            "email": email
        }

print("\n Drafts stored in shared memory:", list(pending_drafts.keys()))

# Save drafts to JSON file for persistence
with open("data/pending_drafts.json", "w", encoding="utf-8") as f:
    json.dump(pending_drafts, f, indent=2, ensure_ascii=False)
print("Drafts saved to data/pending_drafts.json")
