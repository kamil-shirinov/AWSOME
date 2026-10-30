# AWSOME (AWS North × Northumbria Hackathon, September 2026)

Learn AWS the way you already scroll: short reels, flashcards and a Kahoot-style quiz, with an attention score that notices when you skim.

3rd place at the AWS North x Northumbria Hackathon, 25 September 2026. Built in just over five hours.

<img width="2514" height="1012" alt="screens" src="https://github.com/user-attachments/assets/c81d2ae0-5177-43fd-938f-c4e7e64f8a18" />


## Why

Learning AWS usually means long documentation pages and hour-long videos, while most people now learn in short bursts on their phones. And when you skim, it's easy to think you've learned more than you have.

## How it works

Each topic is a short lesson:

1. **Three reels** introduce the service in a 9:16 feed. The video slots are placeholders for now, with the voiceover shown as a caption.
2. **Four flashcards** lock in the key facts. Press Flip to turn each one over.
3. **A five-question quiz**, Kahoot-style: one question at a time, 20 seconds each, four coloured answer tiles, and feedback after every answer.

Behind the scenes:

- **Attention score.** AWSOME times every reel and flashcard against the time it needs (8 seconds to read a reel caption, 5 for a flashcard), caps each card at 100% and averages them. Below 30%, you don't get the quiz: the app suggests another topic and marks this one incomplete.
- **Pass mark.** You need 80% on the quiz to pass. Passing a topic for the first time earns 100 XP, and every 100 XP is a new level.
- **Best scores and retakes.** Each topic keeps your best score, and you can retake it any time to improve.
- **Badges.** First Steps for your first pass, Laser Focus for passing with 90% attention or more, and Perfect Score for getting every answer right.

Live topics today: Amazon S3 and AWS Lambda. EC2, IAM, DynamoDB and Bedrock are coming soon, and Challenge mode unlocks at Level 6.

## Built with

- **Python and Streamlit** for the app, styled as a phone with custom CSS, including 3D card flips, reel slide transitions and screen fades.
- **Local JSON storage.** Lessons are JSON files in content/, and each learner's progress (XP, level, badges and best scores) is saved as a JSON file in progress/.

## Project structure

```
app.py            Streamlit UI: screens, phone frame, quiz, animations
logic.py          Rules: attention score, pass mark, XP, levels, badges
store.py          Data access: lessons from content/, progress saved to progress/
test_logic.py     Unit tests for logic.py
content/          Lesson files (s3.json, lambda.json)
.streamlit/       Theme
```

## Run it locally

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

The app reads lessons from content/ and saves progress to a local progress/ folder. Run the tests with pytest -q.

## What's next

- Move lessons to Amazon S3 and learner progress to Amazon DynamoDB, using boto3.
- Real AWS videos in the reel slots through the YouTube API, with actual watch time feeding the attention score. One of the AWS reps suggested this on the day.
- An API Gateway and Lambda backend in front of that storage.
- Amazon Bedrock generating new topics from AWS documentation.
- Sign-in with Amazon Cognito.
- Swipe gestures in a native or React version.
- Spaced repetition that brings back the cards you rushed.

## Team

Led and built by Kamil Shirinov at the AWS North × Northumbria Hackathon, with teammates contributing ideas and suggesting fixes and additions.

Licence: all rights reserved, published for review.
