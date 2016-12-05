from flask import request, jsonify

from app import app
from models import User


@app.route('/api/v1/registration/', methods=['POST'])
def user_registration():
    username = request.form['username']
    password = request.form['password']
    user = User(username, password)
    result = user.save_to_db()
    return jsonify(result)


@app.route('/api/v1/login/', methods=['POST'])
def user_login():
    username = request.form['username']
    password = request.form['password']
    result = User.check_user_login(username, password)
    return jsonify(result)


@app.route('/api/v1/game_result/', methods=['POST'])
def game_result():
    username = request.form['username']
    score = request.form['score']
    user = User.get_user_by_username(username)
    if user is not None:
        user.update_score(score)
