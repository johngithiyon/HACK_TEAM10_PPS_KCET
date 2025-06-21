from flask import Flask, render_template, request, redirect, url_for, jsonify
import json
from fuzzywuzzy import process

app = Flask(__name__)

# Load Q&A dataset
with open("qa_dataset.json") as f:
    qa_pairs = json.load(f)
questions = [pair["question"] for pair in qa_pairs]

# Home page: Learning style form
@app.route('/')
def index():
    return render_template('index.html')

# Form handler: Redirect based on work type
@app.route('/submit', methods=['POST'])
def submit():
    work_type = request.form.get('work_type')

    if work_type == "individual":
        return redirect(url_for('chatbot'))
    elif work_type == "group":
        return redirect(url_for('topics'))
    else:
        return "Invalid work type selected"

# Group users: Show topics
@app.route('/topics')
def topics():
    return render_template("topics.html")

# Individual users: Chatbot page
@app.route('/chatbot')
def chatbot():
    return render_template("chatbot.html")

# Chatbot API: Process chat messages
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

if __name__ == '__main__':
    app.run(debug=True)
