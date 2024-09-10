# this code file is from https://github.com/DissonanceTK/MacReddy fork and is licensed under the MIT License.

"""
MIT License

Copyright (c) 2024 ILikeAI

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import os
import platform
import shutil
import tarfile
import zipfile
import requests
import subprocess

default_voice_model_url = "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/amy/medium/en_US-amy-medium.onnx"
default_voice_model_json_url = "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/amy/medium/en_US-amy-medium.onnx.json"

def download_file(url, save_path):
    print(f"Downloading from {url}")
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        total_length = int(r.headers.get("content-length", 0))
        dl = 0
        with open(save_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                if chunk:
                    dl += len(chunk)
                    f.write(chunk)
                    done = int(50 * dl / total_length)
                    print(
                        f"\r[{'=' * done}{' ' * (50-done)}] {dl/total_length*100:.2f}%",
                        end="",
                    )
    print("\nDownload complete.")


def extract_tar_gz(file_path, destination_dir):
    print(f"Extracting {file_path}")
    with tarfile.open(file_path, "r:gz") as tar:
        tar.extractall(path=destination_dir)
    print("Extraction complete.")


def extract_zip(file_path, destination_dir):
    print(f"Extracting {file_path}")
    with zipfile.ZipFile(file_path, "r") as zip_ref:
        zip_ref.extractall(destination_dir)
    print("Extraction complete.")


def setup_piper_tts():
    operating_system = platform.system()
    machine = platform.machine()
    url_base = "https://github.com/rhasspy/piper/releases/download/2023.11.14-2/"
    additional_url_base = (
        "https://github.com/rhasspy/piper-phonemize/releases/download/2023.11.14-4/"
    )
    binary_file, binary_name, extract_func = None, None, None
    additional_file = None

    if operating_system == "Windows":
        binary_file = "piper_windows_amd64.zip"
        extract_func = extract_zip
    elif operating_system == "Darwin":
        if machine == "x86_64":
            binary_file = "piper_macos_x64.tar.gz"
            additional_file = "piper-phonemize_macos_x64.tar.gz"
        elif machine == "arm64":
            binary_file = "piper_macos_aarch64.tar.gz"
            additional_file = "piper-phonemize_macos_aarch64.tar.gz"
        else:
            raise ValueError(f"Unsupported macOS architecture: {machine}")
        extract_func = extract_tar_gz
    elif operating_system == "Linux":
        if machine == "x86_64":
            binary_file = "piper_linux_x86_64.tar.gz"
        elif machine == "aarch64":
            binary_file = "piper_linux_aarch64.tar.gz"
        elif machine == "armv7l":
            binary_file = "piper_linux_armv7l.tar.gz"
        else:
            raise ValueError(f"Unsupported Linux architecture: {machine}")
        extract_func = extract_tar_gz
    else:
        raise ValueError(f"Unsupported operating system: {operating_system}")

    script_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(script_dir)
    binary_path = os.path.join(script_dir, binary_file)
    additional_path = (
        os.path.join(script_dir, additional_file) if additional_file else None
    )
    extraction_dir = os.path.join(script_dir, "piper_tts_extracted")
    destination_dir = os.path.join(parent_dir, "models", "piper_tts")

    # Download the binary
    download_url = url_base + binary_file
    download_file(download_url, binary_path)

    # Download the additional file for macOS if needed
    if additional_file:
        additional_url = additional_url_base + additional_file
        download_file(additional_url, additional_path)

    # Extract and setup binary
    if not os.path.exists(extraction_dir):
        os.makedirs(extraction_dir)

    extract_func(binary_path, extraction_dir)

    # Extract the additional file if downloaded
    if additional_file and additional_path:
        # Extract the lib folder from the additional tar.gz
        with tarfile.open(additional_path, "r:gz") as tar:
            members = [m for m in tar.getmembers() if "lib/" in m.name]
            tar.extractall(path=destination_dir, members=members)
        print("Extracted additional files to lib directory.")

    first_dir_path = next(
        (
            os.path.join(extraction_dir, d)
            for d in os.listdir(extraction_dir)
            if os.path.isdir(os.path.join(extraction_dir, d))
        ),
        None,
    )
    if not first_dir_path:
        raise Exception("No directory found within the extracted archive.")

    if not os.path.exists(destination_dir):
        os.makedirs(destination_dir)

    # Handle existing directories
    for item in os.listdir(first_dir_path):
        source_item_path = os.path.join(first_dir_path, item)
        destination_item_path = os.path.join(destination_dir, item)
        if os.path.isfile(source_item_path):
            shutil.copy(source_item_path, destination_item_path)
        elif os.path.isdir(source_item_path):
            if os.path.exists(destination_item_path):
                shutil.rmtree(destination_item_path)
            shutil.copytree(source_item_path, destination_item_path)

    # Adjust the paths to dylib files using install_name_tool on macOS
    if operating_system == "Darwin":
        piper_executable = os.path.join(
            destination_dir, "piper"
        )  # Assuming "piper" is the executable name
        lib_dir = os.path.join(destination_dir, "piper-phonemize", "lib")
        dylib_files = [
            "libespeak-ng.1.dylib",
            "libpiper_phonemize.1.dylib",
            "libonnxruntime.1.14.1.dylib",
        ]

        for dylib in dylib_files:
            dylib_path = os.path.join(lib_dir, dylib)
            subprocess.run(
                [
                    "install_name_tool",
                    "-change",
                    f"@rpath/{dylib}",
                    dylib_path,
                    piper_executable,
                ],
                check=True,
            )

    # Clean up the extraction directory and the downloaded binary file
    shutil.rmtree(extraction_dir)
    os.remove(binary_path)
    if additional_file and additional_path:
        os.remove(additional_path)

    print("Piper TTS setup completed successfully.")
    
def download_default_model():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(script_dir)
    voice_model_path = os.path.join(parent_dir, "models", "piper_voice", "en_US-amy-medium.onnx")
    voice_model_json_path = os.path.join(parent_dir, "models", "piper_voice", "en_US-amy-medium.onnx.json")
    
    download_file(default_voice_model_url, voice_model_path)
    download_file(default_voice_model_json_url, voice_model_json_path)
    print("Piper TTS default voice model downloaded successfully.")



if __name__ == "__main__":
    setup_piper_tts()
