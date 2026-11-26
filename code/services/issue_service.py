class IssueService:
    @staticmethod
    def get_issue_summary(issue):
        try: return issue.fields.summary or ""
        except Exception: return ""
    @staticmethod
    def get_issue_status(issue):
        try: return issue.fields.status.name or ""
        except Exception: return ""
    @staticmethod
    def get_issue_type(issue):
        try: return issue.fields.issuetype.name or ""
        except Exception: return ""
    @staticmethod
    def get_issue_created_date(issue):
        try: return issue.fields.created or ""
        except Exception: return ""
    @staticmethod
    def get_issue_updated_date(issue):
        try: return issue.fields.updated or ""
        except Exception: return ""
    @staticmethod
    def get_issue_assignee(issue):
        try: return issue.fields.assignee.displayName if issue.fields.assignee else ""
        except Exception: return ""
    @staticmethod
    def get_issue_reporter(issue):
        try: return issue.fields.reporter.displayName if issue.fields.reporter else ""
        except Exception: return ""
    @staticmethod
    def get_issue_priority(issue):
        try: return issue.fields.priority.name if issue.fields.priority else ""
        except Exception: return ""
    @staticmethod
    def get_issue_parent_key(issue):
        try:
            parent = getattr(issue.fields, "parent", None)
            return parent.key if parent else ""
        except Exception: return ""
    @staticmethod
    def get_issue_parent_summary(issue):
        try:
            parent = getattr(issue.fields, "parent", None)
            return parent.fields.summary if parent else ""
        except Exception: return ""
    @staticmethod
    def get_issue_is_subtask(issue):
        try: return "Sim" if issue.fields.issuetype.subtask else "Não"
        except Exception: return "Não"