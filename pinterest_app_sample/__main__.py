from flask import Flask, render_template, request, jsonify, redirect, session
import os
import base64
import requests

import sys
from os.path import abspath, dirname, join

sys.path.append(
    abspath(join(dirname(__file__), "../pinterest-api-quickstart/python/src"))
)

from access_token import AccessToken
from api_config import ApiConfig
from oauth_scope import lookup_scope

app = Flask(__name__)
app.secret_key = "YOUR_APP_SEACRET_KEY"


class PinterestPinCreator:
    def __init__(self, access_token):
        self.api_url = "https://api-sandbox.pinterest.com/v5/pins"
        self.headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }

    def create_pin(self, image_path, title, description, board_id):
        with open(image_path, "rb") as image_file:
            image_data = image_file.read()
            image_base64 = base64.b64encode(image_data).decode("utf-8")
            data = {
                "board_id": board_id,
                "media_source": {
                    "source_type": "image_base64",
                    "content_type": "image/jpeg",
                    "data": image_base64,
                },
                "title": title,
                "description": description,
            }
            response = requests.post(self.api_url, headers=self.headers, json=data)
            return response


@app.route("/", methods=["GET", "POST"])
def index():
    access_token = session.get("access_token")
    if request.method == "POST":
        if access_token:
            board_id = request.form.get("board_id", "").strip()
            image_folder = request.form.get("image_folder", "").strip()

            if not board_id or not image_folder:
                print("入力フィールドが空です。")
                warning = "投稿エラー: 必要な情報が指定されていません"
                return jsonify({"warning": warning})

            if not os.path.exists(image_folder):
                warning = (
                    f"投稿エラー: 指定された画像フォルダが存在しません: {image_folder}"
                )
                return jsonify({"warning": warning})

            try:
                pinterest_pin_creator = PinterestPinCreator(access_token)
            except Exception as e:
                warning = f"投稿エラー: {str(e)}"
                return jsonify({"warning": warning})

            image_files = sorted(os.listdir(image_folder))
            all_success = True
            for image_file in image_files:
                if image_file == ".DS_Store":
                    continue
                image_path = os.path.join(image_folder, image_file)
                title = os.path.splitext(image_file)[0]
                description = ""
                response = pinterest_pin_creator.create_pin(
                    image_path, title, description, board_id
                )
                if response.status_code != 201:
                    all_success = False
                    break

            if all_success:
                success = "ピンの投稿が完了しました。"
                return jsonify({"success": success})
            else:
                warning = f"投稿エラー: {response.text}"
                return jsonify({"warning": warning})
        else:
            app_id = request.form.get("app_id")
            app_secret = request.form.get("app_secret")
            session["app_id"] = app_id
            session["app_secret"] = app_secret
            return redirect("/auth")
    return render_template("index.html", access_token=access_token)


@app.route("/auth", methods=["GET", "POST"])
def auth():
    if request.method == "POST":
        app_id = request.form.get("app_id")
        app_secret = request.form.get("app_secret")
        session["app_id"] = app_id
        session["app_secret"] = app_secret
    else:
        app_id = session.get("app_id")
        app_secret = session.get("app_secret")

    if app_id and app_secret:
        api_config = ApiConfig(verbosity=2)
        api_config.app_id = app_id
        api_config.app_secret = app_secret
        access_token = AccessToken(api_config)
        scopes = [
            lookup_scope("pins:read"),
            lookup_scope("pins:read_secret"),
            lookup_scope("pins:write"),
            lookup_scope("pins:write_secret"),
            lookup_scope("boards:read"),
            lookup_scope("boards:read_secret"),
            lookup_scope("boards:write"),
            lookup_scope("boards:write_secret"),
        ]
        access_token.oauth(scopes=scopes, refreshable=True)
        session["access_token"] = access_token.access_token
        return redirect("/")
    else:
        return redirect("/")


@app.route("/get_images", methods=["POST"])
def get_images():
    folder_path = request.form["folder_path"]
    image_names = []
    if os.path.exists(folder_path):
        image_files = sorted(os.listdir(folder_path))
        for file_name in image_files:
            if file_name.lower().endswith((".png", ".jpg", ".jpeg", ".gif")):
                image_names.append(file_name)
    return jsonify(image_names)


@app.route("/get_boards", methods=["POST"])
def get_boards():
    access_token = session.get("access_token")
    if access_token:
        username = "YOUR_USER_NAME"
        access_token = session.get("access_token")
        access_token = "YOUR_ACCCESS_TOKEN(NO_SANDBOX)"
        url = f"https://api.pinterest.com/v5/boards/?owner={username}"
        headers = {"Authorization": f"Bearer {access_token}"}
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            boards_data = response.json()["items"]
            boards = [
                {"id": board["id"], "name": board["name"]} for board in boards_data
            ]
            return jsonify(boards)
        else:
            return jsonify([])
    else:
        return jsonify([])


if __name__ == "__main__":
    app.run(debug=True)
