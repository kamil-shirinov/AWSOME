from logic import (
    attention_score,
    level_for_xp,
    apply_topic_result,
    new_progress,
    XP_PER_TOPIC,
)


def test_attention_score_caps_at_one():
    assert attention_score([(20, 8), (20, 8)]) == 1.0


def test_attention_score_empty():
    assert attention_score([]) == 0.0


def test_level_for_xp():
    assert level_for_xp(0) == 1
    assert level_for_xp(100) == 2


def test_apply_topic_result_first_steps_only_once():
    progress = new_progress("alice")
    progress, new_badges1, _, passed1 = apply_topic_result(progress, "s3", 3, 3, 1.0)
    assert passed1
    assert "first_steps" in new_badges1

    progress, new_badges2, _, passed2 = apply_topic_result(progress, "lambda", 4, 5, 0.5)
    assert passed2
    assert "first_steps" not in new_badges2


def test_apply_topic_result_moves_incomplete_to_completed():
    progress = new_progress("bob")
    progress["incomplete"].append("s3")

    progress, _, _, passed = apply_topic_result(progress, "s3", 3, 3, 0.5)

    assert passed
    assert "s3" not in progress["incomplete"]
    assert "s3" in progress["completed"]


def test_apply_topic_result_below_pass_mark_gives_no_xp_and_marks_incomplete():
    progress = new_progress("carol")

    progress, new_badges, leveled_up, passed = apply_topic_result(progress, "s3", 3, 5, 1.0)

    assert not passed
    assert progress["xp"] == 0
    assert new_badges == []
    assert not leveled_up
    assert "s3" in progress["incomplete"]
    assert "s3" not in progress["completed"]


def test_apply_topic_result_at_pass_mark_gives_xp():
    progress = new_progress("dave")

    progress, _, _, passed = apply_topic_result(progress, "s3", 4, 5, 1.0)

    assert passed
    assert progress["xp"] == XP_PER_TOPIC
    assert "s3" in progress["completed"]


def test_apply_topic_result_retake_gives_no_extra_xp():
    progress = new_progress("erin")
    progress, _, _, _ = apply_topic_result(progress, "s3", 4, 5, 1.0)
    assert progress["xp"] == XP_PER_TOPIC

    progress, _, _, passed = apply_topic_result(progress, "s3", 5, 5, 1.0)

    assert passed
    assert progress["xp"] == XP_PER_TOPIC


def test_apply_topic_result_keeps_best_score():
    progress = new_progress("frank")
    progress, _, _, _ = apply_topic_result(progress, "s3", 4, 5, 1.0)
    assert progress["scores"]["s3"] == 80

    progress, _, _, _ = apply_topic_result(progress, "s3", 3, 5, 1.0)

    assert progress["scores"]["s3"] == 80
