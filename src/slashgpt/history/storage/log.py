import json
import os


def create_log_dir(base_dir: str, agent_name: str):
    if not os.path.isdir(base_dir):
        os.makedirs(base_dir)
    if not os.path.isdir(f"{base_dir}/{agent_name}"):
        os.makedirs(f"{base_dir}/{agent_name}")


def save_log(base_dir: str, agent_name: str, context: dict, time):
    timeStr = time.strftime("%Y-%m-%d %H-%M-%S.%f")
    with open(f"{base_dir}/{agent_name}/{timeStr}.json", "w") as f:
        json.dump(context, f, ensure_ascii=False, indent=2)
