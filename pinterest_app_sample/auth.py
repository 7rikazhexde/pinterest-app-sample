from flask import Flask, render_template, request, redirect, session

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


@app.route("/", methods=["GET", "POST"])
def index():
    access_token_str = session.get("access_token")
    if request.method == "POST":
        app_id = request.form.get("app_id")
        app_secret = request.form.get("app_secret")
        session["app_id"] = app_id
        session["app_secret"] = app_secret
        return redirect("/auth")
    return render_template("index.html", access_token=access_token_str)


@app.route("/auth", methods=["GET"])
def auth():
    app_id = session.get("app_id")
    app_secret = session.get("app_secret")
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


if __name__ == "__main__":
    app.run(debug=True)
