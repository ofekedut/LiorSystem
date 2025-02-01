from PIL import Image
import os
from fastapi import UploadFile, HTTPException
from typing import Tuple, Set
import asyncio


class ImageService:
    ALLOWED_FORMATS: Set[str] = {'JPEG', 'PNG'}
    MAX_FILE_SIZE: int = 5 * 1024 * 1024  # 5MB

    def __init__(self, upload_dir: str, max_size: Tuple[int, int] = (200, 200)):
        self.upload_dir = upload_dir
        self.max_size = max_size
        self._lock = asyncio.Lock()
        os.makedirs(upload_dir, exist_ok=True)

    async def process_avatar(self, file: UploadFile, filename: str) -> str:
        if self.get_image_size(file) > self.MAX_FILE_SIZE:
            raise HTTPException(status_code=400, detail="File too large")

        try:
            async with self._lock:
                return await self._save_image(file, filename)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid image: {str(e)}")

    async def _save_image(self, file: UploadFile, filename: str) -> str:
        file_path = os.path.join(self.upload_dir, filename)

        with Image.open(file.file) as img:
            if img.format not in self.ALLOWED_FORMATS:
                raise ValueError(f"Unsupported format: {img.format}")

            img = img.convert('RGB')
            img.thumbnail(self.max_size)

            img.save(file_path, format='JPEG', quality=85, optimize=True)

        return file_path

    async def delete_avatar(self, filepath: str) -> None:
        if filepath and os.path.exists(filepath):
            try:
                os.remove(filepath)
            except OSError as e:
                raise HTTPException(status_code=500, detail=f"Failed to delete file: {str(e)}")

    def get_image_size(self, file: UploadFile) -> int:
        try:
            file.file.seek(0, 2)
            size = file.file.tell()
            file.file.seek(0)
            return size
        except Exception:
            raise HTTPException(status_code=400, detail="Cannot determine file size")