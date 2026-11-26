from core.common_imports import json

class JsonExporter:
    def export_issue_raw_data(self, issue, output_file):
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, "w", encoding="utf-8") as file:
            json.dump(issue.raw, file, ensure_ascii=False, indent=4, default=str)
