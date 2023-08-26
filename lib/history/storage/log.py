import json
import os


def create_log_dir(base_dir, manifest_key):
    if not os.path.isdir(base_dir):
        os.makedirs(base_dir)
    if not os.path.isdir(f"{base_dir}/{manifest_key}"):
        os.makedirs(f"{base_dir}/{manifest_key}")


def save_log(base_dir, manifest_key, messages, time):
    timeStr = time.strftime("%Y-%m-%d %H-%M-%S.%f")
    with open(f"{base_dir}/{manifest_key}/{timeStr}.json", "w") as f:
        json.dump(messages, f, ensure_ascii=False, indent=2)
