from core.common_imports import html, re, json

class HtmlCleaner:
    @staticmethod
    def clean(value):
        if value is None:
            return ""
        if isinstance(value, (dict, list, tuple, set)):
            value = json.dumps(value, ensure_ascii=False, default=str)
        if not isinstance(value, str):
            return value
        cleaned_value = html.unescape(value)
        cleaned_value = re.sub(r"<\s*script[^>]*>.*?<\s*/\s*script\s*>", " ", cleaned_value, flags=re.IGNORECASE | re.DOTALL)
        cleaned_value = re.sub(r"<\s*style[^>]*>.*?<\s*/\s*style\s*>", " ", cleaned_value, flags=re.IGNORECASE | re.DOTALL)
        cleaned_value = re.sub(r"<[^>]+>", " ", cleaned_value)
        cleaned_value = html.unescape(cleaned_value)
        return re.sub(r"\s+", " ", cleaned_value).strip()
