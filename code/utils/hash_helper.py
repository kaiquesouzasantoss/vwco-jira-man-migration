from core.common_imports import hashlib

class HashHelper:
    @staticmethod
    def sha256_file(file_path):
        if file_path is None or not file_path or not file_path.exists():
            return ""
        sha256 = hashlib.sha256()
        with open(file_path, "rb") as file:
            for chunk in iter(lambda: file.read(1024 * 1024), b""):
                sha256.update(chunk)
        return sha256.hexdigest()

    @staticmethod
    def write_hash_manifest(files, output_file):
        output_file.parent.mkdir(parents=True, exist_ok=True)
        lines = []
        for file_path in files:
            if file_path and file_path.exists():
                lines.append(f"{HashHelper.sha256_file(file_path)}  {file_path.name}")
        output_file.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")
        return output_file
