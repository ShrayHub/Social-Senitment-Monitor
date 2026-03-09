from report_generator import generate_report_pdf
import pandas as pd
import random
from flask import Flask, render_template, request
from dotenv import load_dotenv
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from database import init_db, add_schedule
from email_scheduler import start_scheduler

# -------------------- INIT --------------------
init_db()
load_dotenv(".env")

# -------------------- DATASET LOAD --------------------
DATASET_PATH = "sentiment140.csv"

COLUMNS = ["target", "ids", "date", "flag", "user", "text"]

df = pd.read_csv(
    DATASET_PATH,
    encoding="latin-1",
    names=COLUMNS
)

df["sentiment"] = df["target"].map({
    0: "NEGATIVE",
    4: "POSITIVE"
})

# -------------------- MODEL SETUP --------------------
MODEL_NAME = "cardiffnlp/twitter-roberta-base-sentiment"
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModelForSequenceClassification.from_pretrained(MODEL_NAME)
model.eval()

# -------------------- TWEET FETCH (KAGGLE DATASET) --------------------
def getTweets(query, limit=100):
    filtered = df[df["text"].str.contains(query, case=False, na=False)]

    if filtered.empty:
        return []

    sampled = filtered.sample(
        n=min(limit, len(filtered)),
        random_state=random.randint(0, 9999)
    )

    tweets = []

    class TweetWrapper:
        def __init__(self, row):
            self.id = row["ids"]
            self.full_text = row["text"]
            self.user = type(
                "User",
                (),
                {
                    "name": row["user"],
                    "screen_name": row["user"],
                    "profile_image_url": ""
                }
            )

    for _, row in sampled.iterrows():
        tweets.append(TweetWrapper(row))

    return tweets

# -------------------- SENTIMENT --------------------
def sentiment(tweets):
    positive, negative, neutral = [], [], []

    for item in tweets:
        inputs = tokenizer(item.full_text, return_tensors="pt", truncation=True)

        with torch.no_grad():
            outputs = model(**inputs)

        probs = torch.nn.functional.softmax(outputs.logits, dim=1)[0]
        neg, neu, pos = probs.tolist()

        item.score = pos - neg

        if pos > max(neg, neu):
            positive.append(item)
        elif neg > max(pos, neu):
            negative.append(item)
        else:
            neutral.append(item)

    return positive, negative, neutral

# -------------------- CLEANING --------------------
def removeDuplicate(tweets):
    uniq_texts = set()
    clean, removed = [], []

    for item in tweets:
        if item.full_text not in uniq_texts and item.full_text.count("#") <= 5:
            uniq_texts.add(item.full_text)
            clean.append(item)
        else:
            removed.append(item)

    return clean, removed

# -------------------- CSV --------------------
def saveToCsv(tweets):
    rows = []

    for item in tweets:
        inputs = tokenizer(item.full_text, return_tensors="pt", truncation=True)
        with torch.no_grad():
            outputs = model(**inputs)

        probs = torch.nn.functional.softmax(outputs.logits, dim=1)[0]
        neg, neu, pos = probs.tolist()

        if pos > max(neg, neu):
            label = f"POSITIVE {pos:.3f}"
        elif neg > max(pos, neu):
            label = f"NEGATIVE {neg:.3f}"
        else:
            label = f"NEUTRAL {neu:.3f}"

        rows.append([
            item.user.name,
            item.user.screen_name,
            item.full_text,
            label
        ])

    pd.DataFrame(
        rows,
        columns=["User name", "Handle", "Tweets", "Sentiment"]
    ).to_csv("output.csv", index=False)

# -------------------- FLASK APP --------------------
app = Flask(__name__)

@app.route("/")
@app.route("/home")
def home():
    return render_template("index.html")

@app.route("/analysis")
def analysis():
    return render_template("analysis.html")

@app.route("/reports")
def reports():
    return render_template("reports.html")

@app.route("/schedule-report", methods=["POST"])
def schedule_report():
    email = request.form.get("email")
    frequency = request.form.get("frequency")
    day_value = request.form.get("day_value")

    add_schedule(email, frequency, day_value)

    if frequency == "daily":
        success_message = "You will receive this daily at 9:30 AM IST."
    elif frequency == "weekly":
        success_message = f"You will receive this weekly on {day_value} at 9:30 AM IST."
    elif frequency == "monthly":
        success_message = f"You will receive this monthly on the {day_value} at 9:30 AM IST."
    else:
        success_message = "Report scheduled."

    return render_template("reports.html", success_message=success_message)

@app.route("/searchTopic", methods=["POST"])
def searchTopic():
    name = request.form.get("name", "").strip()

    if not name:
        return render_template("analysis.html", error="please put keyword")

    tweetList = getTweets(name)
    cleanTweets, removedTweets = removeDuplicate(tweetList)

    if not tweetList:
        return render_template(
            "analysis.html",
            error="No matching tweets found in dataset."
        )

    firstHundredTweets = cleanTweets[:100]
    saveToCsv(firstHundredTweets)

    positive, negative, neutral = sentiment(firstHundredTweets)

    positive = sorted(positive, key=lambda x: x.score, reverse=True)
    negative = sorted(negative, key=lambda x: x.score)
    neutral = sorted(neutral, key=lambda x: x.score)

    summary = {
        "query": name,
        "total_tweets": len(tweetList),
        "removed_list": len(removedTweets),
        "clear_tweets": len(cleanTweets),
        "sentiment_input": len(firstHundredTweets),
        "positive": len(positive),
        "negative": len(negative),
        "neutral": len(neutral)
    }

    generate_report_pdf(summary)

    return render_template(
        "analysis.html",
        positive=positive,
        negative=negative,
        neutral=neutral,
        removed=removedTweets,
        summary=summary
    )

# -------------------- RUN --------------------
if __name__ == "__main__":
    start_scheduler()
    app.run(port=5000, use_reloader=False)
