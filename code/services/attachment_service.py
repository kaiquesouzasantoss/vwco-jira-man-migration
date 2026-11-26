from config.settings import (
    MAX_RETRIES,
    RETRY_BACKOFF_SECONDS
)
from core.common_imports import time
from managers.file_name_manager import FileNameManager
from utils.logger import Logger

class AttachmentService:
    def __init__(self, authenticated_session, verify_ssl=True):
        self.session = authenticated_session
        self.verify_ssl = verify_ssl

    def download_attachments(self, issue, attachments_folder):
        attachments = getattr(issue.fields, "attachment", [])
        attachments_folder.mkdir(parents=True, exist_ok=True)
        if not attachments:
            Logger.info(f"No attachments found for {issue.key}.")
            return []
        downloaded_files = []
        issue_summary = getattr(issue.fields, "summary", "")
        for index, attachment in enumerate(attachments, start=1):
            file_name = FileNameManager.build_attachment_file_name(index, attachment.filename, issue.key, issue_summary)
            target_file = self._get_unique_file_path(attachments_folder, file_name)
            Logger.info(f"Downloading attachment: {attachment.filename}")
            self._download_with_retry(attachment.content, target_file)
            downloaded_files.append(target_file)
            Logger.success(f"Attachment saved: {target_file}")

        Logger.info(
            f"Issue {issue.key}: "
            f"{len(attachments)} attachments found, "
            f"{len(downloaded_files)} successfully downloaded."
        )

        if len(attachments) != len(downloaded_files):
            Logger.error(
                f"Issue {issue.key}: "
                f"attachment count mismatch between "
                f"found and downloaded files."
            )

        return downloaded_files

    def _download_with_retry(self, url, target_file):
        last_exception = None

        for attempt in range(1, MAX_RETRIES + 1):
            try:
                response = self.session.get(
                    url,
                    stream=True
                )

                response.raise_for_status()

                with open(target_file, "wb") as file:
                    for chunk in response.iter_content(
                            chunk_size=1024 * 1024
                    ):
                        if chunk:
                            file.write(chunk)

                return

            except Exception as exception:
                last_exception = exception

                Logger.warning(
                    f"Attachment download attempt "
                    f"{attempt}/{MAX_RETRIES} failed: {exception}"
                )

                if attempt < MAX_RETRIES:
                    time.sleep(
                        RETRY_BACKOFF_SECONDS * attempt
                    )

        raise last_exception

    def _get_unique_file_path(self, folder, file_name):
        file_path = folder / file_name
        if not file_path.exists(): return file_path
        stem, suffix, counter = file_path.stem, file_path.suffix, 1
        while True:
            new_file_path = folder / f"{stem}_{counter}{suffix}"
            if not new_file_path.exists(): return new_file_path
            counter += 1
