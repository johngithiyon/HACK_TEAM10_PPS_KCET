from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_socketio import SocketIO, emit, join_room
import json
import re
from fuzzywuzzy import process

app = Flask(__name__)
socketio = SocketIO(app)

# Load Q&A dataset
with open("qa_dataset.json") as f:
    qa_pairs = json.load(f)
questions = [pair["question"] for pair in qa_pairs]

# Store answers per room
room_answers = {}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/submit', methods=['POST'])
def submit():
    work_type = request.form['work_type']
    if work_type == "individual":
        return redirect(url_for('chatbot'))
    elif work_type == "group":
        return redirect(url_for('topics_page', work="group"))
    return "Invalid work type selected"

@app.route('/topics/<work>')
def topics_page(work):
    return render_template('topics.html', work=work)

@app.route('/learn/<topic>')
def learning_mode(topic):
    work = request.args.get('work', 'group')
    if work == 'group':
        return render_template('quiz.html', topic=topic)
    return redirect(url_for('chatbot'))

@app.route('/chatbot')
def chatbot():
    return render_template('chatbot.html')

@app.route('/chat', methods=['POST'])
def chat():
    data = request.get_json()
    user_input = data.get("message", "").lower().strip()
    if not user_input:
        return jsonify({"response": "Please ask a question."})
    best_match, score = process.extractOne(user_input, questions)
    if score > 70:
        for pair in qa_pairs:
            if pair["question"] == best_match:
                return jsonify({"response": pair["answer"]})
    return jsonify({"response": "Sorry, I don't understand that question."})

# === SocketIO Events ===
@socketio.on('join')
def on_join(data):
    room = data['room']
    username = data.get('username', 'Unknown')
    join_room(room)

    if room not in room_answers:
        room_answers[room] = {}

    emit('status', {'msg': f"{username} joined room {room}"}, room=room)

@socketio.on('answer')
def on_answer(data):
    room = data['room']
    username = data['username']
    answer = data['answer']

    if room not in room_answers:
        room_answers[room] = {}

    room_answers[room][username] = answer

    if len(room_answers[room]) == 2:
        correct_answer = "4"  # Static answer for demo
        results = []
        for user, ans in room_answers[room].items():
            status = "✅ Correct" if ans.strip() == correct_answer else "❌ Wrong"
            results.append(f"{user}: {ans} - {status}")

        emit('results', {
            'correct': correct_answer,
            'details': results
        }, room=room)

        room_answers[room] = {}  # Reset room state

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
