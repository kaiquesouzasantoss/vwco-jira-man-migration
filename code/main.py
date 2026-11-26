from config.settings import JIRA_URL, JIRA_USERNAME, JIRA_PASSWORD, RUN_SINGLE_ISSUE, SINGLE_ISSUE_KEY, validate_required_settings
from clients.jira_client import JiraClient
from managers.path_manager import PathManager
from services.control_workbook_service import ControlWorkbookService
from services.extraction_menu_service import ExtractionMenuService
from services.migration_service import MigrationService
from utils.logger import Logger


def main():
    Logger.info("Starting Jira extraction process.")
    selected_extraction = ExtractionMenuService.choose_extraction()
    if selected_extraction is None:
        Logger.warning("No extraction selected. Process finished.")
        Logger.flush_to_file()
        return
    Logger.info(f"Selected extraction: {selected_extraction.key}")
    path_manager = PathManager(extraction_key=selected_extraction.key)
    path_manager.create_base_structure()
    execution_log_file = path_manager.get_execution_log_file()
    Logger.set_log_file(execution_log_file)
    Logger.info(f"Execution log file: {execution_log_file}")
    try:
        validate_required_settings()
        jira_client = JiraClient(jira_url=JIRA_URL, username=JIRA_USERNAME, password=JIRA_PASSWORD)
        jira_client.connect()
        if RUN_SINGLE_ISSUE:
            Logger.warning(f"Running in single issue test mode: {SINGLE_ISSUE_KEY}")
            issues = [jira_client.get_issue(issue_key=SINGLE_ISSUE_KEY)]
            jql_used = f"key = {SINGLE_ISSUE_KEY}"
        else:
            issues = jira_client.search_all_issues(jql=selected_extraction.jql)
            jql_used = selected_extraction.jql
        control_workbook_service = ControlWorkbookService(control_file=path_manager.get_control_workbook_file())
        control_workbook_service.initialize_or_update_workbook(issues=issues)
        issues_to_process = control_workbook_service.filter_pending_issues(issues=issues)
        if not issues_to_process:
            Logger.success("No pending issues found. Everything is already migrated.")
            Logger.info(f"Control workbook: {path_manager.get_control_workbook_file()}")
            return
        migration_service = MigrationService(jira_client=jira_client, path_manager=path_manager, control_workbook_service=control_workbook_service, jql_used=jql_used)
        migration_service.migrate_issues(issues=issues_to_process)
        Logger.success("Jira extraction process finished.")
        Logger.info(f"Extraction folder: {path_manager.extraction_folder}")
        Logger.info(f"Control workbook: {path_manager.get_control_workbook_file()}")
        Logger.info(f"Execution log file: {execution_log_file}")
    except Exception as exception:
        Logger.error("Jira extraction process failed unexpectedly.")
        Logger.error(str(exception))
        raise
    finally:
        Logger.flush_to_file()


if __name__ == "__main__":
    main()
