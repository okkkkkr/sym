import json
import os
import re
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException, UploadFile

from app.settings import settings


class ProductImportUploadService:
    upload_id_pattern = re.compile(r"^[0-9a-f]{32}$")

    def __init__(self, base_dir: str | None = None):
        self.base_dir = base_dir or settings.PRODUCT_IMPORT_TMP_DIR

    def get_upload_dir(self, upload_id: str) -> str:
        self._validate_upload_id(upload_id)
        return str(self._ensure_safe_path(Path(self.base_dir) / upload_id))

    def get_chunks_dir(self, upload_id: str) -> str:
        return os.path.join(self.get_upload_dir(upload_id), "chunks")

    def get_meta_path(self, upload_id: str) -> str:
        return os.path.join(self.get_upload_dir(upload_id), "meta.json")

    def get_merged_file_path(self, upload_id: str, filename: str) -> str:
        return os.path.join(self.get_upload_dir(upload_id), filename)

    def get_extract_dir(self) -> str:
        return os.path.join(self.base_dir, "extract")

    async def init_upload(
        self,
        *,
        filename: str,
        file_size: int,
        total_chunks: int,
        chunk_size: int,
        task_id: int,
        created_by: int,
        import_strategy: str,
    ) -> dict:
        upload_id = uuid4().hex
        chunks_dir = self.get_chunks_dir(upload_id)
        os.makedirs(chunks_dir, exist_ok=True)
        meta = {
            "upload_id": upload_id,
            "task_id": task_id,
            "created_by": created_by,
            "filename": Path(filename).name,
            "file_size": file_size,
            "total_chunks": total_chunks,
            "chunk_size": chunk_size,
            "import_strategy": import_strategy,
        }
        self._write_meta(upload_id, meta)
        return meta

    async def get_upload_meta(self, upload_id: str) -> dict:
        meta_path = self.get_meta_path(upload_id)
        if not os.path.exists(meta_path):
            raise HTTPException(status_code=404, detail="未找到上传任务")
        with open(meta_path, "r", encoding="utf-8") as file_obj:
            return json.load(file_obj)

    async def list_uploaded_chunks(self, upload_id: str) -> list[int]:
        chunks_dir = self.get_chunks_dir(upload_id)
        if not os.path.exists(chunks_dir):
            return []
        chunk_indexes = []
        for name in os.listdir(chunks_dir):
            if not name.endswith(".part"):
                continue
            try:
                chunk_indexes.append(int(name.replace(".part", "")))
            except ValueError:
                continue
        return sorted(chunk_indexes)

    async def save_chunk(self, upload_id: str, chunk_index: int, chunk_file: UploadFile) -> dict:
        meta = await self.get_upload_meta(upload_id)
        if chunk_index < 0 or chunk_index >= meta["total_chunks"]:
            raise HTTPException(status_code=400, detail="分片序号不合法")

        chunk_path = os.path.join(self.get_chunks_dir(upload_id), f"{chunk_index}.part")
        chunk_content = await chunk_file.read()
        if not chunk_content:
            raise HTTPException(status_code=400, detail="分片内容不能为空")
        if len(chunk_content) > meta["chunk_size"] and chunk_index != meta["total_chunks"] - 1:
            raise HTTPException(status_code=400, detail="分片大小超出系统限制")

        with open(chunk_path, "wb") as file_obj:
            file_obj.write(chunk_content)

        uploaded_chunks = await self.list_uploaded_chunks(upload_id)
        return {
            "upload_id": upload_id,
            "chunk_index": chunk_index,
            "uploaded_chunks": uploaded_chunks,
            "is_complete": len(uploaded_chunks) == meta["total_chunks"],
        }

    async def complete_upload(self, upload_id: str) -> dict:
        meta = await self.get_upload_meta(upload_id)
        uploaded_chunks = await self.list_uploaded_chunks(upload_id)
        expected_chunks = list(range(meta["total_chunks"]))
        if uploaded_chunks != expected_chunks:
            raise HTTPException(status_code=400, detail="分片上传不完整")

        merged_file_path = self.get_merged_file_path(upload_id, meta["filename"])
        with open(merged_file_path, "wb") as merged_file:
            for chunk_index in expected_chunks:
                chunk_path = os.path.join(self.get_chunks_dir(upload_id), f"{chunk_index}.part")
                with open(chunk_path, "rb") as chunk_file:
                    shutil.copyfileobj(chunk_file, merged_file)

        merged_file_size = os.path.getsize(merged_file_path)
        if merged_file_size != meta["file_size"]:
            raise HTTPException(status_code=400, detail="合并后的文件大小与原始声明不一致")

        meta["merged_file_path"] = merged_file_path
        self._write_meta(upload_id, meta)
        return meta

    async def cleanup_upload(self, upload_id: str) -> None:
        upload_dir = self.get_upload_dir(upload_id)
        self.cleanup_path(upload_dir)

    async def cleanup_task_uploads(self, task_id: int) -> int:
        cleaned_count = 0
        base_dir = self._resolve_base_dir()
        if not base_dir.exists():
            return cleaned_count
        for upload_dir in base_dir.iterdir():
            if not upload_dir.is_dir() or upload_dir.name == "extract":
                continue
            meta = self._read_meta(upload_dir / "meta.json")
            if int(meta.get("task_id") or 0) != int(task_id):
                continue
            self.cleanup_path(upload_dir)
            cleaned_count += 1
        return cleaned_count

    def cleanup_path(self, path: str | Path) -> int:
        cleanup_path = self._ensure_safe_path(path)
        if not cleanup_path.exists():
            return 0
        size = self.get_path_size(cleanup_path)
        if cleanup_path.is_dir():
            shutil.rmtree(cleanup_path)
        else:
            cleanup_path.unlink()
        return size

    def list_expired_upload_dirs(self, retention_hours: int) -> list[dict]:
        base_dir = self._resolve_base_dir()
        if not base_dir.exists():
            return []

        expired_dirs = []
        for upload_dir in base_dir.iterdir():
            if not upload_dir.is_dir() or upload_dir.name == "extract":
                continue
            meta_path = upload_dir / "meta.json"
            chunks_dir = upload_dir / "chunks"
            if not meta_path.exists() and not chunks_dir.exists():
                continue
            if not self._is_expired(upload_dir, retention_hours):
                continue
            expired_dirs.append(
                {
                    "upload_id": upload_dir.name,
                    "path": str(upload_dir),
                    "meta": self._read_meta(meta_path),
                    "size": self.get_path_size(upload_dir),
                }
            )
        return expired_dirs

    def list_expired_extract_dirs(self, retention_hours: int) -> list[dict]:
        extract_dir = self._ensure_safe_path(self.get_extract_dir())
        if not extract_dir.exists():
            return []

        expired_dirs = []
        for task_dir in extract_dir.iterdir():
            if not task_dir.is_dir() or not self._is_expired(task_dir, retention_hours):
                continue
            expired_dirs.append(
                {
                    "task_id": int(task_dir.name) if task_dir.name.isdigit() else None,
                    "path": str(task_dir),
                    "size": self.get_path_size(task_dir),
                }
            )
        return expired_dirs

    def get_path_size(self, path: str | Path) -> int:
        safe_path = self._ensure_safe_path(path)
        if not safe_path.exists():
            return 0
        if safe_path.is_file():
            return safe_path.stat().st_size
        total_size = 0
        for root, _, files in os.walk(safe_path):
            for filename in files:
                file_path = Path(root) / filename
                if file_path.exists():
                    total_size += file_path.stat().st_size
        return total_size

    def _resolve_base_dir(self) -> Path:
        return Path(self.base_dir).resolve()

    def _validate_upload_id(self, upload_id: str) -> None:
        if not self.upload_id_pattern.fullmatch(str(upload_id or "")):
            raise HTTPException(status_code=400, detail="上传 ID 不合法")

    def _ensure_safe_path(self, path: str | Path) -> Path:
        safe_path = Path(path).resolve()
        try:
            safe_path.relative_to(self._resolve_base_dir())
        except ValueError as exc:
            raise HTTPException(status_code=500, detail="临时文件路径不在允许清理范围内") from exc
        return safe_path

    def _is_expired(self, path: Path, retention_hours: int) -> bool:
        retention_deadline = datetime.now() - timedelta(hours=max(1, int(retention_hours)))
        return datetime.fromtimestamp(path.stat().st_mtime) < retention_deadline

    @staticmethod
    def _read_meta(meta_path: Path) -> dict:
        if not meta_path.exists():
            return {}
        try:
            with open(meta_path, "r", encoding="utf-8") as file_obj:
                return json.load(file_obj)
        except (OSError, ValueError):
            return {}

    def _write_meta(self, upload_id: str, meta: dict) -> None:
        os.makedirs(self.get_upload_dir(upload_id), exist_ok=True)
        with open(self.get_meta_path(upload_id), "w", encoding="utf-8") as file_obj:
            json.dump(meta, file_obj, ensure_ascii=False, indent=2)


product_import_upload_service = ProductImportUploadService()
