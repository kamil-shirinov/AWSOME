import inspect
import time

import streamlit as st
import streamlit.components.v1 as components

from logic import (
    REDIRECT_THRESHOLD,
    FOCUSED_THRESHOLD,
    FLASHCARD_SECONDS,
    XP_PER_TOPIC,
    PASS_MARK,
    BADGES,
    new_progress,
    attention_score,
    mark_incomplete,
    apply_topic_result,
)
from store import load_topic, load_progress, save_progress

CATALOG = [
    {"id": "s3", "icon": "bucket", "name": "Amazon S3", "live": True},
    {"id": "lambda", "icon": "bolt", "name": "AWS Lambda", "live": True},
    {"id": "ec2", "icon": "server", "name": "EC2", "live": False},
    {"id": "iam", "icon": "key", "name": "IAM", "live": False},
    {"id": "dynamodb", "icon": "database", "name": "DynamoDB", "live": False},
    {"id": "bedrock", "icon": "sparkle", "name": "Bedrock", "live": False},
]

TUTORIAL_CARDS = [
    {"title": "Watch short videos", "body": "Quick reels teach you the basics of each AWS service."},
    {"title": "Flip flashcards", "body": "Test your memory by flipping through key concepts."},
    {"title": "Take the quiz and earn XP", "body": "Answer questions correctly to earn XP, badges, and level up."},
]

REEL_DISPLAY_LENGTHS = {"s3": [47, 72, 58], "lambda": [53, 64, 41]}

CHALLENGE_UNLOCK_LEVEL = 6

QUIZ_SECONDS = 20
KAHOOT_COLORS = ["#E21B3C", "#1368CE", "#D89E00", "#26890C"]
KAHOOT_SYMBOLS = ["▲", "◆", "●", "■"]

BADGE_ICON_NAMES = {"first_steps": "sprout", "laser_focus": "target", "perfect_score": "star"}

_BUTTON_SUPPORTS_WIDTH = "width" in inspect.signature(st.button).parameters

# ---------------------------------------------------------------------------
# Icons: one consistent set of original inline-SVG line icons (24px, 1.75px
# stroke, rounded caps, currentColor). "star" and "play" are solid glyphs.
# ---------------------------------------------------------------------------

ICON_PATHS = {
    "bucket": '<path d="M5 7h14l-1.4 11.8A2 2 0 0 1 15.6 20H8.4a2 2 0 0 1-2-1.8L5 7Z"/>'
              '<path d="M8 7a4 4 0 0 1 8 0"/>',
    "bolt": '<path d="M13 2 4 14h6l-1 8 9-12h-6l1-8Z"/>',
    "server": '<rect x="4" y="4" width="16" height="7" rx="1.5"/>'
              '<rect x="4" y="13" width="16" height="7" rx="1.5"/>'
              '<circle cx="7.5" cy="7.5" r="0.75" fill="currentColor" stroke="none"/>'
              '<circle cx="7.5" cy="16.5" r="0.75" fill="currentColor" stroke="none"/>',
    "key": '<circle cx="7.5" cy="16.5" r="4"/><path d="M10.5 13.5 20 4"/>'
           '<path d="M15 9l3 3"/><path d="M18 6l2.5 2.5"/>',
    "database": '<ellipse cx="12" cy="6" rx="7" ry="3"/>'
                '<path d="M5 6v12c0 1.7 3.1 3 7 3s7-1.3 7-3V6"/>'
                '<path d="M5 12c0 1.7 3.1 3 7 3s7-1.3 7-3"/>',
    "sparkle": '<path d="M12 3l1.8 5.2L19 10l-5.2 1.8L12 17l-1.8-5.2L5 10l5.2-1.8L12 3Z"/>'
               '<path d="M19 15l.7 1.8L22 18l-2.3 1.2L19 21l-.7-1.8L16 18l2.3-1.2L19 15Z"/>',
    "trophy": '<path d="M7 4h10v4a5 5 0 0 1-10 0V4Z"/><path d="M7 5H4a3 3 0 0 0 3 5"/>'
              '<path d="M17 5h3a3 3 0 0 1-3 5"/><path d="M12 13v3"/>'
              '<path d="M9.5 20h5"/><path d="M10 16.5h4v3h-4z"/>',
    "lock": '<rect x="5" y="11" width="14" height="9" rx="2"/>'
            '<path d="M8 11V8a4 4 0 0 1 8 0v3"/>',
    "unlock": '<rect x="5" y="11" width="14" height="9" rx="2"/>'
              '<path d="M8 11V8a4 4 0 0 1 7.5-2.2"/>',
    "sprout": '<path d="M12 21v-8"/><path d="M12 13c0-4-3-6-7-6 0 4 3 6 7 6Z"/>'
              '<path d="M12 11c0-3.5 2.5-5.5 6-5.5 0 3.5-2.5 5.5-6 5.5Z"/>',
    "target": '<circle cx="12" cy="12" r="8"/><circle cx="12" cy="12" r="4.5"/>'
              '<circle cx="12" cy="12" r="1" fill="currentColor" stroke="none"/>',
    "check": '<path d="M5 13l4 4 10-10"/>',
    "cross": '<path d="M6 6l12 12"/><path d="M18 6 6 18"/>',
    "clock": '<circle cx="12" cy="12" r="8.5"/><path d="M12 7.5V12l3.5 2"/>',
    "star": '<path d="M12 3l2.6 5.9 6.4.6-4.8 4.3 1.4 6.3L12 16.9 6.4 20.1l1.4-6.3-4.8-4.3 6.4-.6L12 3Z"/>',
    "play": '<path d="M8 5.5v13l11-6.5-11-6.5Z"/>',
}
ICON_FILLED = {"star", "play"}


