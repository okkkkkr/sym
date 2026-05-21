import os
import shutil
import zipfile
from pathlib import Path

from fastapi import HTTPException

from app.schemas.product_import import ProductImportMaterialSet
from app.settings import settings


class ProductImportZipService:
    IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
    VIDEO_EXTENSIONS = {".mp4", ".mov", ".avi", ".mkv"}

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
            for info in zip_file.infolist():
                filename = info.filename
                normalized = filename.replace("\\", "/").strip()
                if not normalized:
                    continue
                parts = [part for part in normalized.split("/") if part not in {"", "."}]
                if any(part == ".." for part in parts):
                    raise HTTPException(status_code=400, detail="ZIP 包内包含非法相对路径")
                if normalized.startswith("/"):
                    raise HTTPException(status_code=400, detail="ZIP 包内不允许绝对路径")

                is_directory = info.is_dir() or normalized.endswith("/")
                if is_directory:
                    if len(parts) > 1:
                        raise HTTPException(status_code=400, detail="ZIP 包内不允许多级目录")
                    if parts:
                        directories.add(parts[0])
                    continue

                file_count += 1
                total_uncompressed_size += info.file_size
                if info.file_size <= 0:
                    raise HTTPException(status_code=400, detail="ZIP 包内存在空文件")

                if len(parts) == 1:
                    if parts[0] == "product.xlsx":
                        root_excel_found = True
                    else:
                        raise HTTPException(status_code=400, detail="ZIP 根目录仅允许存在 product.xlsx")
                    continue

                if len(parts) != 2:
                    raise HTTPException(status_code=400, detail="ZIP 仅支持一级素材目录")
                directories.add(parts[0])

        if not root_excel_found:
            raise HTTPException(status_code=400, detail="ZIP 根目录必须包含 product.xlsx")

        return {
            "file_count": file_count,
            "total_uncompressed_size": total_uncompressed_size,
            "directories": sorted(directories),
        }

    def extract_to_temp(self, zip_path: str, task_id: int) -> str:
        extract_dir = os.path.join(settings.PRODUCT_IMPORT_TMP_DIR, "extract", str(task_id))
        if os.path.exists(extract_dir):
            shutil.rmtree(extract_dir)
        os.makedirs(extract_dir, exist_ok=True)

        with zipfile.ZipFile(zip_path, "r") as zip_file:
            for info in zip_file.infolist():
                target_path = Path(extract_dir) / info.filename
                resolved_target = target_path.resolve()
                if not str(resolved_target).startswith(str(Path(extract_dir).resolve())):
                    raise HTTPException(status_code=400, detail="ZIP 解压路径不安全")
            zip_file.extractall(extract_dir)

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

            cover_image = self._pick_cover_image(images)
            material_map[entry] = ProductImportMaterialSet(
                directory_name=entry,
                cover_image=cover_image,
                images=images,
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


product_import_zip_service = ProductImportZipService()