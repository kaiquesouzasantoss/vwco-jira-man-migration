from core.common_imports import dataclass

@dataclass
class MigrationResult:
    issue_key: str
    status: str
    message: str
    attachments_count: int
    issue_folder: str
    excel_file: str
    json_file: str
    attachment_hashes_file: str
    sha256_excel: str
    sha256_json: str
    processed_at: str
    script_version: str
    jql_used: str
    workers_used: int