def icon(name, size=24):
    inner = ICON_PATHS[name]
    if name in ICON_FILLED:
        return (
            f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="currentColor" '
            f'stroke="none" style="vertical-align:middle;flex-shrink:0;">{inner}</svg>'
        )
    return (
        f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" '
        f'stroke="currentColor" stroke-width="1.75" stroke-linecap="round" '
        f'stroke-linejoin="round" style="vertical-align:middle;flex-shrink:0;">{inner}</svg>'
    )


def badge_label(b):
    label = BADGES[b].split(" ", 1)[1] if " " in BADGES[b] else BADGES[b]
    return f'{icon(BADGE_ICON_NAMES[b], 16)} {label}'


def badge_pills(badge_keys):
    return "".join(
        f"""<span style="background:#F2F3F3; color:#232F3E; border-radius:999px;
            padding:4px 12px; margin-right:6px; font-size:0.85rem; display:inline-flex;
            align-items:center; gap:4px; margin-bottom:6px;">{badge_label(b)}</span>"""
        for b in badge_keys
    )


# ---------------------------------------------------------------------------
# Background bubbles: fixed constants so inject_css() emits byte-identical
# HTML every rerun and Streamlit never recreates (restarts) the DOM node.
# ---------------------------------------------------------------------------

BUBBLES = [
    (6, 10, 0.18, 11, 0.0),
    (16, 14, 0.22, 9, 1.6),
    (24, 7, 0.15, 13, 3.2),
    (33, 16, 0.25, 10, 0.9),
    (43, 9, 0.14, 15, 4.4),
    (52, 12, 0.20, 8, 2.3),
    (61, 18, 0.24, 14, 5.6),
    (71, 6, 0.12, 16, 1.1),
    (81, 15, 0.19, 12, 3.9),
    (90, 11, 0.17, 9.5, 6.2),
]


def _bubbles_html():
    spans = "".join(
        f'<span class="bg-bubble" style="left:{left}%; width:{size}px; height:{size}px; '
        f'background:rgba(255,153,0,{opacity}); animation-duration:{dur}s; '
        f'animation-delay:{delay}s;"></span>'
        for left, size, opacity, dur, delay in BUBBLES
    )
    return f'<div class="bg-bubbles">{spans}</div>'


CELEBRATION_PIECES = [
    (4, "#FF9900", 8, 0.00, 2.8, 15),
    (11, "#232F3E", 10, 0.15, 3.2, -20),
    (18, "#FF9900", 7, 0.30, 2.6, 30),
    (25, "#232F3E", 9, 0.05, 3.0, -10),
    (32, "#FF9900", 11, 0.25, 2.9, 25),
    (39, "#232F3E", 8, 0.40, 3.1, -30),
    (46, "#FF9900", 9, 0.10, 2.7, 10),
    (53, "#232F3E", 10, 0.35, 3.3, -15),
    (60, "#FF9900", 7, 0.20, 2.8, 35),
    (67, "#232F3E", 9, 0.05, 3.0, -25),
    (74, "#FF9900", 10, 0.30, 2.9, 20),
    (81, "#232F3E", 8, 0.15, 3.2, -35),
    (88, "#FF9900", 9, 0.45, 2.7, 15),
    (95, "#232F3E", 11, 0.10, 3.1, -20),
]


def render_celebration():
    pieces = "".join(
        f'<span class="celebration-piece" style="left:{left}%; width:{w}px; '
        f'height:{round(w * 1.6)}px; background:{color}; animation-delay:{delay}s; '
        f'animation-duration:{dur}s; --rot:{rot}deg;"></span>'
        for left, color, w, delay, dur, rot in CELEBRATION_PIECES
    )
    st.markdown(f'<div class="celebration-layer">{pieces}</div>', unsafe_allow_html=True)


def nav_button(label, **kwargs):
    if _BUTTON_SUPPORTS_WIDTH:
        return st.button(label, width="stretch", **kwargs)
    return st.button(label, use_container_width=True, **kwargs)


