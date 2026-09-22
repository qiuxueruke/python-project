"""把用户头像上传到阿里云 OSS，并拼出可公开访问的 URL。"""
import uuid

import oss2
from fastapi import HTTPException

from fastapi_app.core.config import get_settings

MAX_AVATAR_BYTES = 1 * 1024 * 1024


def detect_image_type(content: bytes) -> tuple[str, str]:
    if content.startswith(b"\xff\xd8\xff"):
        return "image/jpeg", ".jpg"
    if content.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png", ".png"
    if content.startswith((b"GIF87a", b"GIF89a")):
        return "image/gif", ".gif"
    if len(content) >= 12 and content[:4] == b"RIFF" and content[8:12] == b"WEBP":
        return "image/webp", ".webp"
    raise HTTPException(status_code=400, detail="仅支持 jpg/png/gif/webp 图片")


def _bucket() -> oss2.Bucket:
    settings = get_settings()
    if not settings.oss_access_key_id or not settings.oss_access_key_secret:
        raise HTTPException(status_code=500, detail="未配置对象存储")
    auth = oss2.Auth(settings.oss_access_key_id, settings.oss_access_key_secret)
    return oss2.Bucket(auth, settings.oss_endpoint, settings.oss_bucket)


def public_url(key: str) -> str:
    return f"{get_settings().oss_public_base_url.rstrip('/')}/{key.lstrip('/')}"


def upload_avatar(content: bytes, user_id: int) -> str:
    if not content:
        raise HTTPException(status_code=400, detail="请选择图片")
    if len(content) > MAX_AVATAR_BYTES:
        raise HTTPException(status_code=400, detail="头像不能超过 1MB")

    mime, ext = detect_image_type(content)
    key = f"avatars/{user_id}/{uuid.uuid4().hex}{ext}"
    try:
        _bucket().put_object(
            key,
            content,
            headers={
                "Content-Type": mime,
                "x-oss-object-acl": oss2.OBJECT_ACL_PUBLIC_READ,
            },
        )
    except oss2.exceptions.OssError as exc:
        raise HTTPException(status_code=502, detail="头像上传失败") from exc
    return public_url(key)


def delete_by_public_url(url: str | None) -> None:
    if not url:
        return
    base = get_settings().oss_public_base_url.rstrip("/")
    prefix = f"{base}/"
    if not url.startswith(prefix):
        return
    key = url[len(prefix) :]
    if not key.startswith("avatars/"):
        return
    try:
        _bucket().delete_object(key)
    except Exception as exc:  # noqa: BLE001
        print(f"[warn] skip delete oss object: {exc}")
