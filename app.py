from flask import Flask, request, jsonify, render_template
from pymongo import MongoClient
from datetime import datetime

app = Flask(__name__)

# MongoDB setup
client = MongoClient("mongodb://localhost:27017/")
db = client["github_events"]
collection = db["events"]

# Webhook endpoint
@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json
    event_type = request.headers.get('X-GitHub-Event', 'ping')
    timestamp = datetime.utcnow()

    # Parse event data
    event = {
        "author": data.get("sender", {}).get("login", "Unknown"),
        "event_type": event_type,
        "from_branch": data.get("pull_request", {}).get("head", {}).get("ref", ""),
        "to_branch": data.get("pull_request", {}).get("base", {}).get("ref", ""),
        "timestamp": timestamp,
    }
    collection.insert_one(event)
    return jsonify({"status": "success"}), 200

# UI endpoint
@app.route('/')
def index():
    events = collection.find().sort("timestamp", -1).limit(10)
    return render_template("index.html", events=events)

if __name__ == '__main__':
    app.run(debug=True)
