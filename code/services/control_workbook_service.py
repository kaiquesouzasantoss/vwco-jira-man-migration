from core.common_imports import Workbook, load_workbook, datetime, Lock
from core.constants import FOUND_ISSUES_SHEET_NAME, PROGRESS_CONTROL_SHEET_NAME, MIGRATION_REPORT_SHEET_NAME, STATUS_PENDING, STATUS_IN_PROGRESS, STATUS_MIGRATED, STATUS_FAILED
from services.issue_service import IssueService
from utils.excel_helper import ExcelHelper
from utils.html_cleaner import HtmlCleaner
from utils.logger import Logger

class ControlWorkbookService:
    FOUND_HEADERS = ["Issue Key", "Summary", "Status", "Issue Type", "Parent Key", "Parent Summary", "Is Subtask", "Created", "Updated", "Assignee", "Reporter", "Priority"]
    PROGRESS_HEADERS = ["Issue Key", "Summary", "Jira Status", "Migration Status", "Attempts", "Last Started At", "Last Finished At", "Message"]
    REPORT_HEADERS = ["Issue Key", "Status", "Message", "Attachments Count", "Issue Folder", "Excel File", "JSON File", "Attachment Hashes File", "SHA256 Excel", "SHA256 JSON", "Processed At", "Script Version", "JQL Used", "Workers Used"]

    def __init__(self, control_file):
        self.control_file = control_file
        self.lock = Lock()

    def initialize_or_update_workbook(self, issues):
        with self.lock:
            workbook = self._load_or_create_workbook()
            found_sheet = self._get_or_create_sheet(workbook, FOUND_ISSUES_SHEET_NAME, self.FOUND_HEADERS)
            progress_sheet = self._get_or_create_sheet(workbook, PROGRESS_CONTROL_SHEET_NAME, self.PROGRESS_HEADERS)
            self._get_or_create_sheet(workbook, MIGRATION_REPORT_SHEET_NAME, self.REPORT_HEADERS)
            self._refresh_found_issues_sheet(found_sheet, issues)
            self._append_missing_progress_rows(progress_sheet, issues)
            self._format_all_sheets(workbook)
            workbook.save(self.control_file)
            Logger.info(f"Control workbook updated: {self.control_file}")

    def filter_pending_issues(self, issues):
        status_map = self.get_status_map()
        pending_issues = [issue for issue in issues if status_map.get(issue.key, STATUS_PENDING) != STATUS_MIGRATED]
        Logger.info(f"Pending issues to process: {len(pending_issues)}")
        return pending_issues

    def mark_in_progress(self, issue_key):
        self._update_progress_status(issue_key, STATUS_IN_PROGRESS, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), None, "Processing started.", True)

    def mark_migrated(self, issue_key, message):
        self._update_progress_status(issue_key, STATUS_MIGRATED, None, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), message, False)

    def mark_failed(self, issue_key, message):
        self._update_progress_status(issue_key, STATUS_FAILED, None, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), message, False)

    def append_migration_result(self, migration_result):
        with self.lock:
            workbook = self._load_or_create_workbook()
            report_sheet = self._get_or_create_sheet(workbook, MIGRATION_REPORT_SHEET_NAME, self.REPORT_HEADERS)
            ExcelHelper.append_non_empty_row(report_sheet, [migration_result.issue_key, migration_result.status, migration_result.message, migration_result.attachments_count, migration_result.issue_folder, migration_result.excel_file, migration_result.json_file, migration_result.attachment_hashes_file, migration_result.sha256_excel, migration_result.sha256_json, migration_result.processed_at, migration_result.script_version, migration_result.jql_used, migration_result.workers_used])
            ExcelHelper.remove_empty_rows(report_sheet)
            ExcelHelper.format_sheet(report_sheet)
            workbook.save(self.control_file)

    def get_status_map(self):
        with self.lock:
            if not self.control_file.exists(): return {}
            workbook = load_workbook(self.control_file)
            if PROGRESS_CONTROL_SHEET_NAME not in workbook.sheetnames: return {}
            sheet = workbook[PROGRESS_CONTROL_SHEET_NAME]
            columns = self._get_column_indexes(sheet, self.PROGRESS_HEADERS)
            issue_col, status_col = columns.get("Issue Key"), columns.get("Migration Status")
            status_map = {}
            if issue_col is None or status_col is None: return {}
            for row_index in range(2, sheet.max_row + 1):
                issue_key = sheet.cell(row=row_index, column=issue_col).value
                status = sheet.cell(row=row_index, column=status_col).value
                if issue_key: status_map[str(issue_key)] = status or STATUS_PENDING
            return status_map

    def _update_progress_status(self, issue_key, migration_status, started_at, finished_at, message, increment_attempts):
        with self.lock:
            workbook = self._load_or_create_workbook()
            sheet = self._get_or_create_sheet(workbook, PROGRESS_CONTROL_SHEET_NAME, self.PROGRESS_HEADERS)
            columns = self._get_column_indexes(sheet, self.PROGRESS_HEADERS)
            row_index = self._find_issue_row(sheet, issue_key, columns)
            if row_index is None:
                row_index = sheet.max_row + 1
                sheet.cell(row=row_index, column=columns["Issue Key"]).value = issue_key
                sheet.cell(row=row_index, column=columns["Migration Status"]).value = STATUS_PENDING
                sheet.cell(row=row_index, column=columns["Attempts"]).value = 0
            sheet.cell(row=row_index, column=columns["Migration Status"]).value = migration_status
            sheet.cell(row=row_index, column=columns["Message"]).value = HtmlCleaner.clean(message)
            if started_at is not None: sheet.cell(row=row_index, column=columns["Last Started At"]).value = started_at
            if finished_at is not None: sheet.cell(row=row_index, column=columns["Last Finished At"]).value = finished_at
            if increment_attempts:
                attempts_cell = sheet.cell(row=row_index, column=columns["Attempts"])
                attempts_cell.value = int(attempts_cell.value or 0) + 1
            ExcelHelper.remove_empty_rows(sheet)
            ExcelHelper.format_sheet(sheet)
            workbook.save(self.control_file)

    def _refresh_found_issues_sheet(self, sheet, issues):
        ExcelHelper.clear_sheet_keep_headers(sheet, self.FOUND_HEADERS)
        for issue in issues:
            ExcelHelper.append_non_empty_row(sheet, [issue.key, HtmlCleaner.clean(IssueService.get_issue_summary(issue)), HtmlCleaner.clean(IssueService.get_issue_status(issue)), HtmlCleaner.clean(IssueService.get_issue_type(issue)), HtmlCleaner.clean(IssueService.get_issue_created_date(issue)), HtmlCleaner.clean(IssueService.get_issue_updated_date(issue)), HtmlCleaner.clean(IssueService.get_issue_assignee(issue)), HtmlCleaner.clean(IssueService.get_issue_reporter(issue)), HtmlCleaner.clean(IssueService.get_issue_priority(issue))])

    def _append_missing_progress_rows(self, sheet, issues):
        existing_keys = self._get_existing_issue_keys(sheet)
        for issue in issues:
            if issue.key not in existing_keys:
                ExcelHelper.append_non_empty_row(sheet, [issue.key, HtmlCleaner.clean(IssueService.get_issue_summary(issue)), HtmlCleaner.clean(IssueService.get_issue_status(issue)), STATUS_PENDING, 0, "", "", ""])

    def _load_or_create_workbook(self):
        if self.control_file.exists(): return load_workbook(self.control_file)
        workbook = Workbook()
        workbook.remove(workbook.active)
        return workbook

    def _get_or_create_sheet(self, workbook, sheet_name, headers):
        if sheet_name in workbook.sheetnames:
            sheet = workbook[sheet_name]
            self._ensure_headers(sheet, headers)
            return sheet
        sheet = workbook.create_sheet(sheet_name)
        sheet.append(headers)
        return sheet

    def _ensure_headers(self, sheet, headers):
        if sheet.max_row < 1:
            sheet.append(headers)
            return
        for index, header in enumerate(headers, start=1):
            if sheet.cell(row=1, column=index).value != header:
                sheet.cell(row=1, column=index).value = header

    def _get_existing_issue_keys(self, sheet):
        columns = self._get_column_indexes(sheet, self.PROGRESS_HEADERS)
        issue_col = columns.get("Issue Key")
        if issue_col is None: return set()
        keys = set()
        for row_index in range(2, sheet.max_row + 1):
            value = sheet.cell(row=row_index, column=issue_col).value
            if value: keys.add(str(value))
        return keys

    def _get_column_indexes(self, sheet, headers):
        self._ensure_headers(sheet, headers)
        return {str(cell.value): cell.column for cell in sheet[1] if cell.value}

    def _find_issue_row(self, sheet, issue_key, columns):
        issue_col = columns.get("Issue Key")
        for row_index in range(2, sheet.max_row + 1):
            if str(sheet.cell(row=row_index, column=issue_col).value) == str(issue_key): return row_index
        return None

    def _format_all_sheets(self, workbook):
        for sheet in workbook.worksheets:
            ExcelHelper.remove_empty_rows(sheet)
            ExcelHelper.format_sheet(sheet)
