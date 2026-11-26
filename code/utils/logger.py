from core.common_imports import datetime
from utils.sensitive_data import SensitiveDataSanitizer

class Logger:
    _log_lines = []
    _log_file = None

    @staticmethod
    def set_log_file(log_file):
        Logger._log_file = log_file
        Logger._log_file.parent.mkdir(parents=True, exist_ok=True)
        if not Logger._log_file.exists():
            Logger._log_file.write_text("", encoding="utf-8")
        Logger.flush_to_file()

    @staticmethod
    def info(message):
        Logger._write("INFO", message)

    @staticmethod
    def success(message):
        Logger._write("SUCCESS", message)

    @staticmethod
    def warning(message):
        Logger._write("WARNING", message)

    @staticmethod
    def error(message):
        Logger._write("ERROR", message)

    @staticmethod
    def flush_to_file():
        if Logger._log_file is None:
            return
        content = "\n".join(Logger._log_lines)
        if content:
            Logger._log_file.write_text(content + "\n", encoding="utf-8")

    @staticmethod
    def _write(level, message):
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_line = f"[{current_time}] [{level}] {SensitiveDataSanitizer.sanitize_text(message)}"
        Logger._log_lines.append(log_line)
        print(log_line)
        if Logger._log_file is not None:
            with open(Logger._log_file, "a", encoding="utf-8") as file:
                file.write(log_line + "\n")
