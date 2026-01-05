def generate_draft(email, intent):
    sender = email.get("sender", "there")

    if intent["intent"] == "academic":
        return (
            f"Dear {sender},\n\n"
            f"Thank you for your message. I have received your email and "
            f"will get back to you shortly with the requested information.\n\n"
            f"Best regards,\nRayan"
        )

    if intent["intent"] == "internship":
        return (
            f"Hello {sender},\n\n"
            f"Thank you for reaching out. I appreciate the opportunity and "
            f"will confirm my availability shortly.\n\n"
            f"Kind regards,\nRayan"
        )

    if intent["intent"] == "meeting":
        return (
            f"Hello {sender},\n\n"
            f"Thank you for the message. I am available at the proposed time. "
            f"Please let me know if that works for you.\n\n"
            f"Best,\nRayan"
        )

    return None
