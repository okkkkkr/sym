import os
import shutil
import zipfile
from pathlib import Path

from fastapi import HTTPException

from app.schemas.product_import import ProductImportMaterialSet
from app.settings import settings
from app.utils.product_media import sort_media_paths


class ProductImportZipService:
    IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
    VIDEO_EXTENSIONS = {".mp4", ".mov", ".avi", ".mkv"}
    IGNORED_ROOT_DIRECTORIES = {"__MACOSX"}
    IGNORED_FILENAMES = {".DS_Store"}

    def validate_zip(self, zip_path: str) -> dict:
        if not os.path.exists(zip_path):
            raise HTTPException(status_code=404, detail="未找到上传的 ZIP 文件")
        if not zipfile.is_zipfile(zip_path):
            raise HTTPException(status_code=400, detail="上传文件不是合法的 ZIP 压缩包")
        if os.path.getsize(zip_path) > settings.PRODUCT_IMPORT_MAX_FILE_SIZE:
            raise HTTPException(status_code=400, detail="ZIP 文件大小超出系统限制")

        root_excel_found = False
        file_count = 0
        total_uncompressed_size = 0
        directories = set()

        with zipfile.ZipFile(zip_path, "r") as zip_file:
            entries = self._build_zip_entries(zip_file)
            if len(entries) > settings.PRODUCT_IMPORT_MAX_ENTRIES:
                raise HTTPException(status_code=400, detail="ZIP 条目数量超出系统限制")
            wrapper_dir = self._detect_wrapper_dir(entries)
            for info, parts, is_directory in entries:
                normalized_parts = self._strip_wrapper(parts, wrapper_dir)
                if not normalized_parts:
                    continue

                if is_directory:
                    if len(normalized_parts) > 1:
                        raise HTTPException(status_code=400, detail="ZIP 包内不允许多级目录")
                    directories.add(normalized_parts[0])
                    continue

                file_count += 1
                total_uncompressed_size += info.file_size
                if info.file_size <= 0:
                    raise HTTPException(status_code=400, detail="ZIP 包内存在空文件")
                if info.file_size > settings.PRODUCT_IMPORT_MAX_ENTRY_SIZE:
                    raise HTTPException(status_code=400, detail="ZIP 包内单个文件大小超出系统限制")
                if total_uncompressed_size > settings.PRODUCT_IMPORT_MAX_UNCOMPRESSED_SIZE:
                    raise HTTPException(status_code=400, detail="ZIP 解压总体积超出系统限制")
                if (
                    info.compress_size <= 0
                    or info.file_size / info.compress_size > settings.PRODUCT_IMPORT_MAX_COMPRESSION_RATIO
                ):
                    raise HTTPException(status_code=400, detail="ZIP 包内文件压缩比异常")

                if len(normalized_parts) == 1:
                    if normalized_parts[0] == "product.xlsx":
                        root_excel_found = True
                    else:
                        raise HTTPException(status_code=400, detail="ZIP 导入根目录仅允许存在 product.xlsx")
                    continue

                if len(normalized_parts) != 2:
                    raise HTTPException(status_code=400, detail="ZIP 仅支持一级素材目录")
                directories.add(normalized_parts[0])

        if not root_excel_found:
            raise HTTPException(status_code=400, detail="ZIP 导入根目录必须包含 product.xlsx")

        return {
            "file_count": file_count,
            "total_uncompressed_size": total_uncompressed_size,
            "directories": sorted(directories),
        }

    def extract_to_temp(self, zip_path: str, task_id: int) -> str:
        validation = self.validate_zip(zip_path)
        extract_dir = os.path.join(settings.PRODUCT_IMPORT_TMP_DIR, "extract", str(task_id))
        if os.path.exists(extract_dir):
            shutil.rmtree(extract_dir)
        os.makedirs(extract_dir, exist_ok=True)

        required_space = validation["total_uncompressed_size"] + settings.PRODUCT_IMPORT_DISK_RESERVE_SIZE
        if shutil.disk_usage(extract_dir).free < required_space:
            shutil.rmtree(extract_dir)
            raise HTTPException(status_code=507, detail="磁盘可用空间不足，无法安全解压")

        extracted_size = 0
        try:
            with zipfile.ZipFile(zip_path, "r") as zip_file:
                entries = self._build_zip_entries(zip_file)
                wrapper_dir = self._detect_wrapper_dir(entries)
                base_path = Path(extract_dir).resolve()

                for info, parts, is_directory in entries:
                    normalized_parts = self._strip_wrapper(parts, wrapper_dir)
                    if not normalized_parts:
                        continue

                    resolved_target = Path(extract_dir).joinpath(*normalized_parts).resolve()
                    try:
                        resolved_target.relative_to(base_path)
                    except ValueError as exc:
                        raise HTTPException(status_code=400, detail="ZIP 解压路径不安全") from exc

                    if is_directory:
                        resolved_target.mkdir(parents=True, exist_ok=True)
                        continue

                    resolved_target.parent.mkdir(parents=True, exist_ok=True)
                    entry_size = 0
                    with zip_file.open(info, "r") as source, open(resolved_target, "wb") as target:
                        while chunk := source.read(1024 * 1024):
                            entry_size += len(chunk)
                            extracted_size += len(chunk)
                            if entry_size > settings.PRODUCT_IMPORT_MAX_ENTRY_SIZE:
                                raise HTTPException(status_code=400, detail="ZIP 解压单文件体积超出系统限制")
                            if extracted_size > settings.PRODUCT_IMPORT_MAX_UNCOMPRESSED_SIZE:
                                raise HTTPException(status_code=400, detail="ZIP 实际解压体积超出系统限制")
                            target.write(chunk)
        except Exception:
            shutil.rmtree(extract_dir, ignore_errors=True)
            raise

        return extract_dir

    def scan_materials(self, extract_dir: str) -> dict[str, ProductImportMaterialSet]:
        material_map: dict[str, ProductImportMaterialSet] = {}
        for entry in sorted(os.listdir(extract_dir)):
            absolute_path = os.path.join(extract_dir, entry)
            if entry == "product.xlsx" or not os.path.isdir(absolute_path):
                continue

            images: list[str] = []
            videos: list[str] = []
            for child in sorted(os.listdir(absolute_path)):
                child_path = os.path.join(absolute_path, child)
                if os.path.isdir(child_path):
                    raise HTTPException(status_code=400, detail="素材目录下不允许再嵌套子目录")
                suffix = Path(child).suffix.lower()
                if suffix in self.IMAGE_EXTENSIONS:
                    images.append(child_path)
                elif suffix in self.VIDEO_EXTENSIONS:
                    videos.append(child_path)

            sorted_images = sort_media_paths(images)
            cover_image = self._pick_cover_image(sorted_images)
            material_map[entry] = ProductImportMaterialSet(
                directory_name=entry,
                cover_image=cover_image,
                images=sorted_images,
                videos=videos,
            )
        return material_map

    @staticmethod
    def _pick_cover_image(images: list[str]) -> str | None:
        if not images:
            return None
        cover_candidates = [image for image in images if "_cover" in Path(image).stem.lower()]
        if cover_candidates:
            return sorted(cover_candidates)[0]
        return sorted(images)[0]

    def _build_zip_entries(self, zip_file: zipfile.ZipFile) -> list[tuple[zipfile.ZipInfo, list[str], bool]]:
        entries: list[tuple[zipfile.ZipInfo, list[str], bool]] = []
        for info in zip_file.infolist():
            if (info.external_attr >> 16) & 0o170000 == 0o120000:
                raise HTTPException(status_code=400, detail="ZIP 包内不允许符号链接")
            filename = info.filename
            normalized = filename.replace("\\", "/").strip()
            if not normalized:
                continue
            parts = [part for part in normalized.split("/") if part not in {"", "."}]
            if any(part == ".." for part in parts):
                raise HTTPException(status_code=400, detail="ZIP 包内包含非法相对路径")
            if normalized.startswith("/"):
                raise HTTPException(status_code=400, detail="ZIP 包内不允许绝对路径")
            if self._should_ignore(parts):
                continue

            is_directory = info.is_dir() or normalized.endswith("/")
            entries.append((info, parts, is_directory))
        return entries

    def _detect_wrapper_dir(self, entries: list[tuple[zipfile.ZipInfo, list[str], bool]]) -> str | None:
        file_entries = [parts for _, parts, is_directory in entries if not is_directory]
        if not file_entries:
            return None

        first_root = file_entries[0][0]
        if all(len(parts) >= 2 and parts[0] == first_root for parts in file_entries):
            return first_root
        return None

    @staticmethod
    def _strip_wrapper(parts: list[str], wrapper_dir: str | None) -> list[str]:
        if wrapper_dir and parts and parts[0] == wrapper_dir:
            return parts[1:]
        return parts

    def _should_ignore(self, parts: list[str]) -> bool:
        if not parts:
            return True
        if parts[0] in self.IGNORED_ROOT_DIRECTORIES:
            return True
        if parts[-1] in self.IGNORED_FILENAMES:
            return True
        return any(part.startswith("._") for part in parts)


product_import_zip_service = ProductImportZipService()