def inject_css():
    st.markdown(
        f"""
        <style>
        [data-testid="stHeader"], [data-testid="stToolbar"], footer {{
            visibility: hidden;
            height: 0;
        }}

        [data-testid="stAppViewContainer"]::before {{
            content: "";
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            width: 390px;
            height: min(92vh, 860px);
            border: 14px solid #111111;
            border-radius: 46px;
            pointer-events: none;
            z-index: 999;
            box-shadow: 0 0 0 100vmax #E9EDF2;
            box-sizing: border-box;
        }}
        [data-testid="stAppViewContainer"]::after {{
            content: "";
            position: fixed;
            top: calc(50% - min(92vh, 860px) / 2 + 14px);
            left: 50%;
            transform: translateX(-50%);
            width: 120px;
            height: 26px;
            background: #111111;
            border-radius: 0 0 16px 16px;
            z-index: 1000;
            pointer-events: none;
        }}

        .block-container {{
            max-width: 356px;
            margin: 0 auto;
            padding-top: calc((100vh - min(92vh, 860px)) / 2 + 48px);
            padding-bottom: calc((100vh - min(92vh, 860px)) / 2 + 48px + 24px);
            box-sizing: border-box;
        }}

        /* Ensure whichever ancestor actually owns the scrollbar in this
           Streamlit version can scroll its full content height. */
        [data-testid="stAppViewContainer"], [data-testid="stMain"], section.main {{
            overflow-y: auto !important;
        }}

        div[data-testid="stButton"] {{
            margin-top: 1rem;
            position: relative;
            z-index: 2;
        }}

        div[data-testid="stVerticalBlockBorderWrapper"] {{
            border-radius: 20px !important;
            background: #FFFFFF;
            box-shadow: 0 4px 16px rgba(35, 47, 62, 0.08);
        }}
        div[class*="st-key-comingsoon_"] {{
            opacity: 0.5;
        }}

        /* Home tiles: fixed height so a topic's status/badge never resizes
           the grid, with the button pinned to the tile's bottom edge. */
        div[class*="st-key-tile_"], div[class*="st-key-comingsoon_"] {{
            height: 150px;
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }}
        div[class*="st-key-tile_"] div[data-testid="stButton"],
        div[class*="st-key-comingsoon_"] div[data-testid="stButton"] {{
            margin-top: auto !important;
        }}
        .tile-status {{
            font-size: 0.78rem;
            color: #5A6B7B;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }}
        .stButton > button {{
            width: 100%;
            border-radius: 999px;
            font-weight: 700;
        }}

        div[class*="st-key-answer_opt_0"] .stButton > button,
        div[class*="st-key-answer_opt_1"] .stButton > button,
        div[class*="st-key-answer_opt_2"] .stButton > button,
        div[class*="st-key-answer_opt_3"] .stButton > button {{
            height: 96px !important;
            font-size: 0.95rem !important;
            line-height: 1.2 !important;
            white-space: normal !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            text-align: center !important;
        }}
        div[class*="st-key-answer_opt_0"] .stButton > button {{
            background: #E21B3C !important; color: #FFFFFF !important;
            border: none !important; font-weight: 700 !important;
        }}
        div[class*="st-key-answer_opt_1"] .stButton > button {{
            background: #1368CE !important; color: #FFFFFF !important;
            border: none !important; font-weight: 700 !important;
        }}
        div[class*="st-key-answer_opt_2"] .stButton > button {{
            background: #D89E00 !important; color: #FFFFFF !important;
            border: none !important; font-weight: 700 !important;
        }}
        div[class*="st-key-answer_opt_3"] .stButton > button {{
            background: #26890C !important; color: #FFFFFF !important;
            border: none !important; font-weight: 700 !important;
        }}

        /* Vertically centre each screen's content within the phone's usable
           height. Short screens (login, tutorial, flashcard, quiz...) sit in
           the middle; min-height (not height) lets tall ones (home, results)
           grow and start at the top instead of being squeezed/clipped. */
        div[class*="st-key-view_"], div[class*="st-key-viewnofade_"] {{
            min-height: calc(min(92vh, 860px) - 96px - 2rem);
            display: flex;
            flex-direction: column;
            justify-content: center;
            box-sizing: border-box;
        }}

        /* Extra bottom padding only for the short, centred screens, so their
           content sits slightly above the middle. Tall screens (home,
           results) and reel steps are excluded so they don't scroll too far. */
        div[class*="st-key-view_login_"],
        div[class*="st-key-view_tutorial_"],
        div[class*="st-key-view_redirect_"],
        div[class*="st-key-view_quiz_"],
        div[class*="st-key-view_lesson_card_"] {{
            padding-bottom: 16vh;
        }}

        /* Screen fade: each screen/step view fades and rises in once.
           Reel-to-reel steps use the "viewnofade_" key instead so the fade
           doesn't fight the slide transition below. */
        div[class*="st-key-view_"] {{
            animation: viewFadeIn 0.3s ease;
        }}
        @keyframes viewFadeIn {{
            from {{ opacity: 0; transform: translateY(8px); }}
            to   {{ opacity: 1; transform: translateY(0); }}
        }}

        /* Reel-to-reel slide, Instagram-Reels style. */
        .reel-slide-wrap {{
            position: relative;
            aspect-ratio: 9 / 16;
            width: min(100%, calc(62vh * 9 / 16));
            margin: 0 auto;
        }}
        .reel-slide-old, .reel-slide-new {{
            position: absolute;
            inset: 0;
        }}
        .reel-slide-old {{
            animation: reelSlideOut 0.5s cubic-bezier(0.22, 1, 0.36, 1) forwards;
        }}
        .reel-slide-new {{
            animation: reelSlideIn 0.5s cubic-bezier(0.22, 1, 0.36, 1) forwards;
        }}
        @keyframes reelSlideOut {{
            from {{ transform: translateY(0); opacity: 1; }}
            to   {{ transform: translateY(-110%); opacity: 0; }}
        }}
        @keyframes reelSlideIn {{
            from {{ transform: translateY(110%); }}
            to   {{ transform: translateY(0); }}
        }}

        /* Background bubbles: fixed layer clipped to the phone's inner screen. */
        .bg-bubbles {{
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            width: 362px;
            height: calc(min(92vh, 860px) - 28px);
            border-radius: 32px;
            overflow: hidden;
            pointer-events: none;
            z-index: 1;
        }}
        .bg-bubble {{
            position: absolute;
            bottom: -20px;
            border-radius: 50%;
            animation-name: bubbleRise;
            animation-timing-function: ease-in-out;
            animation-iteration-count: infinite;
        }}
        @keyframes bubbleRise {{
            0%   {{ transform: translate(0, 0); opacity: 0; }}
            10%  {{ opacity: 1; }}
            50%  {{ transform: translate(10px, -410px); }}
            90%  {{ opacity: 1; }}
            100% {{ transform: translate(-8px, -820px); opacity: 0; }}
        }}

        /* 3D flashcard flip. */
        .flip-scene {{ perspective: 1000px; height: 300px; }}
        .flip-inner {{
            position: relative;
            width: 100%;
            height: 100%;
            transform-style: preserve-3d;
        }}
        .flip-face {{
            position: absolute;
            inset: 0;
            backface-visibility: hidden;
            border-radius: 20px;
            box-shadow: 0 4px 16px rgba(35, 47, 62, 0.08);
            display: flex;
            flex-direction: column;
            padding: 20px;
            box-sizing: border-box;
            overflow: hidden;
        }}
        .flip-front {{ background: #FFFFFF; border: 1px solid #E5E9ED; }}
        .flip-back {{ background: #FFF4E5; border: 2px solid #FF9900; transform: rotateY(180deg); }}
        @keyframes flip3dToBack {{ from {{ transform: rotateY(0deg); }} to {{ transform: rotateY(180deg); }} }}
        @keyframes flip3dToFront {{ from {{ transform: rotateY(180deg); }} to {{ transform: rotateY(0deg); }} }}

        /* Level-up celebration: fixed layer clipped to the phone's inner screen. */
        .celebration-layer {{
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            width: 362px;
            height: calc(min(92vh, 860px) - 28px);
            overflow: hidden;
            pointer-events: none;
            z-index: 1200;
        }}
        .celebration-piece {{
            position: absolute;
            bottom: -20px;
            border-radius: 3px;
            opacity: 0;
            animation-name: celebrationRise;
            animation-timing-function: ease-out;
            animation-fill-mode: forwards;
        }}
        @keyframes celebrationRise {{
            0%   {{ transform: translateY(0) rotate(0deg); opacity: 1; }}
            100% {{ transform: translateY(-780px) rotate(var(--rot)); opacity: 0; }}
        }}

        @media (prefers-reduced-motion: reduce) {{
            .bg-bubbles, .celebration-layer {{ display: none !important; }}
            div[class*="st-key-view_"] {{ animation-duration: 0.01s !important; }}
            .flip-inner {{ animation-duration: 0.01s !important; }}
            .reel-slide-old {{ display: none !important; }}
            .reel-slide-new {{ animation: none !important; transform: none !important; }}
        }}
        </style>
        {_bubbles_html()}
        """,
        unsafe_allow_html=True,
    )


