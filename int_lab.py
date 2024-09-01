from main import OpenLLMVTuberMain
import yaml
import threading

if __name__ == "__main__":
    with open("conf.yaml", "rb") as f:
        config = yaml.safe_load(f)

    vtuber_main = OpenLLMVTuberMain(config)
    while True:
        threading.Thread(target=vtuber_main.conversation_chain).start()
        
        if input(">>> say i to interrupt: ") == "i":
            print("\n\n!!!!!!!!!! interrupt !!!!!!!!!!!!...\n")
            vtuber_main.interrupt()
            