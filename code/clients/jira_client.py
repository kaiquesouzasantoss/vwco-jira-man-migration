from core.common_imports import JIRA, urllib3, socket, requests, JIRAError, time
from config.settings import VERIFY_SSL, JIRA_CA_BUNDLE, PAGE_SIZE, API_PAGE_SIZE, MAX_RETRIES, RETRY_BACKOFF_SECONDS
from utils.logger import Logger

class JiraClient:
    def __init__(self, jira_url, username, password):
        self.jira_url = jira_url.rstrip("/")
        self.username = username
        self.password = password
        self.client = None
        self.verify = self._build_verify_value()
        if self.verify is False:
            urllib3.disable_warnings()
            Logger.warning("SSL verification is disabled. Use only when approved for internal environments.")

    def _build_verify_value(self):
        if VERIFY_SSL is False:
            return False
        return JIRA_CA_BUNDLE if JIRA_CA_BUNDLE else True

    def connect(self):
        Logger.info("Connecting to Jira.")
        self._validate_dns_resolution()
        try:
            self.client = JIRA(server=self.jira_url, basic_auth=(self.username, self.password), options={"verify": self.verify})
            server_info = self._retry(lambda: self.client.server_info(), "server_info")
            Logger.success("Jira connection established successfully.")
            Logger.info(f"Server: {server_info.get('serverTitle')}")
            Logger.info(f"Version: {server_info.get('version')}")
        except JIRAError as exception:
            self._handle_jira_error(exception)
        except requests.exceptions.ConnectionError as exception:
            Logger.error("Could not connect to Jira.")
            Logger.error(str(exception))
            raise
        except Exception as exception:
            Logger.error("Unexpected error while connecting to Jira.")
            Logger.error(str(exception))
            raise

    def _handle_jira_error(self, exception):
        status_code = getattr(exception, "status_code", None)
        url = getattr(exception, "url", "")
        response = getattr(exception, "response", None)
        headers = getattr(response, "headers", {}) if response is not None else {}
        Logger.error("Jira returned an authentication or API error.")
        if status_code: Logger.error(f"HTTP Status Code: {status_code}")
        if url: Logger.error(f"URL: {url}")
        login_reason = headers.get("X-Seraph-LoginReason", "")
        authenticate_header = headers.get("WWW-Authenticate", "")
        if login_reason: Logger.error(f"Login Reason: {login_reason}")
        if authenticate_header: Logger.error(f"Authentication Header: {authenticate_header}")
        if status_code == 401: Logger.error("Authentication failed. Check environment variables JIRA_USERNAME and JIRA_PASSWORD.")
        raise exception

    def _validate_dns_resolution(self):
        host = self._extract_host_from_url()
        Logger.info(f"Validating DNS resolution for host: {host}")
        try:
            ip_address = socket.gethostbyname(host)
            Logger.success(f"DNS resolved successfully: {host} -> {ip_address}")
        except socket.gaierror as exception:
            Logger.error(f"DNS resolution failed for host: {host}")
            raise exception

    def _extract_host_from_url(self):
        url = self.jira_url.replace("http://", "").replace("https://", "")
        return url.split("/")[0].split(":")[0]

    def _retry(self, operation, operation_name):
        last_exception = None
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                return operation()
            except Exception as exception:
                last_exception = exception
                Logger.warning(f"Attempt {attempt}/{MAX_RETRIES} failed for {operation_name}: {exception}")
                if attempt < MAX_RETRIES:
                    time.sleep(RETRY_BACKOFF_SECONDS * attempt)
        raise last_exception

    def search_all_issues(self, jql):
        Logger.info(f"Searching Jira issues with JQL: {jql}")
        all_issues = []
        start_at = 0
        while True:
            issues = self._retry(lambda: self.client.search_issues(jql_str=jql, startAt=start_at, maxResults=PAGE_SIZE, fields="*all", expand="changelog,renderedFields,names"), f"search_issues startAt={start_at}")
            if not issues:
                break
            all_issues.extend(issues)
            Logger.info(f"Loaded issues: {len(all_issues)}")
            if len(issues) < PAGE_SIZE:
                break
            start_at += PAGE_SIZE
        Logger.success(f"Total issues found: {len(all_issues)}")
        return all_issues

    def get_issue(self, issue_key):
        return self._retry(lambda: self.client.issue(issue_key, fields="*all", expand="changelog,renderedFields,names"), f"get_issue {issue_key}")

    def get_field_name_map(self):
        fields = self._retry(lambda: self.client.fields(), "fields")
        return {field.get("id"): field.get("name") for field in fields if field.get("id")}

    def get_all_comments(self, issue_key):
        return self._get_paginated(issue_key, "comment", "comments")

    def get_all_worklogs(self, issue_key):
        return self._get_paginated(issue_key, "worklog", "worklogs")

    def _get_paginated(self, issue_key, resource, collection_key):
        records = []
        start_at = 0
        while True:
            url = f"{self.jira_url}/rest/api/2/issue/{issue_key}/{resource}"
            response = self._retry(
                lambda: self.client._session.get(
                    url,
                    params={
                        "startAt": start_at,
                        "maxResults": API_PAGE_SIZE
                    }
                ),
                f"{resource} {issue_key} startAt={start_at}"
            )
            response.raise_for_status()
            data = response.json()
            batch = data.get(collection_key, [])
            records.extend(batch)
            start_at += len(batch)
            total = data.get("total", len(records))
            if len(records) >= total or not batch:
                break
        return records

    def create_authenticated_session(self):
        return self.client._session
