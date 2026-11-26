from config.settings import EXTRACTION_CONFIGS
from models.extraction_config import ExtractionConfig
from utils.logger import Logger

class ExtractionMenuService:
    @staticmethod
    def choose_extraction():
        extraction_options = ExtractionMenuService._build_options()
        print()
        print("=" * 80)
        print("Jira Extraction Menu")
        print("=" * 80)
        for index, extraction in enumerate(extraction_options, start=1):
            print(f"{index}. {extraction.label} - {extraction.description}")
        print("0. Exit")
        print("=" * 80)
        while True:
            selected_value = input("Choose the extraction option: ").strip()
            if selected_value == "0":
                return None
            if not selected_value.isdigit():
                Logger.warning("Invalid option. Type a number from the menu.")
                continue
            selected_index = int(selected_value)
            if 1 <= selected_index <= len(extraction_options):
                return extraction_options[selected_index - 1]
            Logger.warning("Invalid option. Type a valid menu number.")

    @staticmethod
    def _build_options():
        return [ExtractionConfig(key=k, label=v.get("label", k), description=v.get("description", ""), jql=v.get("jql", "")) for k, v in EXTRACTION_CONFIGS.items()]
