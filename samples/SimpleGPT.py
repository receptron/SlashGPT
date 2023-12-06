#!/usr/bin/env python3
# python -m samples.SimpleGPT
import os
import platform
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), "../src"))

from slashgpt import ChatConfig, ChatSession, print_bot, print_error, print_function, print_info  # noqa: E402

if platform.system() == "Darwin":
    # So that input can handle Kanji & delete
    import readline  # noqa: F401


manifest = {
    "title": "名前判別",
    "bot": "名前判別",
    "source": "snakajima, https://st.benesse.ne.jp/ninshin/name/",
    "temperature": "0.0",
    "model": "gpt-3.5-turbo-16k-0613",
    "sample": "['誠'、'由美子','真由美','浩','修','明美','久美子','恵子','隆','達也','豊','由美','裕子','智子','豊','和彦','直樹']",
    "sample2022a": "['碧','陽葵','凛','陽翔','蒼','結菜','芽依','詩','朝陽','蓮']",
    "sample2022b": "['湊','陽菜','葵','莉子','紬','咲茉','結翔','悠真','陽向','樹']",
    "samplej": "東京の天気は？",
    "prompt": [
        "名前のリストを与えられたら、その全ての「読み(hiragana)」と「性別(sex)」をJSONで返してください。",
        "Input: ['太郎','花子']",
        "Output: [{'name':'太郎', 'hiragana':'たろう', 'sex':'male'},\n{'name':'花子', 'hiragana':'はなこ', 'sex':'female'}]",
    ],
}


class SimpleGPT:
    def __init__(self, config: ChatConfig, agent_name: str):
        self.session = ChatSession(config, manifest=manifest, agent_name=agent_name)
        print_info(f"Activating: {self.session.title()}")

        if self.session.intro_message:
            print_bot(self.session.botname(), self.session.intro_message)

    def process_llm(self, session):
        try:
            (res, function_call, _) = session.call_llm()

            if res:
                print_bot(self.session.botname(), res)

            if function_call:
                (
                    function_message,
                    function_name,
                    should_call_llm,
                ) = function_call.process_function_call(
                    session.manifest,
                    session.history,
                    None,
                )
                if function_message:
                    print_function(function_name, function_message)

                if should_call_llm:
                    self.process_llm()

        except Exception as e:
            print_error(f"Exception: Restarting the chat :{e}")

    def start(self):
        while True:
            question = input(f"\033[95m\033[1m{self.session.username()}: \033[95m\033[0m").strip()
            if question:
                self.session.append_user_question(self.session.manifest.format_question(question))
                self.process_llm(self.session)


if __name__ == "__main__":
    path = os.path.join(os.path.dirname(__file__), "../")
    config = ChatConfig(path)
    main = SimpleGPT(config, "names")
    if len(sys.argv) == 2 and sys.argv[1] == "test":
        sys.exit()
    main.start()
