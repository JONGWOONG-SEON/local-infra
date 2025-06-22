import boto3
import os
import json
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Set, Optional, Type
from botocore.exceptions import ClientError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass(frozen=True)
class S3Config:
    endpoint: str
    access_key: str
    secret_key: str
    bucket: str
    track_key: str

    @staticmethod
    def get_env() -> "S3Config":
        return S3Config(
            endpoint=os.environ["MINIO_ENDPOINT"],
            access_key=os.environ["MINIO_ACCESS_KEY"],
            secret_key=os.environ["MINIO_SECRET_KEY"],
            bucket= "process",
            track_key= "process_files.json",
        )

class MetaStore(ABC):
    @abstractmethod
    def load_processed_files(self) -> Set[str]:
        pass

    @abstractmethod
    def save_processed_files(self, files: Set[str]) -> None:
        pass
        
def ImplementS3Config(cls: Type) -> Type:
    origin_init = cls.__init__

    def __init__(self, config: S3Config, client: Optional[boto3.client] = None, *args, **kwargs):
        actual_client = boto3.client(
            "s3",
            endpoint_url=f"http://{config.endpoint}",
            aws_access_key_id=config.access_key,
            aws_secret_access_key=config.secret_key,
        )
        origin_init(self, config, actual_client, *args, **kwargs)

    cls.__init__ = __init__
    return cls

@ImplementS3Config
class S3MetaStore(MetaStore):
    def __init__(self, config: S3Config, client: boto3.client):
        self._cfg = config
        self._client = client

    def __call__(self):
        return self._client

    def load_processed_files(self) -> Set[str]:
        try:
            resp = self._client.get_object(
                Bucket=self._cfg.bucket,
                Key=self._cfg.track_key
            )
            payload = resp["Body"].read().decode('utf-8')
            data = json.loads(payload)
            return set(data)
        except ClientError as e:
            code = e.response.get("Error", {}).get("Code", "")
            if code == "NoSuchKey":
                logger.info(
                    "Track key '%s' not found in bucket '%s'. Initializing empty set.",
                    self._cfg.track_key, self._cfg.bucket
                )
                return set()
            logger.exception("Error loading processed files from Minio")
            raise

    def save_processed_files(self, files: Set[str]) -> None:
        try:
            body = json.dumps(sorted(files))
            self._client.put_object(
                Bucket=self._cfg.bucket,
                Key=self._cfg.track_key,
                Body=body
            )
        except Exception:
            logger.exception("Error saving processed files to Minio")
            raise

