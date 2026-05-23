import json
import re
import unicodedata

from fastapi import HTTPException
from openpyxl import load_workbook

from app.models.admin import Brand, Category, Product, Tag
from app.schemas.product_import import ProductImportParseResult, ProductImportParsedRow


class ProductImportParserService:
    EXPECTED_HEADERS = [
        "name",
        "category_name",
        "brand_name",
        "desc",
        "tag_names",
        "product_code_custom",
        "status",
        "order",
        "detail_text",
        "detail_description_json",
    ]
    DISPLAY_HEADERS = {
        "name": "名称",
        "category_name": "所属分类",
        "brand_name": "所属品牌",
        "desc": "简介",
        "tag_names": "标签",
        "product_code_custom": "自定义识别码",
        "status": "上架状态",
        "order": "排序",
        "detail_text": "详情文本",
        "detail_description_json": "结构化详情JSON",
    }
    HEADER_ALIASES = {
        key: [key, label]
        for key, label in DISPLAY_HEADERS.items()
    }
    HEADER_LOOKUP = {
        alias: key
        for key, aliases in HEADER_ALIASES.items()
        for alias in aliases
    }
    REQUIRED_HEADERS = ["name", "category_name", "brand_name"]
    STATUS_TRUE_VALUES = {"true", "1", "是", "yes"}
    STATUS_FALSE_VALUES = {"false", "0", "否", "no"}

    async def parse(self, workbook_path: str) -> ProductImportParseResult:
        workbook = load_workbook(workbook_path, read_only=True, data_only=True)
        try:
            worksheet = workbook[workbook.sheetnames[0]]
            rows = list(worksheet.iter_rows(values_only=True))
            if not rows:
                return ProductImportParseResult(headers=[], rows=[], total_rows=0, valid_rows=0, invalid_rows=0)

            headers = [self._normalize_cell_value(value) for value in rows[0]]
            header_index = {}
            for index, header in enumerate(headers):
                if not header:
                    continue
                header_index[self.HEADER_LOOKUP.get(header, header)] = index
            missing_headers = [header for header in self.REQUIRED_HEADERS if header not in header_index]
            if missing_headers:
                missing_labels = [self.DISPLAY_HEADERS.get(header, header) for header in missing_headers]
                raise HTTPException(status_code=400, detail=f"缺少必填表头: {', '.join(missing_labels)}")

            categories = {item.name: item.id for item in await Category.all()}
            tags = {item.name: item.id for item in await Tag.all()}
            brands = await Brand.all().prefetch_related("categories")
            brand_map = {brand.name: brand for brand in brands}
            existing_products = {
                self._normalize_name(name)
                for name in await Product.all().values_list("name", flat=True)
                if self._normalize_name(name)
            }

            parsed_rows: list[ProductImportParsedRow] = []
            valid_rows = 0
            invalid_rows = 0

            for row_no, values in enumerate(rows[1:], start=2):
                if self._is_empty_row(values):
                    continue

                row = self._build_row(row_no=row_no, values=values, header_index=header_index)
                self._validate_row(
                    row,
                    categories=categories,
                    brand_map=brand_map,
                    tags=tags,
                    existing_products=existing_products,
                )
                if row.errors:
                    invalid_rows += 1
                else:
                    valid_rows += 1
                parsed_rows.append(row)

            return ProductImportParseResult(
                headers=headers,
                rows=parsed_rows,
                total_rows=len(parsed_rows),
                valid_rows=valid_rows,
                invalid_rows=invalid_rows,
            )
        finally:
            workbook.close()

    def _build_row(self, *, row_no: int, values, header_index: dict[str, int]) -> ProductImportParsedRow:
        name = self._get_cell(values, header_index, "name")
        category_name = self._get_cell(values, header_index, "category_name")
        brand_name = self._get_cell(values, header_index, "brand_name")
        detail_text = self._get_cell(values, header_index, "detail_text")
        detail_description_json = self._get_cell(values, header_index, "detail_description_json")

        status, status_error = self._parse_status(self._get_cell(values, header_index, "status"))
        order, order_error = self._parse_order(self._get_cell(values, header_index, "order"))
        detail_description, detail_error = self._parse_detail_description(detail_text, detail_description_json)

        row = ProductImportParsedRow(
            row_no=row_no,
            name=name,
            category_name=category_name,
            brand_name=brand_name,
            desc=self._empty_to_none(self._get_cell(values, header_index, "desc")),
            tag_names=self._parse_tag_names(self._get_cell(values, header_index, "tag_names")),
            product_code_custom=self._empty_to_none(self._get_cell(values, header_index, "product_code_custom")),
            status=status,
            order=order,
            detail_description=detail_description,
        )
        if status_error:
            row.errors.append(status_error)
        if order_error:
            row.errors.append(order_error)
        if detail_error:
            row.errors.append(detail_error)
        return row

    def _validate_row(
        self,
        row: ProductImportParsedRow,
        *,
        categories: dict[str, int],
        brand_map: dict[str, Brand],
        tags: dict[str, int],
        existing_products: set[str],
    ) -> None:
        if not row.name:
            row.errors.append("名称不能为空")
        if not row.category_name:
            row.errors.append("所属分类不能为空")
        if not row.brand_name:
            row.errors.append("所属品牌不能为空")

        category_id = categories.get(row.category_name)
        if row.category_name and category_id is None:
            row.errors.append("所属分类不存在")
        row.category_id = category_id

        brand = brand_map.get(row.brand_name)
        if row.brand_name and brand is None:
            row.errors.append("所属品牌不存在")
        if brand is not None:
            row.brand_id = brand.id
            category_ids = {category.id for category in brand.categories}
            if category_id is not None and category_id not in category_ids:
                row.errors.append("所属品牌不属于所选分类")

        resolved_tag_ids: list[int] = []
        missing_tags: list[str] = []
        for tag_name in row.tag_names:
            tag_id = tags.get(tag_name)
            if tag_id is None:
                missing_tags.append(tag_name)
                continue
            resolved_tag_ids.append(tag_id)
        if missing_tags:
            row.errors.append(f"以下标签不存在: {', '.join(missing_tags)}")
        row.tag_ids = list(dict.fromkeys(resolved_tag_ids))

        normalized_name = self._normalize_name(row.name)
        if normalized_name and normalized_name in existing_products:
            row.duplicate_hint = True
            row.errors.append("好物名称已存在")
            row.warnings.append("检测到同名好物")

    @staticmethod
    def _normalize_cell_value(value) -> str:
        if value is None:
            return ""
        return str(value).strip()

    def _get_cell(self, values, header_index: dict[str, int], key: str) -> str:
        index = header_index.get(key)
        if index is None or index >= len(values):
            return ""
        return self._normalize_cell_value(values[index])

    @staticmethod
    def _is_empty_row(values) -> bool:
        return all(value in (None, "") for value in values)

    @staticmethod
    def _empty_to_none(value: str) -> str | None:
        return value or None

    def _parse_status(self, value: str) -> tuple[bool, str | None]:
        normalized = str(value or "").strip().lower()
        if not normalized:
            return True, None
        if normalized in self.STATUS_TRUE_VALUES:
            return True, None
        if normalized in self.STATUS_FALSE_VALUES:
            return False, None
        return True, "上架状态仅支持 true/false/1/0/是/否"

    @staticmethod
    def _parse_order(value: str) -> tuple[int, str | None]:
        if not value:
            return 0, None
        try:
            return int(str(value).strip()), None
        except (TypeError, ValueError):
            return 0, "排序必须是整数"

    def _parse_detail_description(self, detail_text: str, detail_description_json: str):
        if detail_description_json:
            try:
                parsed = json.loads(detail_description_json)
                if isinstance(parsed, list):
                    return parsed, None
                return [], "结构化详情JSON必须是数组"
            except json.JSONDecodeError:
                return [], "结构化详情JSON不是合法的 JSON"
        if detail_text:
            return [
                {
                    "type": "text",
                    "title": "产品介绍",
                    "content": detail_text,
                }
            ], None
        return [], None

    @staticmethod
    def _parse_tag_names(value: str) -> list[str]:
        if not value:
            return []
        parts = re.split(r"[;；\n]+", value)
        return list(dict.fromkeys(part.strip() for part in parts if part and part.strip()))

    @staticmethod
    def _normalize_name(value: str) -> str:
        return unicodedata.normalize("NFKC", str(value or "").strip())


product_import_parser_service = ProductImportParserService()