def scroll_to_top(marker):
    components.html(
        f"""
        <div data-marker="{marker}" style="display:none;"></div>
        <script>
        (function() {{
            const doc = window.parent.document;
            ['[data-testid="stMain"]', 'section.main', '[data-testid="stAppViewContainer"]'].forEach(function(sel) {{
                const el = doc.querySelector(sel);
                if (el) {{ el.scrollTo(0, 0); }}
            }});
        }})();
        </script>
        """,
        height=0,
    )


def format_duration(seconds):
    minutes = seconds // 60
    secs = seconds % 60
    return f"{minutes}:{secs:02d}"


def card_counts(topic):
    num_reels = len(topic["reels"])
    num_flashcards = len(topic["flashcards"])
    return num_reels, num_flashcards, num_reels + num_flashcards


def current_step():
    screen = st.session_state.screen
    if screen == "lesson":
        idx = st.session_state.get("card_index", 0)
        topic = st.session_state.get("topic_data")
        if topic:
            num_reels, _, _ = card_counts(topic)
            kind = "reel" if idx < num_reels else "card"
        else:
            kind = "card"
        return f"{kind}_{idx}"
    if screen == "quiz":
        return f"{st.session_state.get('quiz_index', 0)}_{st.session_state.get('quiz_phase', '')}"
    return 0


def init_state():
    if "screen" not in st.session_state:
        st.session_state.screen = "login"


def go_home():
    st.session_state.screen = "home"


def do_login():
    name = st.session_state.get("name_input", "").strip().lower()
    if not name:
        return
    progress = load_progress(name)
    if progress is None:
        progress = new_progress(name)
        save_progress(progress)
    st.session_state.user_id = name
    st.session_state.progress = progress
    st.session_state.tutorial_step = 0
    if progress["tutorial_done"]:
        st.session_state.screen = "home"
    else:
        st.session_state.screen = "tutorial"


def tutorial_next():
    step = st.session_state.tutorial_step
    if step >= len(TUTORIAL_CARDS) - 1:
        st.session_state.progress["tutorial_done"] = True
        save_progress(st.session_state.progress)
        st.session_state.screen = "home"
    else:
        st.session_state.tutorial_step = step + 1


