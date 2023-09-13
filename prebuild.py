import shutil

shutil.copytree("manifests", "src/slashgpt/manifests", dirs_exist_ok=True)
shutil.copytree("resources", "src/slashgpt/resources", dirs_exist_ok=True)
shutil.copytree("test", "src/slashgpt/test", dirs_exist_ok=True)
shutil.copytree("data", "src/slashgpt/data", dirs_exist_ok=True)
