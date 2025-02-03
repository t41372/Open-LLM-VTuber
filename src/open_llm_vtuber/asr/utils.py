import os
import requests
import tarfile
from pathlib import Path
from tqdm import tqdm
from loguru import logger


def get_github_asset_url(owner, repo, release_tag, filename_without_ext):
    """
    Fetch the URL of a GitHub release asset by its filename (without extension).

    Args:
        owner (str): The owner of the repository.
        repo (str): The name of the repository.
        release_tag (str): The tag of the release.
        filename_without_ext (str): The filename to search for (without extension).

    Returns:
        str: The download URL of the matched asset, or None if no match is found.
    """
    url = f"https://api.github.com/repos/{owner}/{repo}/releases/tags/{release_tag}"
    headers = {}  # Add authentication headers if needed

    try:
        # Make a GET request to fetch release data
        response = requests.get(url, headers=headers)
        response.raise_for_status()

        # Parse the JSON response
        release_data = response.json()
        assets = release_data.get("assets", [])

        # Look for a matching file
        for asset in assets:
            if asset["name"].startswith(filename_without_ext):
                logger.info(f"Match found: {asset['name']}")
                return asset["browser_download_url"]

        # If no match found, log the error
        logger.error(
            f"No match found for filename: {filename_without_ext} in release {release_tag}."
        )
        return None

    except requests.exceptions.RequestException as e:
        logger.error(f"An error occurred while fetching release data: {e}")
        return None


def download_and_extract(url: str, output_dir: str) -> Path:
    """
    Download a file from a URL and extract it if it is a tar.bz2 archive.

    Args:
        url (str): The URL to download the file from.
        output_dir (str): The directory to save the downloaded file.

    Returns:
        Path: Path to the extracted directory if it's a tar.bz2 file,
             otherwise Path to the downloaded file.
    """
    # Create the output directory if it doesn't exist
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    # Get the file name from the URL
    file_name = url.split("/")[-1]
    file_path = os.path.join(output_dir, file_name)

    # Extract the root directory name from the filename (removing .tar.bz2)
    root_dir = file_name.replace(".tar.bz2", "")
    extracted_dir_path = Path(output_dir) / root_dir

    # Check if the extracted directory already exists
    if extracted_dir_path.exists():
        logger.info(
            f"✅ The directory {extracted_dir_path} already exists. I would assume that the model is already downloaded and we are ready to go. Skipping download and extraction."
        )
        return extracted_dir_path

    # Download the file
    logger.info(f"🏃‍♂️Downloading {url} to {file_path}...")
    response = requests.get(url, stream=True)
    response.raise_for_status()  # Raise an error for bad status codes
    total_size = int(response.headers.get("content-length", 0))
    logger.debug(f"Total file size: {total_size / 1024 / 1024:.2f} MB")

    with (
        open(file_path, "wb") as f,
        tqdm(
            desc=file_name,
            total=total_size,
            unit="iB",
            unit_scale=True,
            unit_divisor=1024,
        ) as pbar,
    ):
        for chunk in response.iter_content(chunk_size=8192):
            size = f.write(chunk)
            pbar.update(size)

    logger.info(f"Downloaded {file_name} successfully.")

    # Extract the tar.bz2 file
    if file_name.endswith(".tar.bz2"):
        logger.info(f"Extracting {file_name}...")
        with tarfile.open(file_path, "r:bz2") as tar:
            tar.extractall(path=output_dir)
        logger.info("Extraction completed.")

        # Delete the compressed file
        os.remove(file_path)
        logger.debug(f"Deleted the compressed file: {file_name}")

        return extracted_dir_path
    else:
        logger.warning("The downloaded file is not a tar.bz2 archive.")
        return Path(file_path)


def check_and_extract_local_file(url: str, output_dir: str) -> Path | None:
    """
    新增方法：检查本地是否已存在压缩包，存在则直接解压

    Args:
        url (str): 原始下载URL（用于解析文件名）
        output_dir (str): 模型存储目录

    Returns:
        Path | None: 若存在压缩包并解压成功返回路径，否则返回None
    """
    # 从URL解析文件名
    file_name = url.split("/")[-1]
    compressed_path = Path(output_dir) / file_name

    # 如果压缩包存在且是tar.bz2格式
    if compressed_path.exists() and file_name.endswith(".tar.bz2"):
        logger.info(f"🔍 发现本地压缩包: {compressed_path}")
        extracted_dir = compressed_path.parent / file_name.replace(".tar.bz2", "")

        if extracted_dir.exists():
            logger.info(f"✅ 解压目录已存在: {extracted_dir}，无需操作")
            return extracted_dir

        try:
            logger.info("⏳ 正在解压本地文件...")
            with tarfile.open(compressed_path, "r:bz2") as tar:
                tar.extractall(path=output_dir)
            logger.success(f"解压完成至: {extracted_dir}")
            os.remove(compressed_path)  # 解压后删除压缩包
            return extracted_dir
        except Exception as e:
            logger.error(f"解压失败: {str(e)}")
            return None

    # 如果压缩包不存在或格式不符
    return None


if __name__ == "__main__":
    url = "https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/sherpa-onnx-sense-voice-zh-en-ja-ko-yue-2024-07-17.tar.bz2"
    output_dir = "./models"

    # 先尝试本地解压
    local_result = check_and_extract_local_file(url, output_dir)

    # 本地没有则下载
    if local_result is None:
        logger.info("未找到本地压缩包，开始下载...")
        download_and_extract(url, output_dir)
    else:
        logger.info("已通过本地文件完成解压")