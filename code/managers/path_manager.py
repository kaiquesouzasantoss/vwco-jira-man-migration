from core.common_imports import Path, datetime
from config.settings import BASE_OUTPUT_FOLDER, RUN_FOLDER_NAME, USE_TIMESTAMPED_RUN_FOLDER
from core.constants import RUN_FOLDER_PREFIX, CONTROL_FOLDER_NAME, ISSUES_FOLDER_NAME, DATA_FOLDER_NAME, ATTACHMENTS_FOLDER_NAME, EXECUTION_LOG_FILE_SUFFIX
from managers.file_name_manager import FileNameManager

class PathManager:
    def __init__(self, extraction_key):
        self.extraction_key = extraction_key
        folder_name = f"{RUN_FOLDER_PREFIX}_{datetime.now().strftime('%Y%m%d_%H%M%S')}" if USE_TIMESTAMPED_RUN_FOLDER else RUN_FOLDER_NAME
        self.run_folder = Path(BASE_OUTPUT_FOLDER) / folder_name
        self.extraction_folder = self.run_folder / FileNameManager.sanitize_name(extraction_key)
        self.control_folder = self.extraction_folder / CONTROL_FOLDER_NAME
        self.issues_folder = self.extraction_folder / ISSUES_FOLDER_NAME

    def create_base_structure(self):
        self.control_folder.mkdir(parents=True, exist_ok=True)
        self.issues_folder.mkdir(parents=True, exist_ok=True)

    def get_issue_folder(self, issue_key, issue_summary=None):
        issue_folder = self.issues_folder / FileNameManager.build_issue_base_name(issue_key, issue_summary)
        issue_folder.mkdir(parents=True, exist_ok=True)
        return issue_folder

    def get_issue_data_folder(self, issue_key, issue_summary=None):
        data_folder = self.get_issue_folder(issue_key, issue_summary) / DATA_FOLDER_NAME
        data_folder.mkdir(parents=True, exist_ok=True)
        return data_folder

    def get_issue_attachments_folder(self, issue_key, issue_summary=None):
        attachments_folder = self.get_issue_folder(issue_key, issue_summary) / ATTACHMENTS_FOLDER_NAME
        attachments_folder.mkdir(parents=True, exist_ok=True)
        return attachments_folder

    def get_issue_excel_file(self, issue_key, issue_summary=None):
        return self.get_issue_data_folder(issue_key, issue_summary) / FileNameManager.build_issue_excel_file_name(issue_key, issue_summary)

    def get_issue_json_file(self, issue_key, issue_summary=None):
        return self.get_issue_data_folder(issue_key, issue_summary) / FileNameManager.build_issue_json_file_name(issue_key, issue_summary)

    def get_attachment_hashes_file(self, issue_key, issue_summary=None):
        return self.get_issue_data_folder(issue_key, issue_summary) / FileNameManager.build_attachment_hashes_file_name(issue_key, issue_summary)

    def get_control_workbook_file(self):
        return self.control_folder / FileNameManager.build_control_workbook_file_name(self.extraction_key)

    def get_execution_log_file(self):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return self.control_folder / f"{self.extraction_key}_{timestamp}_{EXECUTION_LOG_FILE_SUFFIX}"
