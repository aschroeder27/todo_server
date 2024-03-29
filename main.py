import json
import logging
import os.path
import uuid

from flask import Flask, request, abort, jsonify

file = "data.json"
users_file = "users.json"

app = Flask(__name__)

todo_lists = {}

users = {}


@app.after_request
def apply_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET,POST,PUT,DELETE'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    return response


@app.route("/todo-list", methods=['POST', 'GET'])
def create_list():
    global todo_lists
    if request.method == "POST":
        body = request.get_json()
        list_id = create_list_id()
        logging.info(f"Created new List, id = {list_id}")
        body["id"] = list_id

        if "entries" not in body:
            body["entries"] = {}

        if "name" not in body:
            abort(400)

        todo_lists[list_id] = body
        save_data()

        return body
    else:
        return jsonify([get_list(ls["id"], False) for ls in todo_lists.values()])


@app.route("/todo-list/<list_id>", methods=['GET', 'DELETE'])
def get_list(list_id, called_ext=True):
    global todo_lists
    if request.method == 'GET' or not called_ext:
        l: dict = todo_lists[list_id].copy()

        l["entries"] = list(l["entries"].values())

        return l
    elif request.method == 'DELETE':
        popped = todo_lists.pop(list_id, None)
        if popped is None:
            abort(404)
        else:
            save_data()

    return "OK"


@app.route("/todo-list/<list_id>/entry", methods=['POST'])
def add_entry(list_id):
    global todo_lists
    body: dict = request.get_json()
    if "user_id" not in body.keys() or not body["user_id"] in users.keys():
        abort(406)
    body["id"] = create_entry_id(list_id)
    logging.info(f"Added entry {body['id']} to list {list_id}")
    todo_lists[list_id]["entries"][body["id"]] = body
    save_data()
    return body


@app.route("/todo-list/<list_id>/entry/<entry_id>", methods=['PUT', 'DELETE'])
def put_entry(list_id, entry_id):
    global todo_lists
    if request.method == 'PUT':
        body: dict = request.get_json()
        if list_id not in todo_lists.keys():
            abort(404)
        if entry_id not in todo_lists[list_id]["entries"]:
            abort(404)
        if "user" not in body:
            abort(406)
        if not body["user"] in users.keys():
            abort(406)
        body["id"] = entry_id
        todo_lists[list_id]["entries"][entry_id] = body
        save_data()
        return body
    else:
        if list_id not in todo_lists.keys():
            abort(404)
        popped = todo_lists[list_id]["entries"].pop(entry_id, None)
        if popped is None:
            abort(404)
        save_data()
        return "OK"


@app.route("/user", methods=['GET', 'POST'])
def user():
    global users
    if request.method == "GET":
        return jsonify(list(users.values()))
    else:
        body = request.get_json()
        body["id"] = create_user_id()
        users[body["id"]] = body
        save_users()
        return body


@app.route("/user/<user_id>", methods=['DELETE'])
def delete_user(user_id):
    popped = users.pop(user_id, None)
    if popped is None:
        abort(404)
    else:
        save_users()
    return "OK"


# used to persist the storage to a file
def load_data():
    global todo_lists, file
    try:
        if os.path.exists(file):
            with open(file, 'r') as f:
                lines = f.read()
                todo_lists = json.loads(lines)
    except:
        logging.error(f"Unable to read '{file}'")
        todo_lists = {}
        save_data()
    logging.info(f"Loaded lists: {todo_lists}")


def save_data():
    global todo_lists
    with open(file, 'w') as f:
        f.writelines(json.dumps(todo_lists, indent=4))


def load_users():
    global users, users_file
    try:
        if os.path.exists(users_file):
            with open(users_file, 'r') as f:
                lines = f.read()
                users = json.loads(lines)
    except:
        logging.error(f"Unable to read '{users_file}'")
        users = {}
        save_users()
    logging.info(f"Loaded users: {users}")


def save_users():
    global users
    with open(users_file, 'w') as f:
        f.writelines(json.dumps(users, indent=4))


def create_list_id():
    list_id = generate_id()
    while list_id in todo_lists.keys():
        list_id = generate_id()
    return list_id


def create_entry_id(list_id: str):
    entry_id = generate_id()
    while entry_id in todo_lists[list_id]["entries"].keys():
        entry_id = generate_id()
    return entry_id


def create_user_id():
    user_id = generate_id()
    while user_id in users.keys():
        user_id = generate_id()
    return user_id


def generate_id():
    return str(uuid.uuid4())


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format='[%(asctime)s] %(levelname)-8s %(message)s')
    load_data()
    load_users()
    app.run('0.0.0.0', port=8080)
