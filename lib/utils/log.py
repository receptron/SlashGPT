import json
import os


def create_log_dir(manifest_key):
    if not os.path.isdir("output"):
        os.makedirs("output")
    if not os.path.isdir(f"output/{manifest_key}"):
        os.makedirs(f"output/{manifest_key}")


def save_log(manifest_key, messages, time):
    timeStr = time.strftime("%Y-%m-%d %H-%M-%S.%f")
    with open(f"output/{manifest_key}/{timeStr}.json", "w") as f:
        json.dump(messages, f, ensure_ascii=False)
