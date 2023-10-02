import json

import yaml

with open(f"foo.json", "r", encoding="utf-8") as f:  # encoding add for Win
    data = json.load(f)
    print(data)
    with open("foo.yml", "w") as f:
        # Dump the dictionary to the YAML file
        yaml.dump(data, f)
