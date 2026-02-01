# Building a Smart Email Auto-Responder with Local LLMs: A Journey

*By Rayan*

Managing an overflowing inbox is a challenge for students, professors, and professionals alike. In this post, I share how I built a production-ready **AI Email Auto-Responder** that doesn't just "guess" replies but understands intent, urgency, and context—all while keeping data private.

## The Problem
Standard auto-responders are dumb. "I am out of office" doesn't help a student asking about a deadline or a client with a critical issue. I wanted a system that could:
1. **Read** incoming emails.
2. **Understand** if it's a meeting request, an academic query, or spam.
3. **Decide** how urgent it is.
4. **Draft** a relevant reply.
5. **Ask** for my approval before sending.

## The Solution: A Hybrid AI Pipeline

Instead of throwing everything at ChatGPT, I architected a multi-stage pipeline:

### 1. The "Brain": Classification
I fine-tuned **BERT** (Bidirectional Encoder Representations from Transformers) on a synthetic dataset of emails. This model acts as the traffic controller. It labels every email with:
- **Intent**: `meeting`, `academic`, `personal`...
- **Urgency**: `high`, `medium`, `low`.
- **Sentiment**: `positive`, `neutral`, `aggressive`.

This step is blazing fast (<100ms) and filters out 90% of noise.

### 2. The "Writer": Generation
For drafting replies, I used **T5 (Text-To-Text Transfer Transformer)**. Unlike generic chatbots, T5 is excellent at following specific formatting instructions. I implemented a **RAG (Retrieval Augmented Generation)** system that pulls relevant context (e.g., course syllabus, FAQs) to make the replies accurate, not just grammatically correct.

### 3. The "Guard": Validation
AI can hallucinate. That's why every draft passes through a **Confidence Validator**. If the model isn't >80% sure, it flags the draft for manual review. Additionally, a safety filter checks for PII and inappropriate tone.

## Challenges & Lessons Learned

### Latency vs. Accuracy
Running models locally means managing resources. My first iteration with a 7B parameter model was too slow (15s per email). I switched to **DistilBERT** and **T5-Small**, reducing latency by 95% while maintaining acceptable accuracy for drafted replies.

### The "Human-in-the-Loop"
Trust is earned. I built a **Telegram Bot** integration. Now, when a high-urgency email arrives, I get a ping on my phone with a draft. I can reply `/approve`, `/modify`, or `/ignore`. This simple loop makes the system usable in the real world.

## Tech Stack
- **Backend**: FastAPI
- **ML**: PyTorch, HuggingFace, ONNX
- **Infrastructure**: Docker, Redis, PostgreSQL
- **Monitoring**: Streamlit Dashboard

## Future Work
I plan to add **Calendar Integration** to automatically book slots for meeting requests and explore **Quantization** to run larger models on consumer hardware.

---
*Check out the full code on [GitHub](https://github.com/afrit-med-rayan/smart-email-auto-responder).*
