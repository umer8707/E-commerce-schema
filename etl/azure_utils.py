import os
from azure.storage.blob import BlobServiceClient


def _client(account: str, key: str) -> BlobServiceClient:
    conn_str = (
        f"DefaultEndpointsProtocol=https;"
        f"AccountName={account};"
        f"AccountKey={key};"
        f"EndpointSuffix=core.windows.net"
    )
    return BlobServiceClient.from_connection_string(conn_str)


def upload_dir(local_dir: str, container: str, prefix: str, account: str, key: str) -> None:
    client = _client(account, key)
    uploaded = 0
    for root, _, files in os.walk(local_dir):
        for fname in files:
            if fname.startswith(".") or fname == "_SUCCESS":
                continue
            local_path = os.path.join(root, fname)
            rel_path = os.path.relpath(local_path, local_dir).replace("\\", "/")
            blob_name = f"{prefix}/{rel_path}"
            blob_client = client.get_blob_client(container=container, blob=blob_name)
            with open(local_path, "rb") as f:
                blob_client.upload_blob(f, overwrite=True)
            uploaded += 1
    print(f"Uploaded {uploaded} file(s) → azure://{container}/{prefix}")


def download_dir(container: str, prefix: str, local_dir: str, account: str, key: str) -> None:
    client = _client(account, key)
    os.makedirs(local_dir, exist_ok=True)
    container_client = client.get_container_client(container)
    downloaded = 0
    for blob in container_client.list_blobs(name_starts_with=prefix):
        rel_path = os.path.relpath(blob.name, prefix).replace("\\", "/")
        if rel_path in (".", "..") or blob.name.endswith("/"):
            continue
        local_path = os.path.join(local_dir, rel_path)
        os.makedirs(os.path.dirname(local_path), exist_ok=True)
        blob_client = client.get_blob_client(container=container, blob=blob.name)
        with open(local_path, "wb") as f:
            f.write(blob_client.download_blob().readall())
        downloaded += 1
    print(f"Downloaded {downloaded} file(s) ← azure://{container}/{prefix}")
