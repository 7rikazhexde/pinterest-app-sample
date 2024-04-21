from flask import Flask, render_template, request, jsonify
import os
import base64
import requests

app = Flask(__name__)


class PinterestPinCreator:
    def __init__(self, access_token):
        self.api_url = "https://api-sandbox.pinterest.com/v5/pins"
        # self.api_url = "https://api.pinterest.com/v5/pins"
        self.headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }

    def create_pin(self, image_path, title, description, board_id):
        with open(image_path, "rb") as image_file:
            image_data = image_file.read()
            image_base64 = base64.b64encode(image_data).decode("utf-8")
            data = {
                "title": str(title),
                "description": str(description),
                "board_id": str(board_id),
                "media_source": {
                    "source_type": "image_base64",
                    "content_type": "image/jpeg",
                    "data": image_base64,
                },
            }
            response = requests.post(self.api_url, headers=self.headers, json=data)
            return response


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        warning, success = handle_pin_creation(request)
        if warning:
            return jsonify({"warning": warning})
        elif success:
            return jsonify({"success": success})
    return render_template("index.html")


def handle_pin_creation(request):
    warning = None
    success = None

    access_token = request.form.get("access_token", "").strip()
    board_id = request.form.get("board_id", "").strip()
    image_folder = request.form.get("image_folder", "").strip()

    if not access_token or not board_id or not image_folder:
        print("入力フィールドが空です。")
        warning = "投稿エラー: 必要な情報が指定されていません"
        return warning, success

    if not os.path.exists(image_folder):
        warning = f"投稿エラー: 指定された画像フォルダが存在しません: {image_folder}"
        return warning, success

    try:
        pinterest_pin_creator = PinterestPinCreator(access_token)
    except Exception as e:
        warning = f"投稿エラー: {str(e)}"
        return warning, success

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
            api_reference_url = (
                "https://developers.pinterest.com/docs/api/v5/#operation/pins/create"
            )
            warning = f"投稿エラー: {response.text}<br>API referenceを確認してください: <a href='{api_reference_url}' target='_blank'>{api_reference_url}</a>"
            break

    if all_success:
        success = "ピンの投稿が完了しました。"

    return warning, success


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
    username = "YOUR_USER_NAME"
    access_token = request.form.get("access_token", "").strip()
    access_token = "YOUR_ACCCESS_TOKEN(NO_SANDBOX)"
    url = f"https://api.pinterest.com/v5/boards/?owner={username}"
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(url, headers=headers)
    boards = []
    if response.status_code == 200:
        data = response.json()
        for board in data["items"]:
            boards.append(f"Board ID: {board['id']}, Board Name: {board['name']}")
    else:
        boards.append(
            f"Failed to retrieve boards. Status code: {response.status_code}, Error message: {response.text}"
        )
    return jsonify(boards)


if __name__ == "__main__":
    app.run(debug=True)
