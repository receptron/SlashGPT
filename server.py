import os
import sys

from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request

sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

from slashgpt.chat_session import ChatSession  # noqa: E402
from slashgpt.chat_slash_config import ChatSlashConfig  # noqa: E402
from slashgpt.function.jupyter_runtime import PythonRuntime  # noqa: E402
from slashgpt.history.storage.file import ChatHistoryFileStorage  # noqa: E402
from slashgpt.utils.print import print_error  # noqa: E402

load_dotenv()

app = Flask(__name__)

current_dir = os.path.dirname(__file__)


# with open(current_dir + "/manifests/manifests.json", "r") as f:
#    manifests_manager = json.load(f)
# dir = manifests_manager["main"]["manifests_dir"]
# config = ChatSlashConfig(current_dir, current_dir + "/" + dir)

runtime = PythonRuntime(current_dir + "/output/notebooks")


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/manifests/<manifests>")
def manifests_list(manifests):
    config = ChatSlashConfig(current_dir, current_dir + "/manifests/" + manifests)

    return jsonify({"manifests": config.manifests})


def init_session(config, agent_name, manifest):
    engine = ChatHistoryFileStorage("sample", agent_name)
    session_id = engine.session_id
    session = ChatSession(config, manifest=manifest, agent_name=agent_name, history_engine=engine)
    return (session_id, session, engine)


def restore_session(config, agent_name, manifest, session_id):
    engine = ChatHistoryFileStorage("sample", agent_name, session_id=session_id)
    session = ChatSession(config, manifest=manifest, agent_name=agent_name, history_engine=engine, intro=False, restore=True)
    return (session, engine)


def process_llm(session):
    try:
        (res, function_call) = session.call_llm()

        if function_call:
            runtime.create_notebook(session.llm_model.name())
            (
                function_message,
                function_name,
                should_call_llm,
            ) = function_call.process_function_call(
                session.history,
                runtime,
                True,
            )
            if should_call_llm:
                process_llm(session)

    except Exception as e:
        print_error(f"Exception: Restarting the chat :{e}")


@app.route("/manifests/<manifests>/<agent>/talk", methods=["POST"])
@app.route("/manifests/<manifests>/<agent>/talk/<session_id>", methods=["POST"])
def talk(manifests, agent, session_id=None):
    config = ChatSlashConfig(current_dir, current_dir + "/manifests/" + manifests)
    m = config.manifests[agent]

    message = request.json["message"]
    print(m, message)

    if session_id is None:
        (session_id, session, engine) = init_session(config, agent, m)
        if message:
            # print(session)
            session.append_user_question(session.manifest.format_question(message))
            process_llm(session)
            # talk_to(message)
        print(message)
    else:
        (session, engine) = restore_session(config, agent, m, session_id)
        if message:
            session.append_user_question(session.manifest.format_question(message))
            process_llm(session)

    print(session_id)
    return jsonify({"session_id": session_id, "messages": engine.messages()})


if __name__ == "__main__":
    app.run(debug=True)
