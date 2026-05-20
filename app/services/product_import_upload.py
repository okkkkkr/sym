import json
import os
import shutil
from uuid import uuid4

from fastapi import HTTPException, UploadFile

from app.settings import settings


class ProductImportUploadService:
    def __init__(self, base_dir: str | None = None):
        self.base_dir = base_dir or settings.PRODUCT_IMPORT_TMP_DIR

    def get_upload_dir(self, upload_id: str) -> str:
        return os.path.join(self.base_dir, upload_id)

    def get_chunks_dir(self, upload_id: str) -> str:
        return os.path.join(self.get_upload_dir(upload_id), "chunks")

    def get_meta_path(self, upload_id: str) -> str:
        return os.path.join(self.get_upload_dir(upload_id), "meta.json")

    def get_merged_file_path(self, upload_id: str, filename: str) -> str:
        return os.path.join(self.get_upload_dir(upload_id), filename)

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
        upload_dir = self.get_upload_dir(upload_id)
        chunks_dir = self.get_chunks_dir(upload_id)
        os.makedirs(chunks_dir, exist_ok=True)
        meta = {
            "upload_id": upload_id,
            "task_id": task_id,
            "created_by": created_by,
            "filename": filename,
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
            raise HTTPException(status_code=404, detail="upload task not found")
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
            raise HTTPException(status_code=400, detail="invalid chunk index")

        chunk_path = os.path.join(self.get_chunks_dir(upload_id), f"{chunk_index}.part")
        chunk_content = await chunk_file.read()
        if not chunk_content:
            raise HTTPException(status_code=400, detail="empty chunk is not allowed")
        if len(chunk_content) > meta["chunk_size"] and chunk_index != meta["total_chunks"] - 1:
            raise HTTPException(status_code=400, detail="chunk size exceeds configured limit")

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
            raise HTTPException(status_code=400, detail="chunks are incomplete")

        merged_file_path = self.get_merged_file_path(upload_id, meta["filename"])
        with open(merged_file_path, "wb") as merged_file:
            for chunk_index in expected_chunks:
                chunk_path = os.path.join(self.get_chunks_dir(upload_id), f"{chunk_index}.part")
                with open(chunk_path, "rb") as chunk_file:
                    shutil.copyfileobj(chunk_file, merged_file)

        merged_file_size = os.path.getsize(merged_file_path)
        if merged_file_size != meta["file_size"]:
            raise HTTPException(status_code=400, detail="merged file size mismatch")

        meta["merged_file_path"] = merged_file_path
        self._write_meta(upload_id, meta)
        return meta

    async def cleanup_upload(self, upload_id: str) -> None:
        upload_dir = self.get_upload_dir(upload_id)
        if os.path.exists(upload_dir):
            shutil.rmtree(upload_dir)

    def _write_meta(self, upload_id: str, meta: dict) -> None:
        os.makedirs(self.get_upload_dir(upload_id), exist_ok=True)
        with open(self.get_meta_path(upload_id), "w", encoding="utf-8") as file_obj:
            json.dump(meta, file_obj, ensure_ascii=False, indent=2)


product_import_upload_service = ProductImportUploadService()