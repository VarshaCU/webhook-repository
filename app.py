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

    # Print the received data for debugging
    print("Received payload:", data)

    # Handle pull_request events
    if event_type == "pull_request":
        event["from_branch"] = data.get("pull_request", {}).get("head", {}).get("ref", "")
        event["to_branch"] = data.get("pull_request", {}).get("base", {}).get("ref", "")
        event["status"] = data.get("pull_request", {}).get("state", "")  # open, closed, merged
        event["merge"] = data.get("pull_request", {}).get("merged", False)  # merge status
    elif event_type == "push":
        # For push events, add relevant data
        event["ref"] = data.get("ref", "")  # The ref (branch) for the push event
        event["pusher"] = data.get("pusher", {}).get("name", "")  # Who pushed the changes

    # Print the event data for debugging
    print(f"Processed event: {event}")

    try:
        # Insert the event into MongoDB
        collection.insert_one(event)
        print("Event successfully inserted into MongoDB.")
        return jsonify({"status": "success"}), 200
    except Exception as e:
        print(f"Error inserting event into MongoDB: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


# UI endpoint
@app.route('/')
def index():
    events = collection.find().sort("timestamp", -1).limit(10)
    return render_template("index.html", events=events)


if __name__ == '__main__':
    app.run(debug=True)
