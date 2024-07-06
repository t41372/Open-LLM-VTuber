import subprocess
import os


print("Fetching py whisper cpp from git...")

# Update/get all git submodule
subprocess.run(["git", "submodule", "update", "--init", "--recursive"], stdout=subprocess.DEVNULL)

input("pip install build? (Press enter to continue or press Ctrl+C to exit and not install build)")

# Install build
subprocess.run(["pip", "install", "build"])

print("Compiling pywhispercpp for coreml? (Press enter to continue or press Ctrl+C to exit and not compile)")

os.chdir("submodules/pywhispercpp")

# Set CMAKE_ARGS environment variable
os.environ["CMAKE_ARGS"] = "-DWHISPER_COREML=1"

# python -m build --wheel
subprocess.run(["python", "-m", "build", "--wheel"])

# pip install dist/<generated>.whl
import glob

# Find all .whl files in the dist directory
whl_files = glob.glob('dist/*.whl')

# Make sure there is only one .whl file
if len(whl_files) == 1:
    subprocess.run(["pip", "install", whl_files[0]])
else:
    if len(whl_files) == 0:
        print("Error: No .whl file found in dist directory. Exiting...")
    else:
        print("Error: More than one .whl file found in dist directory. Exiting...")



os.chdir("../..")

print("\nYou will need to get some models converted to coreml format. You can convert models by yourself. Check whisper.cpp documentation.\nYou can also download converted models from huggingface. From repo like this https://huggingface.co/chidiwilliams/whisper.cpp-coreml/tree/main \n Remember to decompress the .zip files and place the .mlmodelc file (folder) in asr/models folder. \n\n")








# import requests
# import sys

# def download_file(url, local_filename):
#     print(f"Downloading {url} to {local_filename}")
#     with requests.get(url, stream=True) as r:
#         r.raise_for_status()
#         total_length = int(r.headers.get('content-length'))
#         downloaded = 0
#         total_length_MB = total_length / (1024 * 1024)  # 将总长度转换为MB
#         with open(local_filename, 'wb') as f:
#             for chunk in r.iter_content(chunk_size=8192):
#                 f.write(chunk)
#                 downloaded += len(chunk)
#                 done = int(50 * downloaded / total_length)
#                 sys.stdout.write("\r[%s%s] %s%% of %.2f MB" % (
#                     '=' * done, ' ' * (50-done), 
#                     int(100 * downloaded / total_length), 
#                     total_length_MB))
#                 sys.stdout.flush()
#     print()  # 确保在下载完成后换行

# download_file("https://huggingface.co/distil-whisper/distil-medium.en/resolve/main/ggml-medium-32-2.en.bin", "asr/models/ggml-medium-32-2.en.bin")






