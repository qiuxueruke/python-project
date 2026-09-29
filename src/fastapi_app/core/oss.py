"""把用户头像上传到阿里云 OSS，并拼出可公开访问的 URL。"""
# 导入 uuid 模块
import uuid

# 导入 oss2 模块·
import oss2
# 导入 HTTPException 异常
from fastapi import HTTPException

# 导入 get_settings 配置
from fastapi_app.core.config import get_settings

# 定义最大头像字节数
MAX_AVATAR_BYTES = 1 * 1024 * 1024


def detect_image_type(content: bytes) -> tuple[str, str]:
    """
    检测图片类型
    :param content: 图片内容
    :return: 图片类型和扩展名
    """
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
    """
    获取 Bucket
    :return: Bucket
    """
    # 获取设置
    settings = get_settings()
    # 如果未配置对象存储，则抛出异常
    if not settings.oss_access_key_id or not settings.oss_access_key_secret:
        raise HTTPException(status_code=500, detail="未配置对象存储")
    # 创建认证
    auth = oss2.Auth(settings.oss_access_key_id, settings.oss_access_key_secret)
    # 创建 Bucket，使用认证、端点和桶名
    return oss2.Bucket(auth, settings.oss_endpoint, settings.oss_bucket)


def public_url(key: str) -> str:
    """
    获取公开 URL
    :param key: 对象键
    :return: 公开 URL
    """
    return f"{get_settings().oss_public_base_url.rstrip('/')}/{key.lstrip('/')}"


def upload_avatar(content: bytes, user_id: int) -> str:
    """
    上传头像
    :param content: 图片内容
    :param user_id: 用户 ID
    :return: 公开 URL
    """
    # 如果图片内容为空，则抛出异常
    if not content:
        # 抛出 HTTP 异常，状态码为 400，详情为 "请选择图片"
        raise HTTPException(status_code=400, detail="请选择图片")
    if len(content) > MAX_AVATAR_BYTES:
        # 抛出 HTTP 异常，状态码为 400，详情为 "头像不能超过 1MB"
        raise HTTPException(status_code=400, detail="头像不能超过 1MB")

    # 检测图片类型
    mime, ext = detect_image_type(content)
    # 生成对象键
    key = f"avatars/{user_id}/{uuid.uuid4().hex}{ext}"
    try:
        # 上传对象
        # 使用 Bucket 上传对象，使用对象键、图片内容、头信息
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
    """
    删除公开 URL
    :param url: 公开 URL
    :return: None
    """
    # 如果公开 URL 为空，则返回
    if not url:
        # 返回
        return
    # 获取设置
    base = get_settings().oss_public_base_url.rstrip("/")
    # 生成前缀
    prefix = f"{base}/"
    # 如果公开 URL 不以前缀开头，则返回
    if not url.startswith(prefix):
        # 返回
        return
    # 生成对象键
    key = url[len(prefix) :]
    if not key.startswith("avatars/"):
        # 返回
        return
    try:
        # 删除对象
        _bucket().delete_object(key)
    except Exception as exc:  # noqa: BLE001
        # 打印警告
        print(f"[warn] skip delete oss object: {exc}")
    except Exception as exc:  # noqa: BLE001
        print(f"[warn] skip delete oss object: {exc}")
