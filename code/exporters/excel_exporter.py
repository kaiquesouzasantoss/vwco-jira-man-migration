from core.common_imports import Workbook, json
from services.issue_service import IssueService
from utils.html_cleaner import HtmlCleaner
from utils.excel_helper import ExcelHelper

class ExcelExporter:
    def __init__(self, field_name_map):
        self.field_name_map = field_name_map

    def export_issue_to_excel(self, issue, output_file, comments=None, worklogs=None):
        output_file.parent.mkdir(parents=True, exist_ok=True)
        workbook = Workbook()
        overview_sheet = workbook.active
        overview_sheet.title = "Overview"
        fields_sheet = workbook.create_sheet("Fields")
        rendered_fields_sheet = workbook.create_sheet("Rendered Fields")
        comments_sheet = workbook.create_sheet("Comments")
        worklogs_sheet = workbook.create_sheet("Worklogs")
        activities_sheet = workbook.create_sheet("Activities")
        self._write_overview_sheet(overview_sheet, issue)
        self._write_fields_sheet(fields_sheet, issue)
        self._write_rendered_fields_sheet(rendered_fields_sheet, issue)
        self._write_comments_sheet(comments_sheet, issue, comments or [])
        self._write_worklogs_sheet(worklogs_sheet, issue, worklogs or [])
        self._write_activities_sheet(activities_sheet, issue)
        for sheet in workbook.worksheets:
            ExcelHelper.remove_empty_rows(sheet)
            ExcelHelper.format_sheet(sheet)
        workbook.save(output_file)

    def _write_overview_sheet(self, sheet, issue):
        sheet.append(["Property", "Value"])
        overview_rows = [["Issue Key", issue.key], ["Summary", IssueService.get_issue_summary(issue)], ["Status", IssueService.get_issue_status(issue)], ["Issue Type", IssueService.get_issue_type(issue)], ["Created", IssueService.get_issue_created_date(issue)], ["Updated", IssueService.get_issue_updated_date(issue)], ["Assignee", IssueService.get_issue_assignee(issue)], ["Reporter", IssueService.get_issue_reporter(issue)], ["Priority", IssueService.get_issue_priority(issue)]]
        overview_rows.append(["Parent Key", IssueService.get_issue_parent_key(issue)])
        overview_rows.append(["Parent Summary", IssueService.get_issue_parent_summary(issue)])
        try: description = issue.fields.description or ""
        except Exception: description = ""
        overview_rows.append(["Description", description])
        for property_name, value in overview_rows:
            clean_value = HtmlCleaner.clean(value)
            if str(clean_value).strip() != "":
                ExcelHelper.append_non_empty_row(sheet, [HtmlCleaner.clean(property_name), clean_value])

    def _write_fields_sheet(self, sheet, issue):
        sheet.append(["Issue Key", "Field ID", "Field Name", "Value"])
        for field_id, value in issue.raw.get("fields", {}).items():
            field_name = self.field_name_map.get(field_id, field_id)
            clean_value = HtmlCleaner.clean(self._serialize_value(value))
            if str(clean_value).strip() != "":
                ExcelHelper.append_non_empty_row(sheet, [issue.key, field_id, HtmlCleaner.clean(field_name), clean_value])

    def _write_rendered_fields_sheet(self, sheet, issue):
        sheet.append(["Issue Key", "Field ID", "Field Name", "Rendered Value"])
        for field_id, value in issue.raw.get("renderedFields", {}).items():
            field_name = self.field_name_map.get(field_id, field_id)
            clean_value = HtmlCleaner.clean(self._serialize_value(value))
            if str(clean_value).strip() != "":
                ExcelHelper.append_non_empty_row(sheet, [issue.key, field_id, HtmlCleaner.clean(field_name), clean_value])

    def _write_comments_sheet(self, sheet, issue, comments):
        sheet.append(["Issue Key", "Comment ID", "Author", "Created", "Updated", "Body"])
        for comment in comments:
            body = HtmlCleaner.clean(comment.get("body", ""))
            if str(body).strip() != "":
                ExcelHelper.append_non_empty_row(sheet, [issue.key, comment.get("id", ""), HtmlCleaner.clean(comment.get("author", {}).get("displayName", "")), HtmlCleaner.clean(comment.get("created", "")), HtmlCleaner.clean(comment.get("updated", "")), body])

    def _write_worklogs_sheet(self, sheet, issue, worklogs):
        sheet.append(["Issue Key", "Worklog ID", "Author", "Created", "Updated", "Started", "Time Spent", "Time Spent Seconds", "Comment"])
        for worklog in worklogs:
            ExcelHelper.append_non_empty_row(sheet, [issue.key, worklog.get("id", ""), HtmlCleaner.clean(worklog.get("author", {}).get("displayName", "")), HtmlCleaner.clean(worklog.get("created", "")), HtmlCleaner.clean(worklog.get("updated", "")), HtmlCleaner.clean(worklog.get("started", "")), HtmlCleaner.clean(worklog.get("timeSpent", "")), worklog.get("timeSpentSeconds", ""), HtmlCleaner.clean(worklog.get("comment", ""))])

    def _write_activities_sheet(self, sheet, issue):
        sheet.append(["Issue Key", "History ID", "Created", "Author", "Field", "From", "From String", "To", "To String"])
        for history in issue.raw.get("changelog", {}).get("histories", []):
            for item in history.get("items", []):
                ExcelHelper.append_non_empty_row(sheet, [issue.key, history.get("id", ""), history.get("created", ""), HtmlCleaner.clean(history.get("author", {}).get("displayName", "")), HtmlCleaner.clean(item.get("field", "")), HtmlCleaner.clean(item.get("from", "")), HtmlCleaner.clean(item.get("fromString", "")), HtmlCleaner.clean(item.get("to", "")), HtmlCleaner.clean(item.get("toString", ""))])

    def _serialize_value(self, value):
        if value is None: return ""
        if isinstance(value, str): return HtmlCleaner.clean(value)
        if isinstance(value, (int, float, bool)): return value
        if isinstance(value, list):
            values = [self._serialize_value(item) for item in value]
            return HtmlCleaner.clean(" | ".join(str(item) for item in values if str(item).strip() != ""))
        if isinstance(value, dict):
            preferred_keys = ["displayName", "name", "value", "key", "id", "emailAddress"]
            extracted_values = []
            for key in preferred_keys:
                if key in value and value.get(key) is not None:
                    extracted_value = str(self._serialize_value(value.get(key))).strip()
                    if extracted_value != "": extracted_values.append(extracted_value)
            if extracted_values: return HtmlCleaner.clean(" | ".join(extracted_values))
            return HtmlCleaner.clean(json.dumps(value, ensure_ascii=False, default=str))
        return HtmlCleaner.clean(str(value))
