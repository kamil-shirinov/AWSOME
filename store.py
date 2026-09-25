import json
import os

CONTENT_DIR = "content"
PROGRESS_DIR = "progress"


def load_topic(topic_id):
    with open(os.path.join(CONTENT_DIR, f"{topic_id}.json")) as f:
        return json.load(f)


def load_progress(user_id):
    path = os.path.join(PROGRESS_DIR, f"{user_id}.json")
    if not os.path.exists(path):
        return None
    with open(path) as f:
        return json.load(f)


def save_progress(progress):
    os.makedirs(PROGRESS_DIR, exist_ok=True)
    path = os.path.join(PROGRESS_DIR, f"{progress['user_id']}.json")
    with open(path, "w") as f:
        json.dump(progress, f)