def start_lesson(topic_id):
    topic_data = load_topic(topic_id)
    num_questions = len(topic_data["quiz"])

    st.session_state.current_topic = topic_id
    st.session_state.topic_data = topic_data
    st.session_state.card_index = 0
    st.session_state.dwells = []
    st.session_state.flipped = False
    st.session_state.just_flipped = False
    st.session_state.reel_transition = False
    st.session_state.outgoing_reel_idx = None
    st.session_state.card_started_at = time.time()

    st.session_state.quiz_index = 0
    st.session_state.quiz_phase = "question"
    st.session_state.quiz_answers = [None] * num_questions
    st.session_state.quiz_timed_out = [False] * num_questions
    st.session_state.quiz_start_times = [None] * num_questions

    st.session_state.screen = "lesson"


def flip_card():
    st.session_state.flipped = not st.session_state.flipped
    st.session_state.just_flipped = True


def next_card():
    idx = st.session_state.card_index
    topic = st.session_state.topic_data
    num_reels, _, total = card_counts(topic)
    if idx < num_reels:
        expected = topic["reels"][idx]["seconds"]
    else:
        expected = FLASHCARD_SECONDS
    spent = time.time() - st.session_state.card_started_at
    st.session_state.dwells.append((spent, expected))

    if idx == total - 1:
        st.session_state.reel_transition = False
        attention = attention_score(st.session_state.dwells)
        st.session_state.attention = attention
        if attention < REDIRECT_THRESHOLD:
            st.session_state.progress = mark_incomplete(st.session_state.progress, st.session_state.current_topic)
            save_progress(st.session_state.progress)
            st.session_state.screen = "redirect"
        else:
            st.session_state.screen = "quiz"
    else:
        is_reel_to_reel = (idx + 1) < num_reels
        st.session_state.reel_transition = is_reel_to_reel
        st.session_state.outgoing_reel_idx = idx if is_reel_to_reel else None
        st.session_state.card_index = idx + 1
        st.session_state.flipped = False
        st.session_state.card_started_at = time.time()


def prev_card():
    idx = st.session_state.card_index
    topic = st.session_state.topic_data
    num_reels, _, _ = card_counts(topic)
    if idx <= num_reels:
        return
    spent = time.time() - st.session_state.card_started_at
    st.session_state.dwells.append((spent, FLASHCARD_SECONDS))
    st.session_state.reel_transition = False
    st.session_state.card_index = idx - 1
    st.session_state.flipped = False
    st.session_state.card_started_at = time.time()


def select_answer(q_index, opt_index):
    if st.session_state.quiz_phase != "question":
        return
    st.session_state.quiz_answers[q_index] = opt_index
    st.session_state.quiz_phase = "feedback"


def advance_quiz():
    idx = st.session_state.quiz_index
    quiz = st.session_state.topic_data["quiz"]

    if idx == len(quiz) - 1:
        correct = sum(
            1 for i in range(len(quiz))
            if st.session_state.quiz_answers[i] == quiz[i]["answer"]
        )
        topic_id = st.session_state.current_topic
        was_completed_before = topic_id in st.session_state.progress["completed"]
        progress, new_badges, leveled_up, passed = apply_topic_result(
            st.session_state.progress,
            topic_id,
            correct,
            len(quiz),
            st.session_state.attention,
        )
        st.session_state.progress = progress
        save_progress(progress)
        st.session_state.quiz_correct = correct
        st.session_state.quiz_total = len(quiz)
        st.session_state.new_badges = new_badges
        st.session_state.leveled_up = leveled_up
        st.session_state.passed = passed
        st.session_state.attempt_score_pct = round((correct / len(quiz)) * 100)
        st.session_state.xp_gained = XP_PER_TOPIC if (passed and not was_completed_before) else 0
        st.session_state.screen = "results"
    else:
        st.session_state.quiz_index = idx + 1
        st.session_state.quiz_phase = "question"


