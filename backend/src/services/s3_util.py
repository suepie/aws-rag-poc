"""S3 presigned URL とオブジェクト操作。"""
from __future__ import annotations

import os

import boto3

_s3 = boto3.client("s3")

EXCEL_BUCKET = os.environ.get("EXCEL_BUCKET", "")
PRESIGN_EXPIRES = int(os.environ.get("PRESIGN_EXPIRES", "900"))  # 15 分


def presign_put(key: str, content_type: str) -> str:
    return _s3.generate_presigned_url(
        "put_object",
        Params={"Bucket": EXCEL_BUCKET, "Key": key, "ContentType": content_type},
        ExpiresIn=PRESIGN_EXPIRES,
    )


def presign_get(key: str) -> str:
    return _s3.generate_presigned_url(
        "get_object",
        Params={"Bucket": EXCEL_BUCKET, "Key": key},
        ExpiresIn=PRESIGN_EXPIRES,
    )


def get_bytes(key: str) -> bytes:
    obj = _s3.get_object(Bucket=EXCEL_BUCKET, Key=key)
    return obj["Body"].read()


def put_bytes(key: str, data: bytes, content_type: str) -> None:
    _s3.put_object(Bucket=EXCEL_BUCKET, Key=key, Body=data, ContentType=content_type)


def head_exists(key: str) -> bool:
    try:
        _s3.head_object(Bucket=EXCEL_BUCKET, Key=key)
        return True
    except _s3.exceptions.ClientError:
        return False
