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

    # Initialize event data structure
    event = {
        "author": data.get("sender", {}).get("login", "Unknown"),
        "event_type": event_type,
        "timestamp": timestamp,
    }

    # Handle pull_request events
    if event_type == "pull_request":
        event["from_branch"] = data.get("pull_request", {}).get("head", {}).get("ref", "")
        event["to_branch"] = data.get("pull_request", {}).get("base", {}).get("ref", "")
        event["action"] = data.get("action", "")  # added action (opened, closed, etc.)

    # Handle push events
    elif event_type == "push":
        event["ref"] = data.get("ref", "")  # The ref (branch) for the push event
        event["commits"] = data.get("commits", [])  # List of commits for the push

    # Handle merge events
    elif event_type == "merge":
        # Merge events might not always have the same structure depending on the payload
        event["merged"] = data.get("merged", False)
        event["merge_ref"] = data.get("merge_ref", "")

    try:
        # Insert the event into MongoDB
        collection.insert_one(event)
        return jsonify({"status": "success"}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# UI endpoint
@app.route('/')
def index():
    events = collection.find().sort("timestamp", -1).limit(10)
    return render_template("index.html", events=events)

if __name__ == '__main__':
    app.run(debug=True)
