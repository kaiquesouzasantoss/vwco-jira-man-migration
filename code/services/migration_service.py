from config.settings import CREATE_RAW_JSON, ENABLE_PARALLEL_EXECUTION, MAX_WORKERS, SAFE_MAX_WORKERS_LIMIT, REFRESH_ISSUE_BEFORE_EXPORT, DOWNLOAD_ATTACHMENTS, SCRIPT_VERSION
from core.common_imports import datetime, ThreadPoolExecutor, as_completed
from core.constants import STATUS_MIGRATED, STATUS_FAILED
from models.migration_result import MigrationResult
from exporters.excel_exporter import ExcelExporter
from exporters.json_exporter import JsonExporter
from services.attachment_service import AttachmentService
from utils.hash_helper import HashHelper
from utils.logger import Logger

class MigrationService:
    def __init__(self, jira_client, path_manager, control_workbook_service, jql_used):
        self.jira_client = jira_client
        self.path_manager = path_manager
        self.control_workbook_service = control_workbook_service
        self.jql_used = jql_used
        self.workers_used = min(MAX_WORKERS, SAFE_MAX_WORKERS_LIMIT)

    def migrate_issues(self, issues):
        field_name_map = self.jira_client.get_field_name_map()
        excel_exporter = ExcelExporter(field_name_map=field_name_map)
        json_exporter = JsonExporter()
        
        attachment_service = AttachmentService(self.jira_client.create_authenticated_session(), verify_ssl=self.jira_client.verify)

        self._print_found_issues(issues)
        if ENABLE_PARALLEL_EXECUTION and len(issues) > 1:
            self._migrate_issues_parallel(issues, excel_exporter, json_exporter, attachment_service)
        else:
            self._migrate_issues_sequential(issues, excel_exporter, json_exporter, attachment_service)

    def _migrate_issues_parallel(self, issues, excel_exporter, json_exporter, attachment_service):
        safe_max_workers = min(MAX_WORKERS, SAFE_MAX_WORKERS_LIMIT)
        Logger.warning(f"Parallel execution enabled with max workers: {safe_max_workers}")
        with ThreadPoolExecutor(max_workers=safe_max_workers) as executor:
            future_map = {executor.submit(self._migrate_single_issue, issue_summary, excel_exporter, json_exporter, attachment_service): issue_summary.key for issue_summary in issues}
            for future in as_completed(future_map):
                issue_key = future_map[future]
                try:
                    future.result()
                except Exception as exception:
                    error_message = str(exception)
                    Logger.error(f"Unexpected parallel failure for issue {issue_key}.")
                    Logger.error(error_message)
                    self.control_workbook_service.mark_failed(issue_key, error_message)
                    self.control_workbook_service.append_migration_result(self._build_failure_result(issue_key, error_message))

    def _migrate_issues_sequential(self, issues, excel_exporter, json_exporter, attachment_service):
        for issue_summary in issues:
            self._migrate_single_issue(issue_summary, excel_exporter, json_exporter, attachment_service)

    def _migrate_single_issue(self, issue_summary, excel_exporter, json_exporter, attachment_service):
        issue_key = issue_summary.key
        self.control_workbook_service.mark_in_progress(issue_key)
        try:
            Logger.info("=" * 80)
            Logger.info(f"Processing issue: {issue_key}")
            issue = self.jira_client.get_issue(issue_key) if REFRESH_ISSUE_BEFORE_EXPORT else issue_summary
            issue_summary_text = getattr(issue.fields, "summary", "")
            issue_folder = self.path_manager.get_issue_folder(issue.key, issue_summary_text)
            issue_excel_file = self.path_manager.get_issue_excel_file(issue.key, issue_summary_text)
            issue_json_file = self.path_manager.get_issue_json_file(issue.key, issue_summary_text)
            attachment_hashes_file = self.path_manager.get_attachment_hashes_file(issue.key, issue_summary_text)
            comments = self.jira_client.get_all_comments(issue.key)
            worklogs = self.jira_client.get_all_worklogs(issue.key)
            excel_exporter.export_issue_to_excel(issue, issue_excel_file, comments=comments, worklogs=worklogs)
            if CREATE_RAW_JSON:
                json_exporter.export_issue_raw_data(issue, issue_json_file)
            else:
                issue_json_file = None
            downloaded_files = []
            if DOWNLOAD_ATTACHMENTS:
                attachments_folder = self.path_manager.get_issue_attachments_folder(issue.key, issue_summary_text)
                downloaded_files = attachment_service.download_attachments(issue, attachments_folder)
            HashHelper.write_hash_manifest(downloaded_files, attachment_hashes_file)
            sha256_excel = HashHelper.sha256_file(issue_excel_file)
            sha256_json = HashHelper.sha256_file(issue_json_file) if issue_json_file else ""
            success_message = "Issue data, audit data and attachments exported successfully."
            self.control_workbook_service.mark_migrated(issue.key, success_message)
            Logger.success(f"Issue migrated successfully: {issue.key}")
            result = MigrationResult(issue.key, STATUS_MIGRATED, success_message, len(downloaded_files), str(issue_folder), str(issue_excel_file), str(issue_json_file or ""), str(attachment_hashes_file), sha256_excel, sha256_json, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), SCRIPT_VERSION, self.jql_used, self.workers_used)
            self.control_workbook_service.append_migration_result(result)
            return result
        except Exception as exception:
            error_message = str(exception)
            self.control_workbook_service.mark_failed(issue_key, error_message)
            Logger.error(f"Failed to migrate issue {issue_key}.")
            Logger.error(error_message)
            result = self._build_failure_result(issue_key, error_message)
            self.control_workbook_service.append_migration_result(result)
            return result

    def _build_failure_result(self, issue_key, error_message):
        return MigrationResult(issue_key, STATUS_FAILED, error_message, 0, "", "", "", "", "", "", datetime.now().strftime("%Y-%m-%d %H:%M:%S"), SCRIPT_VERSION, self.jql_used, self.workers_used)

    def _print_found_issues(self, issues):
        Logger.info("=" * 80)
        Logger.info("Issues pending for this execution:")
        for issue in issues:
            Logger.info(issue.key)
        Logger.info("=" * 80)
