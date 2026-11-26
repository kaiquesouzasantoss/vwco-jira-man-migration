from core.common_imports import re

class FileNameManager:
    @staticmethod
    def sanitize_name(value):
        if value is None:
            return "Unnamed"
        value = str(value).strip()
        sanitized_value = re.sub(r'[<>:"/\\|?*]', "_", value)
        sanitized_value = re.sub(r"\s+", " ", sanitized_value).strip(" .")
        return sanitized_value or "Unnamed"

    @staticmethod
    def limit_name(value, max_length=120):
        sanitized_value = FileNameManager.sanitize_name(value)
        return sanitized_value if len(sanitized_value) <= max_length else sanitized_value[:max_length].rstrip()

    @staticmethod
    def build_issue_base_name(issue_key, issue_summary=None, max_length=140):
        safe_issue_key = FileNameManager.sanitize_name(issue_key)
        safe_summary = FileNameManager.sanitize_name(issue_summary)
        base_name = f"{safe_issue_key}-{safe_summary}" if safe_summary and safe_summary != "Unnamed" else safe_issue_key
        return FileNameManager.limit_name(base_name, max_length=max_length)

    @staticmethod
    def build_attachment_file_name(sequence_number, original_file_name, issue_key=None, issue_summary=None):
        safe_file_name = FileNameManager.sanitize_name(original_file_name)
        if issue_key:
            issue_base_name = FileNameManager.build_issue_base_name(issue_key, max_length=80)
            return f"{issue_base_name}_attachment_{sequence_number:03d}_{safe_file_name}"
        return f"attachment_{sequence_number:03d}_{safe_file_name}"

    @staticmethod
    def build_issue_excel_file_name(issue_key, issue_summary=None):
        return f"{FileNameManager.build_issue_base_name(issue_key, issue_summary)}_Issue_Data.xlsx"

    @staticmethod
    def build_issue_json_file_name(issue_key, issue_summary=None):
        return f"{FileNameManager.build_issue_base_name(issue_key, issue_summary)}_Raw_Data.json"

    @staticmethod
    def build_attachment_hashes_file_name(issue_key, issue_summary=None):
        return f"{FileNameManager.build_issue_base_name(issue_key, issue_summary)}_Attachment_Hashes.txt"

    @staticmethod
    def build_control_workbook_file_name(extraction_key):
        return f"{FileNameManager.sanitize_name(extraction_key)}_Control.xlsx"