def render_login():
    st.markdown(
        """
        <div style="text-align:center; margin-top:3rem; margin-bottom:1.5rem;">
            <div style="font-size:2.8rem; font-weight:800; letter-spacing:1px;">
                <span style="color:#FF9900;">AWS</span><span style="color:#232F3E;">OME</span>
            </div>
            <div style="color:#5A6B7B; font-size:1rem; margin-top:0.5rem;">
                Learn AWS, one bite-sized topic at a time.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.text_input(
        "Name",
        key="name_input",
        label_visibility="collapsed",
        placeholder="What's your name?",
    )
    nav_button("Let's go", on_click=do_login, type="primary")


def render_tutorial():
    step = st.session_state.tutorial_step
    card = TUTORIAL_CARDS[step]
    st.markdown(
        """
        <div style="text-align:center; font-size:1.8rem; font-weight:800; margin-bottom:1rem;">
            <span style="color:#FF9900;">AWS</span><span style="color:#232F3E;">OME</span>
        </div>
        """,
        unsafe_allow_html=True,
    )
    with st.container(border=True):
        st.subheader(card["title"])
        st.write(card["body"])
    nav_button("Next", on_click=tutorial_next, type="primary")


def render_tile(item, progress):
    if item["live"]:
        topic_id = item["id"]
        with st.container(border=True, key=f"tile_{topic_id}"):
            st.markdown(
                f'<div style="font-weight:700; display:flex; align-items:center; gap:6px;">'
                f'{icon(item["icon"], 20)} {item["name"]}</div>',
                unsafe_allow_html=True,
            )
            score = progress.get("scores", {}).get(topic_id)
            if topic_id in progress["completed"]:
                status_text = f"Passed, best {score}%"
                button_label = "Retake"
            elif score is not None:
                status_text = f"Best {score}%, needs 80%"
                button_label = "Retake"
            elif topic_id in progress["incomplete"]:
                status_text = "Incomplete"
                button_label = "Redo"
            else:
                status_text = "New"
                button_label = "Start"

            st.markdown(f'<div class="tile-status">{status_text}</div>', unsafe_allow_html=True)
            nav_button(button_label, key=f"btn_{topic_id}", on_click=start_lesson, args=(topic_id,), type="primary")
    else:
        with st.container(border=True, key=f"comingsoon_{item['id']}"):
            st.markdown(
                f'<div style="font-weight:700; display:flex; align-items:center; gap:6px;">'
                f'{icon(item["icon"], 20)} {item["name"]}</div>',
                unsafe_allow_html=True,
            )
            st.markdown('<div class="tile-status">Coming soon</div>', unsafe_allow_html=True)
            nav_button("Coming soon", key=f"btn_{item['id']}", disabled=True)


def render_home():
    progress = st.session_state.progress
    st.markdown(f"### Hi {progress['user_id'].title()}")

    st.markdown(
        f"""
        <span style="background:#FFF4E5; color:#FF9900; padding:4px 14px;
            border-radius:999px; font-weight:700; font-size:0.9rem;">
            Level {progress['level']}
        </span>
        """,
        unsafe_allow_html=True,
    )
    st.write("")
    live_topic_ids = [item["id"] for item in CATALOG if item["live"]]
    passed_count = sum(1 for tid in live_topic_ids if tid in progress["completed"])
    st.caption(f"{passed_count} of {len(live_topic_ids)} passed")

    if progress["badges"]:
        st.markdown(badge_pills(progress["badges"]), unsafe_allow_html=True)

    cols = st.columns(2)
    for i, item in enumerate(CATALOG):
        with cols[i % 2]:
            render_tile(item, progress)

    with st.container(border=True):
        st.markdown(
            f'<div style="font-weight:700; display:flex; align-items:center; gap:6px;">'
            f'{icon("trophy", 20)} Challenge mode</div>',
            unsafe_allow_html=True,
        )
        if progress["level"] < CHALLENGE_UNLOCK_LEVEL:
            st.markdown(
                f'<div style="display:flex; align-items:center; gap:6px; color:#5A6B7B; font-size:0.85rem;">'
                f'{icon("lock", 16)} Unlocks at Level {CHALLENGE_UNLOCK_LEVEL}</div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f'<div style="display:flex; align-items:center; gap:6px; color:#5A6B7B; font-size:0.85rem;">'
                f'{icon("unlock", 16)} Unlocked!</div>',
                unsafe_allow_html=True,
            )
        nav_button("Coming soon", key="btn_challenge", disabled=True)


def _reel_card_inner(topic, reel, idx, total):
    lengths = REEL_DISPLAY_LENGTHS.get(topic.get("id"))
    if lengths and idx < len(lengths):
        display_seconds = lengths[idx]
    else:
        display_seconds = reel["seconds"]
    duration = format_duration(display_seconds)
    return f"""
        <div style="
            width:100%; height:100%; border-radius:20px; position:relative; overflow:hidden;
            background: linear-gradient(160deg, #232F3E 0%, #16202C 100%);
            box-shadow: 0 8px 24px rgba(35, 47, 62, 0.25);
        ">
            <div style="position:absolute; top:16px; left:16px;
                background:rgba(255,153,0,0.9); color:#232F3E; font-weight:700;
                font-size:0.8rem; padding:4px 12px; border-radius:999px;">
                {topic['title']}
            </div>
            <div style="position:absolute; top:16px; right:16px;
                background:rgba(255,255,255,0.15); color:#FFFFFF; font-weight:700;
                font-size:0.8rem; padding:4px 12px; border-radius:999px;">
                {idx + 1}/{total}
            </div>
            <div style="position:absolute; top:50%; left:50%;
                transform:translate(-50%, -50%); text-align:center;">
                <div style="
                    width:72px; height:72px; border-radius:50%;
                    background:rgba(255,255,255,0.15); border:2px solid rgba(255,255,255,0.6);
                    display:flex; align-items:center; justify-content:center;
                    margin:0 auto 10px auto; color:#FFFFFF;">
                    {icon('play', 28)}
                </div>
                <div style="color:#FFFFFF; font-weight:600; font-size:0.95rem;">{duration}</div>
            </div>
            <div style="position:absolute; bottom:0; left:0; right:0; padding:20px;
                background:linear-gradient(0deg, rgba(0,0,0,0.75) 0%, rgba(0,0,0,0) 100%);">
                <div style="color:#FFFFFF; font-weight:700; font-size:1.05rem; margin-bottom:4px;">
                    {reel['title']}
                </div>
                <div style="color:#E5E9ED; font-size:0.9rem;">
                    {reel['body']}
                </div>
            </div>
        </div>
    """


def render_reel(topic, reel, idx, total):
    inner = _reel_card_inner(topic, reel, idx, total)
    st.markdown(f'<div class="reel-slide-wrap">{inner}</div>', unsafe_allow_html=True)
    nav_button("Next ↓", key="next_btn", on_click=next_card, type="primary")


def render_reel_transition(topic, outgoing_idx, incoming_idx, total):
    old_inner = _reel_card_inner(topic, topic["reels"][outgoing_idx], outgoing_idx, total)
    new_inner = _reel_card_inner(topic, topic["reels"][incoming_idx], incoming_idx, total)
    st.markdown(
        f'<div class="reel-slide-wrap">'
        f'<div class="reel-slide-old">{old_inner}</div>'
        f'<div class="reel-slide-new">{new_inner}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )
    nav_button("Next ↓", key="next_btn", on_click=next_card, type="primary")


def render_flashcard(card, idx, total, is_first):
    flipped = st.session_state.flipped
    just_flipped = st.session_state.get("just_flipped", False)

    if just_flipped:
        anim_name = "flip3dToBack" if flipped else "flip3dToFront"
        inner_style = f"animation:{anim_name} 0.6s ease forwards;"
    else:
        resting = "rotateY(180deg)" if flipped else "rotateY(0deg)"
        inner_style = f"animation:none; transform:{resting};"

    chip = (
        f'<span style="background:#F2F3F3; color:#232F3E; border-radius:999px; '
        f'padding:4px 12px; font-weight:700; font-size:0.8rem;">{idx + 1}/{total}</span>'
    )

    st.markdown(
        f"""
        <div class="flip-scene">
            <div class="flip-inner" style="{inner_style}">
                <div class="flip-face flip-front">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <span style="color:#8A97A6; font-weight:700; font-size:0.8rem;
                            text-transform:uppercase;">Question</span>
                        {chip}
                    </div>
                    <div style="flex:1; display:flex; align-items:center; justify-content:center;
                        text-align:center; overflow:hidden; word-wrap:break-word;">
                        <div style="font-size:1.15rem; font-weight:700; color:#232F3E;">
                            {card['front']}
                        </div>
                    </div>
                </div>
                <div class="flip-face flip-back">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <span style="color:#8A97A6; font-weight:700; font-size:0.8rem;
                            text-transform:uppercase;">Answer</span>
                        {chip}
                    </div>
                    <div style="flex:1; display:flex; align-items:center; justify-content:center;
                        text-align:center; overflow:hidden; word-wrap:break-word;">
                        <div style="font-size:1.15rem; font-weight:700; color:#232F3E;">
                            {card['back']}
                        </div>
                    </div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.session_state.just_flipped = False

    col1, col2, col3 = st.columns(3)
    with col1:
        nav_button("←", key="prev_btn", on_click=prev_card, disabled=is_first)
    with col2:
        nav_button("Flip", key="flip_btn", on_click=flip_card)
    with col3:
        nav_button("→", key="next_btn", on_click=next_card, type="primary")


def render_lesson():
    topic = st.session_state.topic_data
    idx = st.session_state.card_index
    num_reels, num_flashcards, total = card_counts(topic)
    reel_transition = st.session_state.get("reel_transition", False)

    if idx < num_reels:
        if reel_transition and st.session_state.get("outgoing_reel_idx") is not None:
            render_reel_transition(topic, st.session_state.outgoing_reel_idx, idx, total)
        else:
            render_reel(topic, topic["reels"][idx], idx, total)
    else:
        render_flashcard(topic["flashcards"][idx - num_reels], idx, total, is_first=(idx == num_reels))

    st.session_state.reel_transition = False


def render_redirect():
    st.markdown(
        """
        <div style="text-align:center; font-size:1.6rem; font-weight:800; margin-bottom:1rem;">
            <span style="color:#FF9900;">AWS</span><span style="color:#232F3E;">OME</span>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.subheader("Looks like this topic isn't clicking right now. Try another one?")
    st.caption("Saved as incomplete — you can pick it back up anytime.")
    nav_button("Back to topics", on_click=go_home, type="primary")


@st.fragment(run_every=1)
def quiz_timer_fragment(q_index, total):
    if st.session_state.quiz_start_times[q_index] is None:
        st.session_state.quiz_start_times[q_index] = time.time()

    elapsed = time.time() - st.session_state.quiz_start_times[q_index]
    remaining = max(0.0, QUIZ_SECONDS - elapsed)

    st.caption(f"Question {q_index + 1} of {total}")
    st.progress(remaining / QUIZ_SECONDS)
    st.markdown(
        f'<div style="display:flex; align-items:center; gap:6px; color:#5A6B7B; font-size:0.9rem;">'
        f'{icon("clock", 18)} {int(remaining)}s</div>',
        unsafe_allow_html=True,
    )

    if remaining <= 0 and st.session_state.quiz_phase == "question":
        st.session_state.quiz_timed_out[q_index] = True
        st.session_state.quiz_phase = "feedback"
        st.rerun()


def render_answer_grid(q, q_index):
    rows = [st.columns(2), st.columns(2)]
    for opt_idx, option in enumerate(q["options"]):
        target_col = rows[opt_idx // 2][opt_idx % 2]
        symbol = KAHOOT_SYMBOLS[opt_idx % len(KAHOOT_SYMBOLS)]
        with target_col:
            with st.container(key=f"answer_opt_{opt_idx}"):
                nav_button(
                    f"{symbol} {option}",
                    key=f"answer_btn_{opt_idx}",
                    on_click=select_answer,
                    args=(q_index, opt_idx),
                )


def render_quiz_feedback(q):
    idx = st.session_state.quiz_index
    quiz = st.session_state.topic_data["quiz"]
    selected = st.session_state.quiz_answers[idx]
    timed_out = st.session_state.quiz_timed_out[idx]

    if timed_out:
        header_icon, header_text, header_color = "clock", "Time's up", "#8A97A6"
    elif selected == q["answer"]:
        header_icon, header_text, header_color = "check", "Correct", "#1E8E3E"
    else:
        header_icon, header_text, header_color = "cross", "Wrong", "#E21B3C"

    st.markdown(
        f'<div style="display:flex; align-items:center; gap:8px; font-size:1.3rem; '
        f'font-weight:800; color:{header_color}; margin-bottom:0.5rem;">'
        f'{icon(header_icon, 26)} {header_text}</div>',
        unsafe_allow_html=True,
    )

    st.write(f"**Correct answer:** {q['options'][q['answer']]}")
    st.caption(q["why"])

    is_last = idx == len(quiz) - 1
    label = "See results" if is_last else "Next question →"
    nav_button(label, key="quiz_next_btn", on_click=advance_quiz, type="primary")


def render_quiz():
    topic = st.session_state.topic_data
    quiz = topic["quiz"]
    idx = st.session_state.quiz_index
    q = quiz[idx]

    if st.session_state.quiz_phase == "question":
        quiz_timer_fragment(idx, len(quiz))
        st.markdown(
            f"""<div style="font-weight:700; font-size:1.2rem; color:#232F3E;
                margin:12px 0;">{q['q']}</div>""",
            unsafe_allow_html=True,
        )
        render_answer_grid(q, idx)
    else:
        st.caption(f"Question {idx + 1} of {len(quiz)}")
        render_quiz_feedback(q)


def render_results():
    st.markdown(
        """
        <div style="text-align:center; font-size:1.6rem; font-weight:800; margin-bottom:1rem;">
            <span style="color:#FF9900;">AWS</span><span style="color:#232F3E;">OME</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    passed = st.session_state.passed

    col1, col2, col3 = st.columns(3)
    col1.metric("Score", f"{st.session_state.quiz_correct}/{st.session_state.quiz_total}")
    attention = st.session_state.attention
    col2.metric("Attention", f"{round(attention * 100)}%")
    col3.metric("XP gained", f"+{st.session_state.xp_gained}")

    if attention >= FOCUSED_THRESHOLD:
        st.markdown(
            f'<div style="display:flex; align-items:center; gap:6px;">{icon("target", 18)} Focused</div>',
            unsafe_allow_html=True,
        )
    else:
        st.write("You rushed some cards, which can cost quiz marks")

    if passed:
        if st.session_state.leveled_up:
            st.success(f"LEVEL UP → Level {st.session_state.progress['level']}")

        if st.session_state.new_badges:
            st.markdown(badge_pills(st.session_state.new_badges), unsafe_allow_html=True)
    else:
        pass_mark_pct = round(PASS_MARK * 100)
        st.error(f"You need {pass_mark_pct}% to pass. You scored {st.session_state.attempt_score_pct}%.")

    st.divider()

    topic = st.session_state.topic_data
    quiz = topic["quiz"]
    for i, q in enumerate(quiz):
        selected = st.session_state.quiz_answers[i]
        timed_out = st.session_state.quiz_timed_out[i]
        if timed_out:
            review_icon, review_color = "clock", "#8A97A6"
        elif selected == q["answer"]:
            review_icon, review_color = "check", "#1E8E3E"
        else:
            review_icon, review_color = "cross", "#E21B3C"
        st.markdown(
            f'<div style="display:flex; align-items:flex-start; gap:8px; margin-top:0.5rem;">'
            f'<span style="color:{review_color}; flex-shrink:0;">{icon(review_icon, 18)}</span>'
            f'<strong>{q["q"]}</strong></div>',
            unsafe_allow_html=True,
        )
        st.caption(q["why"])

    if passed:
        nav_button("Back to topics", on_click=go_home, type="primary")
    else:
        col_a, col_b = st.columns(2)
        with col_a:
            nav_button(
                "Try again",
                key="try_again_btn",
                on_click=start_lesson,
                args=(st.session_state.current_topic,),
                type="primary",
            )
        with col_b:
            nav_button("Back to topics", key="back_btn_fail", on_click=go_home)


def main():
    st.set_page_config(page_title="AWSOME", page_icon=":material/school:")
    inject_css()
    init_state()

    screen = st.session_state.screen
    step = current_step()
    scroll_to_top(f"{screen}-{step}")

    is_reel_transition = screen == "lesson" and st.session_state.get("reel_transition", False)
    key_prefix = "viewnofade" if is_reel_transition else "view"

    with st.container(key=f"{key_prefix}_{screen}_{step}"):
        if screen == "login":
            render_login()
        elif screen == "tutorial":
            render_tutorial()
        elif screen == "home":
            render_home()
        elif screen == "lesson":
            render_lesson()
        elif screen == "redirect":
            render_redirect()
        elif screen == "quiz":
            render_quiz()
        elif screen == "results":
            render_results()

    if screen == "results" and st.session_state.get("leveled_up"):
        render_celebration()


main()
