import os

class SensitiveDataSanitizer:
    @staticmethod
    def mask(value):
        value = "" if value is None else str(value)
        if len(value) <= 4:
            return "****"
        return value[:2] + "****" + value[-2:]

    @staticmethod
    def sanitize_text(text):
        sanitized_text = "" if text is None else str(text)
        for sensitive_value in [os.getenv("JIRA_PASSWORD"), os.getenv("JIRA_USERNAME")]:
            if sensitive_value:
                sanitized_text = sanitized_text.replace(sensitive_value, SensitiveDataSanitizer.mask(sensitive_value))
        return sanitized_text
