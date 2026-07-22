import asyncio
import mimetypes
import os
import subprocess
from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException, UploadFile

from app.services.media_storage import media_storage_service
from app.settings import settings


class VideoProcessingService:
    allowed_extensions = {".mp4", ".mov", ".webm"}
    allowed_content_types = {"video/mp4", "video/quicktime", "video/webm"}
    chunk_size = 1024 * 1024
    storage_prefix = "items/videos"

    def ensure_temp_dir(self) -> str:
        os.makedirs(settings.VIDEO_UPLOAD_TMP_DIR, exist_ok=True)
        return settings.VIDEO_UPLOAD_TMP_DIR

    def sanitize_filename(self, file_name: str) -> str:
        return media_storage_service.sanitize_filename(file_name)

    def validate_upload_file(self, file_name: str, content_type: str | None) -> tuple[str, str]:
        normalized_name = self.sanitize_filename(file_name or "video")
        extension = Path(normalized_name).suffix.lower()
        if extension not in self.allowed_extensions:
            raise HTTPException(status_code=400, detail="仅支持 mp4、mov、webm 视频")
        normalized_content_type = str(content_type or "").strip().lower()
        guessed_content_type = mimetypes.guess_type(normalized_name)[0] or ""
        resolved_content_type = normalized_content_type or guessed_content_type
        if resolved_content_type and resolved_content_type not in self.allowed_content_types:
            raise HTTPException(status_code=400, detail="视频 MIME 类型不支持")
        return normalized_name, extension

    async def save_temp_upload(self, upload_file: UploadFile) -> tuple[str, str, int]:
        if not upload_file:
            raise HTTPException(status_code=400, detail="未找到待上传文件")
        normalized_name, extension = self.validate_upload_file(upload_file.filename or "", upload_file.content_type)
        temp_dir = self.ensure_temp_dir()
        temp_path = os.path.join(temp_dir, f"{uuid4().hex}{extension}")
        file_size = 0
        try:
            with open(temp_path, "wb") as file_obj:
                while True:
                    chunk = await upload_file.read(self.chunk_size)
                    if not chunk:
                        break
                    file_size += len(chunk)
                    self.validate_size(file_size)
                    file_obj.write(chunk)
        except Exception:
            self.cleanup_file(temp_path)
            raise
        if file_size <= 0:
            self.cleanup_file(temp_path)
            raise HTTPException(status_code=400, detail="文件内容不能为空")
        await self.validate_video_content(temp_path)
        return temp_path, normalized_name, file_size

    async def validate_video_content(self, file_path: str) -> None:
        command = [
            "ffprobe",
            "-v",
            "error",
            "-select_streams",
            "v:0",
            "-show_entries",
            "stream=codec_type",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            file_path,
        ]
        try:
            completed = await asyncio.to_thread(
                subprocess.run,
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=False,
                timeout=15,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            self.cleanup_file(file_path)
            raise HTTPException(status_code=400, detail="视频内容校验失败") from exc
        if completed.returncode != 0 or completed.stdout.strip() != "video":
            self.cleanup_file(file_path)
            raise HTTPException(status_code=400, detail="文件不是有效视频")

    def build_storage_key(self) -> str:
        return f"{self.storage_prefix}/vid_{uuid4().hex}.mp4"

    def build_compressed_temp_path(self) -> str:
        return os.path.join(self.ensure_temp_dir(), f"{uuid4().hex}.mp4")

    async def compress_video(self, input_path: str, output_path: str) -> None:
        if not os.path.exists(input_path):
            raise HTTPException(status_code=404, detail="待压缩视频不存在")
        command = [
            "ffmpeg",
            "-y",
            "-i",
            input_path,
            "-c:v",
            "libx264",
            "-crf",
            "23",
            "-preset",
            "medium",
            "-c:a",
            "aac",
            "-b:a",
            "128k",
            "-movflags",
            "+faststart",
            output_path,
        ]
        completed = await asyncio.to_thread(
            subprocess.run,
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
        )
        if completed.returncode != 0:
            error_message = (completed.stderr or completed.stdout or "ffmpeg failed").strip()
            raise RuntimeError(error_message)
        if not os.path.exists(output_path):
            raise RuntimeError("ffmpeg 未生成压缩文件")
        self.validate_size(os.path.getsize(output_path))

    async def upload_compressed_file(self, local_path: str, object_key: str) -> dict:
        upload_result = await media_storage_service.upload_local_file(
            local_path,
            object_key,
            file_name=Path(object_key).name,
            mime_type="video/mp4",
        )
        return upload_result.to_api_dict()

    @staticmethod
    def cleanup_file(file_path: str | None) -> None:
        normalized_path = str(file_path or "").strip()
        if normalized_path and os.path.exists(normalized_path):
            os.remove(normalized_path)

    @staticmethod
    def validate_size(file_size: int) -> None:
        if file_size > settings.MEDIA_UPLOAD_MAX_FILE_SIZE:
            raise HTTPException(status_code=400, detail="文件大小超出系统限制")


video_processing_service = VideoProcessingService()
