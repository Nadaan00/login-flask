import os
from os.path import join, dirname
from dotenv import load_dotenv
from flask import Flask, render_template, request, jsonify
from pymongo import MongoClient

from flask import (
    Flask,
    render_template,
    jsonify,
    request,
    session,
    redirect,
    url_for
)
from pymongo import MongoClient
import jwt
from datetime import datetime, timedelta
import hashlib

dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

MONGODB_URI = os.environ.get("MONGODB_URI")
DB_NAME =  os.environ.get("DB_NAME")

client = MongoClient(MONGODB_URI)
db = client[DB_NAME]

app = Flask(__name__)

SECRET_KEY = 'SPARTA'

@app.route('/', methods=['GET'])
def home():
    token_receive = request.cookies.get("mytoken")
    try:
        payload = jwt.decode(
            token_receive,
            SECRET_KEY,
            algorithms=["HS256"]
        )
        user_info = db.user.find_one({"id": payload["id"]})
        return render_template(
            "index.html",
            nickname=user_info["nick"]
        )
    except jwt.ExpiredSignatureError:
        return redirect(url_for(
            "login",
            msg="Your login token has expired")
        )
    except jwt.exceptions.DecodeError:
        return redirect(url_for(
            "login",
            msg="There was an issue logging you in")
        )

@app.route("/login")
def login():
    msg = request.args.get("msg")
    return render_template("login.html", msg=msg)

@app.route("/register")
def register():
    return render_template("register.html")

@app.route("/api/register", methods=["POST"])
def api_register():
    id_receive = request.form["id_give"]
    pw_receive = request.form["pw_give"]
    nickname_receive = request.form["nickname_give"]

    existing_user = db.user.find_one({"id": id_receive})
    if existing_user:
        return jsonify({"result": "fail", "msg": f"An acount with id '{id_receive}' is already. Please Login!"})

    pw_hash = hashlib.sha256(pw_receive.encode("utf-8")).hexdigest()

    db.user.insert_one({
        "id": id_receive,
        "pw": pw_hash,
        "nick": nickname_receive
    })

    return jsonify({"result": "success"})

@app.route("/api/login", methods=["POST"])
def api_login():
    id_receive = request.form["id_give"]
    pw_receive = request.form["pw_give"]
    pw_hash = hashlib.sha256(pw_receive.encode("utf-8")).hexdigest()
    result = db.user.find_one({"id": id_receive, "pw": pw_hash})
    if result is not None:
        payload = {
            "id": id_receive,
            "exp": datetime.utcnow() + timedelta(seconds=5),
        }
        token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
        return jsonify({"result": "success", "token": token})
    else:
        return jsonify({"result": "fail", "msg": "Either your email or your password is incorrect"})

    
@app.route("/api/nick", methods=["GET"])
def api_valid():
    token_receive = request.cookies.get("mytoken")

    try:
        payload = jwt.decode(
            token_receive,
            SECRET_KEY,
            algorithms=["HS256"]
        )
        print(payload)
        userinfo = db.user.find_one({
            "id": payload["id"]},
            {"_id": 0}
        )
        return jsonify({
            "result": "success",
            "nickname": userinfo["nick"]}
            )
    except jwt.ExpiredSignatureError:
        msg = "Your token has expired"
        return jsonify({
            "result": "fail",
            "msg": msg}
            )
    except jwt.exceptions.DecodeError:
        msg = "There was an error while logging you in"
        return jsonify({
            "result": "fail",
            "msg": msg}
        )
          

if __name__ == '__main__':
    app.run('0.0.0.0', port=5000, debug=True)