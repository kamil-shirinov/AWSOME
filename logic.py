REDIRECT_THRESHOLD = 0.30
FOCUSED_THRESHOLD = 0.70
FLASHCARD_SECONDS = 5
XP_PER_TOPIC = 100
PASS_MARK = 0.8

BADGES = {
    "first_steps": "🐣 First Steps",
    "laser_focus": "🎯 Laser Focus",
    "perfect_score": "💯 Perfect Score",
}


def new_progress(user_id):
    return {
        "user_id": user_id,
        "xp": 0,
        "level": 1,
        "badges": [],
        "completed": [],
        "incomplete": [],
        "tutorial_done": False,
    }


def attention_score(dwells):
    if not dwells:
        return 0.0
    ratios = [min(spent / expected, 1.0) for spent, expected in dwells]
    return sum(ratios) / len(ratios)


def level_for_xp(xp):
    return 1 + xp // 100


def mark_incomplete(progress, topic_id):
    if topic_id not in progress["incomplete"] and topic_id not in progress["completed"]:
        progress["incomplete"].append(topic_id)
    return progress


def apply_topic_result(progress, topic_id, correct, total, attention):
    new_badges = []
    leveled_up = False
    passed = (correct / total) >= PASS_MARK

    scores = progress.setdefault("scores", {})
    score_pct = round((correct / total) * 100)
    scores[topic_id] = max(scores.get(topic_id, 0), score_pct)

    if passed:
        if topic_id not in progress["completed"]:
            progress["xp"] += XP_PER_TOPIC
            progress["level"] = level_for_xp(progress["xp"])
            progress["completed"].append(topic_id)
            leveled_up = level_for_xp(progress["xp"]) > level_for_xp(progress["xp"] - XP_PER_TOPIC)
        if topic_id in progress["incomplete"]:
            progress["incomplete"].remove(topic_id)

        if "first_steps" not in progress["badges"]:
            progress["badges"].append("first_steps")
            new_badges.append("first_steps")

        if attention >= 0.9 and "laser_focus" not in progress["badges"]:
            progress["badges"].append("laser_focus")
            new_badges.append("laser_focus")

        if correct == total and "perfect_score" not in progress["badges"]:
            progress["badges"].append("perfect_score")
            new_badges.append("perfect_score")
    else:
        mark_incomplete(progress, topic_id)

    return progress, new_badges, leveled_up, passed
