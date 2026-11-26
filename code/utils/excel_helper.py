from core.common_imports import Font, PatternFill, Alignment, get_column_letter, json
from utils.html_cleaner import HtmlCleaner

class ExcelHelper:
    @staticmethod
    def normalize_cell_value(value):
        if value is None:
            return ""
        if isinstance(value, (dict, list, tuple, set)):
            return HtmlCleaner.clean(json.dumps(value, ensure_ascii=False, default=str))
        if isinstance(value, str):
            return HtmlCleaner.clean(value)
        return value

    @staticmethod
    def append_non_empty_row(sheet, row):
        normalized_row = [ExcelHelper.normalize_cell_value(value) for value in row]
        if any(str(value).strip() != "" for value in normalized_row):
            sheet.append(normalized_row)

    @staticmethod
    def clear_sheet_keep_headers(sheet, headers):
        sheet.delete_rows(1, sheet.max_row)
        sheet.append(headers)

    @staticmethod
    def remove_empty_rows(sheet):
        rows_to_delete = []
        for row_index in range(1, sheet.max_row + 1):
            if not any(cell.value is not None and str(cell.value).strip() != "" for cell in sheet[row_index]):
                rows_to_delete.append(row_index)
        for row_index in reversed(rows_to_delete):
            sheet.delete_rows(row_index, 1)

    @staticmethod
    def format_sheet(sheet, max_width=120):
        if sheet.max_row < 1:
            return
        header_fill = PatternFill(start_color="1F4E78", end_color="1F4E78", fill_type="solid")
        header_font = Font(color="FFFFFF", bold=True)
        for cell in sheet[1]:
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal="center", vertical="center")
        for column_cells in sheet.columns:
            max_length = 0
            column_letter = get_column_letter(column_cells[0].column)
            for cell in column_cells:
                if cell.value is not None:
                    max_length = max(max_length, len(str(cell.value)))
            sheet.column_dimensions[column_letter].width = min(max_length + 2, max_width)
        for row in sheet.iter_rows():
            for cell in row:
                cell.alignment = Alignment(vertical="top", wrap_text=True)
        sheet.freeze_panes = "A2"
        sheet.auto_filter.ref = sheet.dimensions
