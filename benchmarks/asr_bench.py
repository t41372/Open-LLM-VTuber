from asr.asr_factory import ASRFactory

import timeit
from scipy.io.wavfile import read
import numpy as np

audio = read("benchmarks/test-16b-caps.wav")
audio = np.array(audio[1], dtype=np.float32)
# Standardize the volume of the audio
audio = audio / np.max(np.abs(audio))



exec_round = 3




### ==== Whisper CPP (abdeladim-s/pywhispercpp) ====


def init_cpp():
    print("\n\n### CPP Init")
    whispercpp = ASRFactory.get_asr_system(
        "WhisperCPP",
        model_name="medium",
        model_dir="asr/models",
        language="en",
        print_realtime=False,
        print_progress=False,
        n_threads=6,
    )
    print("\n\n ======= Warmup CPP once ======= ")
    print(whispercpp.transcribe_np(audio))
    print("======= DoneW CPP once =======")
    return whispercpp

whispercpp = init_cpp()

def run_whisper():
    print("\n\n ======= Start CPP once =======")
    print(whispercpp.transcribe_np(audio))
    print(" ======= Done CPP once =======")

result_cpp = timeit.timeit(run_whisper, number=exec_round)
print("\n\n =======  CPP Result =======")
print(f"Total: {result_cpp}s, Avg: {result_cpp/exec_round}s")


###  ==== Faster Whisper ==== ###

print("\n\n### ===  FW  === ###")

def init_fw():
    print("\n\n### FW Init")
    fw = ASRFactory.get_asr_system(
        "Faster-Whisper",
        model_path="distil-medium.en",
        language="en",
        device="auto",
    )
    print("\n\n ======= Warmup FW once ======= ")
    print(fw.transcribe_np(audio))
    print("======= DoneW FW once =======")
    return fw

fw = init_fw()

def run_fw():
    print("\n\n ======= Start FW once =======")
    print(fw.transcribe_np(audio))
    print(" ======= Done FW once =======")

result_fw = timeit.timeit(run_fw, number=exec_round)
print("\n\n =======  FW Result =======")
print(f"Total: {result_fw}s, Avg: {result_fw/exec_round}s")



###  ==== OAI ==== ###



# def bench_fw():
#     print("\n\n ======= Start FW once =======")
#     print(fw.transcribe_np(audio))
#     print(" ======= Done FW once =======")


# def init_oai():
#     print("\n\n### OAI Init")
#     return ASRFactory.get_asr_system(
#         system_name="Whisper",
#         name="medium",
#         download_root="asr/cache",
#         device="cpu",
#     )


# result_oai = 0
# whisper = init_oai()
# def run_whisper():
#     print("\n\n ======= Start OAI once =======")
#     print(whisper.transcribe_np(audio))
#     print(" ======= Done OAI once =======")
# result_oai = timeit.timeit(run_whisper, number=3)

# print("\n\n =======  OAI Result =======")
# print(result_oai)

# result_oai = timeit.timeit(run_whisper, number=3)
# result_faster = timeit.timeit(bench_fw, number=3)

# print(f"OAI: {result_oai}")
# print(f"FW: {result_faster}")
# print(f"CPP: {result_cpp}")



