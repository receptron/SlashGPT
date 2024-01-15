import json
import os
import re
import sys

from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request

sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

from config.llm_config import llm_engine_configs, llm_models  # noqa: E402
from slashgpt import ChatConfigWithManifests, ChatHistoryFileStorage, ChatSession, PythonRuntime, print_error  # noqa: E402

load_dotenv()

app = Flask(__name__)

current_dir = os.path.dirname(__file__)


with open(current_dir + "/manifests/manifests.json", "r") as f:
    manifests_manager = json.load(f)
# dir = manifests_manager["main"]["manifests_dir"]
# config = ChatConfigWithManifests(current_dir, current_dir + "/" + dir)

runtime = PythonRuntime(current_dir + "/output/notebooks")


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/manifests")
def manifests():
    return jsonify({"modes": manifests_manager})


@app.route("/functions")
def functions():
    path = current_dir + "/resources/functions"
    files = os.listdir(path)
    functions = {}
    for file in files:
        if re.search(r"\.json$", file):
            with open(f"{path}/{file}", "r", encoding="utf-8") as f:  # encoding add for Win
                functions[file.split(".")[0]] = json.load(f)

    return jsonify({"functions": functions})


@app.route("/modules")
def modules():
    path = current_dir + "/resources/module"
    files = os.listdir(path)
    functions = {}
    for file in files:
        if re.search(r"\.py$", file):
            with open(f"{path}/{file}", "r", encoding="utf-8") as f:  # encoding add for Win
                functions[file.split(".")[0]] = f.read()

    return jsonify({"modules": functions})


@app.route("/manifests/<manifests>")
def manifests_list(manifests):
    config = ChatConfigWithManifests(current_dir, current_dir + "/manifests/" + manifests, llm_models, llm_engine_configs)

    return jsonify({"manifests": config.manifests})


@app.route("/llms/<manifests>")
def llm_list(manifests):
    print(manifests)
    config = ChatConfigWithManifests(current_dir, current_dir + "/manifests/" + manifests, llm_models, llm_engine_configs)
    return jsonify({"llms": list(config.llm_models.keys())})


def init_session(config, agent_name, manifest, llm):
    engine = ChatHistoryFileStorage("sample", agent_name)
    session_id = engine.session_id
    session = ChatSession(config, manifest=manifest, agent_name=agent_name, history_engine=engine)
    if llm:
        session.set_llm_model(llm)
    return (session_id, session, engine)


def restore_session(config, agent_name, manifest, session_id, llm):
    engine = ChatHistoryFileStorage("sample", agent_name, session_id=session_id)
    session = ChatSession(config, manifest=manifest, agent_name=agent_name, history_engine=engine, intro=False, restore=True)
    if llm:
        session.set_llm_model(llm)
    return (session, engine)


def process_llm(session):
    try:
        (res, function_call, _) = session.call_llm()

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
    config = ChatConfigWithManifests(current_dir, current_dir + "/manifests/" + manifests, llm_models, llm_engine_configs)
    config.verbose = True
    m = config.manifests[agent]

    message = request.json["message"]
    llm = request.json.get("llm")
    print(llm)
    # print(m, message)
    model = None
    if llm:
        print(llm_models)
        model = config.get_llm_model_from_key(llm)
    if session_id is None:
        (session_id, session, engine) = init_session(config, agent, m, model)
        if message:
            # print(session)
            session.append_user_question(message)
            process_llm(session)
            # talk_to(message)
        print(message)
    else:
        (session, engine) = restore_session(config, agent, m, session_id, model)
        if message:
            session.append_user_question(message)
            process_llm(session)

    return jsonify({"session_id": session_id, "messages": engine.messages()})


if __name__ == "__main__":
    app.run(debug=True, port=5001)
    # app.run(debug=True)
