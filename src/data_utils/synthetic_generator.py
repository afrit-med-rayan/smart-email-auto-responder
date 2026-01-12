"""
Synthetic Email Generator

Generates realistic labeled email data for training ML models.
Includes templates for various intents: academic, internship, meeting, etc.
"""

import json
import random
import uuid
import os
from typing import List, Dict, Any
from datetime import datetime, timedelta

class SyntheticGenerator:
    """Generates synthetic email datasets."""
    
    def __init__(self, output_dir: str = "data/raw"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        
        # Templates and slots for generation
        self.templates = {
            "academic": [
                "Dear Professor, I am writing to ask about the {assignment} due on {date}.",
                "Hi, could you clarify the requirements for the {course} final project?",
                "I will be unable to attend the {class_type} tomorrow due to illness.",
                "Is it possible to get an extension on the {assignment}? I have been sick.",
                "Can we meet to discuss my grade for the recent {assignment}?",
            ],
            "internship": [
                "I am writing to apply for the {role} position at {company}.",
                "Thank you for the interview opportunity for the {role} position.",
                "Could you please update me on the status of my application for {role}?",
                "Attached is my resume for the {season} {role} internship.",
                "I would like to withdraw my application for the {role} position."
            ],
            "meeting": [
                "Can we schedule a time to sync up on the {project}?",
                "Are you available for a quick call on {day} at {time}?",
                "I've sent a calendar invite for our meeting about {topic}.",
                "Let's reschedule our {meeting_type} to next week.",
                "Meeting reminder: {topic} starts in 15 minutes."
            ],
            "support": [
                "I am having trouble logging into my account.",
                "The system is throwing an error when I try to {action}.",
                "I need help resetting my password for the portal.",
                "My payment for {service} failed, please assist.",
                "I found a bug in the latest release regarding {feature}."
            ],
            "spam": [
                "CONGRATULATIONS! You've won a {prize}!",
                "Click here to claim your exclusive discount on {product}.",
                "Urgent: Your account will be suspended if you don't verify immediately.",
                "Make money fast working from home! No experience needed.",
                "Meet singles in your area tonight!"
            ],
            "general": [
                "Just checking in to see how you are doing.",
                "Thanks for the update.",
                "Message received.",
                "Have a great weekend!",
                "Here is the document you requested."
            ]
        }
        
        self.slots = {
            "assignment": ["Homework 1", "Lab report", "Thesis draft", "Midterm exam", "Final paper"],
            "course": ["CS101", "History 202", "Deep Learning", "Calculus", "Physics"],
            "class_type": ["lecture", "lab", "recitation", "seminar"],
            "role": ["Software Engineer", "Data Scientist", "Product Manager", "Research Intern", "Analyst"],
            "company": ["TechCorp", "DataSystems", "InnovateAI", "FutureNet", "SoftSolutions"],
            "season": ["Summer", "Fall", "Spring", "Winter"],
            "project": ["migration project", "Q3 roadmap", "dashboard feature", "API integration", "MVP launch"],
            "day": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
            "time": ["10 AM", "2 PM", "11:30 AM", "4 PM", "9 AM"],
            "meeting_type": ["weekly sync", "1:1", "standup", "review", "planning session"],
            "topic": ["budget review", "design sprint", "customer feedback", "team building"],
            "action": ["upload files", "save changes", "submit form", "access the dashboard"],
            "service": ["subscription", "hosting", "premium plan"],
            "feature": ["search", "login", "export", "notifications"],
            "prize": ["iPhone 15", "$1000 Gift Card", "free cruise", "luxury vacation"],
            "product": ["sunglasses", "watches", "software", "insurance"],
            "date": ["Monday", "next week", "tomorrow", "Jan 15th"]
        }
        
        self.senders = {
            "academic": ["prof@university.edu", "student@university.edu", "dept@university.edu"],
            "internship": ["hr@company.com", "recruiter@agency.com", "jobs@linkedin.com"],
            "meeting": ["colleague@work.com", "manager@work.com", "assistant@work.com"],
            "support": ["user@gmail.com", "customer@yahoo.com", "support@service.net"],
            "spam": ["promo@marketing.com", "winner@crypto.net", "alert@security-check.com"],
            "general": ["friend@gmail.com", "mom@yahoo.com", "newsletter@substack.com"]
        }

    def _fill_template(self, template: str) -> str:
        """Fill template slots with random values."""
        words = template.split()
        filled_words = []
        for word in words:
            clean_word = word.strip(".,?!")
            if clean_word.startswith("{") and clean_word.endswith("}"):
                key = clean_word[1:-1]
                if key in self.slots:
                    replacement = random.choice(self.slots[key])
                    # Preserve punctuation
                    if word.endswith((".", ",", "?", "!")):
                        replacement += word[-1]
                    filled_words.append(replacement)
                else:
                    filled_words.append(word)
            else:
                filled_words.append(word)
        return " ".join(filled_words)

    def generate_sample(self, intent: str = None) -> Dict[str, Any]:
        """Generate a single email sample."""
        if not intent:
            intent = random.choice(list(self.templates.keys()))
            
        template = random.choice(self.templates[intent])
        body = self._fill_template(template)
        sender = random.choice(self.senders[intent])
        
        # Add some noise/variation
        subject = " ".join(body.split()[:5]) + "..."
        
        # Determine urgency (heuristic)
        urgency = "low"
        if intent in ["academic", "meeting"]:
            urgency = random.choice(["medium", "high"])
        if "Urgent" in body or "failed" in body or "deadline" in body:
            urgency = "high"
        if intent == "spam":
            urgency = "low" # Functionally low priority, though spam claims high
            
        return {
            "id": str(uuid.uuid4()),
            "text": body,
            "sender": sender,
            "subject": subject,
            "label_intent": intent,
            "label_urgency": urgency,
            "label_sentiment": random.choice(["neutral", "positive", "negative"]), # Placeholder
            "timestamp": datetime.now().isoformat()
        }

    def generate_dataset(self, num_samples: int = 100, filename: str = "synthetic_train.json"):
        """Generate a full dataset and save to file."""
        data = []
        print(f"Generating {num_samples} samples...")
        
        for _ in range(num_samples):
            # Weighted random choice to ensure balance
            data.append(self.generate_sample())
            
        path = os.path.join(self.output_dir, filename)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
            
        print(f"Saved dataset to {path}")
        return path

if __name__ == "__main__":
    generator = SyntheticGenerator()
    generator.generate_dataset(100, "synthetic_dataset.json")
