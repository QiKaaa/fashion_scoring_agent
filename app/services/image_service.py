import os
import uuid
from typing import Optional, Tuple, Dict, Any
from pathlib import Path
import aiofiles
from fastapi import UploadFile
from PIL import Image, ImageOps, ExifTags
import io

from app.core.config import settings


class ImageService:
    """图像处理服务"""
    
    def __init__(self, upload_dir: Optional[str] = None):
        self.upload_dir = upload_dir or settings.UPLOAD_DIR
        # 确保上传目录存在
        os.makedirs(self.upload_dir, exist_ok=True)
    
    async def save_upload(self, file: UploadFile) -> Dict[str, Any]:
        """保存上传的图像文件"""
        # 验证文件类型
        if file.content_type not in settings.ALLOWED_IMAGE_TYPES:
            raise ValueError(f"不支持的文件类型: {file.content_type}")
        
        # 读取文件内容
        content = await file.read()
        
        # 验证文件大小
        if len(content) > settings.MAX_IMAGE_SIZE:
            raise ValueError(f"文件太大，最大允许大小为 {settings.MAX_IMAGE_SIZE / 1024 / 1024}MB")
        
        # 生成唯一文件名
        file_ext = os.path.splitext(file.filename)[1] if file.filename else ".jpg"
        filename = f"{uuid.uuid4()}{file_ext}"
        filepath = os.path.join(self.upload_dir, filename)
        
        # 处理图像
        processed_image, metadata = await self.process_image(content)
        
        # 保存处理后的图像
        await self.save_image(processed_image, filepath)
        
        return {
            "filename": filename,
            "filepath": filepath,
            "content_type": file.content_type,
            "size": len(content),
            "metadata": metadata
        }
    
    async def process_image(self, image_content: bytes) -> Tuple[Image.Image, Dict[str, Any]]:
        """处理图像：调整大小、修正方向等"""
        # 打开图像
        image = Image.open(io.BytesIO(image_content))
        
        # 提取元数据
        metadata = {
            "format": image.format,
            "mode": image.mode,
            "width": image.width,
            "height": image.height,
        }
        
        # 修正图像方向
        image = self._fix_orientation(image)
        
        # 调整图像大小
        if image.width > settings.IMAGE_RESIZE_WIDTH:
            ratio = settings.IMAGE_RESIZE_WIDTH / image.width
            new_height = int(image.height * ratio)
            image = image.resize((settings.IMAGE_RESIZE_WIDTH, new_height), Image.LANCZOS)
            metadata["resized"] = True
            metadata["new_width"] = settings.IMAGE_RESIZE_WIDTH
            metadata["new_height"] = new_height
        
        return image, metadata
    
    def _fix_orientation(self, image: Image.Image) -> Image.Image:
        """修正图像方向（处理EXIF方向标签）"""
        try:
            # 获取EXIF数据
            exif = image._getexif()
            if exif is None:
                return image
            
            # 查找方向标签
            orientation_key = None
            for key in ExifTags.TAGS.keys():
                if ExifTags.TAGS[key] == 'Orientation':
                    orientation_key = key
                    break
            
            if orientation_key is None or orientation_key not in exif:
                return image
            
            # 根据方向标签旋转图像
            orientation = exif[orientation_key]
            if orientation == 2:
                # 水平翻转
                return ImageOps.mirror(image)
            elif orientation == 3:
                # 旋转180度
                return image.rotate(180, expand=True)
            elif orientation == 4:
                # 垂直翻转
                return ImageOps.flip(image)
            elif orientation == 5:
                # 顺时针旋转90度并水平翻转
                image = image.rotate(90, expand=True)
                return ImageOps.mirror(image)
            elif orientation == 6:
                # 顺时针旋转90度
                return image.rotate(270, expand=True)
            elif orientation == 7:
                # 顺时针旋转270度并水平翻转
                image = image.rotate(270, expand=True)
                return ImageOps.mirror(image)
            elif orientation == 8:
                # 顺时针旋转270度
                return image.rotate(90, expand=True)
        except Exception:
            # 如果处理EXIF数据出错，返回原始图像
            pass
        
        return image
    
    async def save_image(self, image: Image.Image, filepath: str) -> None:
        """保存图像到文件系统"""
        # 确保目录存在
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        # 将PIL图像转换为字节
        img_byte_arr = io.BytesIO()
        image.save(img_byte_arr, format=image.format or 'JPEG')
        img_byte_arr = img_byte_arr.getvalue()
        
        # 异步写入文件
        async with aiofiles.open(filepath, 'wb') as f:
            await f.write(img_byte_arr)
    
    async def get_image_bytes(self, filepath: str) -> bytes:
        """获取图像文件的字节内容"""
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"图像文件不存在: {filepath}")
        
        async with aiofiles.open(filepath, 'rb') as f:
            return await f.read()


# 创建默认服务实例
image_service = ImageService()