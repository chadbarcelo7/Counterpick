from flask import Flask, render_template, request, jsonify
from groq import Groq
import json
import os
import urllib.request
import urllib.parse

template_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
app = Flask(__name__, template_folder=template_dir)

client = None

def get_groq():
    global client
    if client is None:
        client = Groq(api_key=os.environ.get("GROQ_API_KEY", ""))
    return client

# ── SYSTEM PROMPTS ────────────────────────────────────────────────────────────

COUNTERPICK_PROMPT = """You are COUNTERPICK — an AI engine that finds the best alternative to any product.

CATEGORY MATCHING RULE — MOST IMPORTANT:
You MUST match the exact product category, form factor, and use case.
- Handheld console → only handheld console
- Over-ear headphones → only over-ear headphones
- Robot vacuum → only robot vacuum
Never suggest a different form factor or category.

PRIORITY RULE:
The user has chosen a priority angle: {priority}
Your counterpick MUST win specifically on that angle above all else.
Priority meanings:
- cheapest: find the best product that costs significantly less
- best_quality: find the highest quality / best performing product regardless of price
- eco_friendly: find the most sustainable, eco-conscious, or ethically made product
- best_battery: find the product with the best battery life / power efficiency
- most_durable: find the most rugged, long-lasting, best-built product

Rules:
- Always return a REAL, widely available product.
- Never invent fake brands or models.
- Avoid medical, prescription, or dangerous products.
- Never break JSON format.

Return ONLY this JSON:
{{
  "original_product": "",
  "original_product_search": "",
  "original_category": "",
  "counterpick_product": "",
  "counterpick_product_search": "",
  "priority_angle": "",
  "reason_summary": "",
  "how_it_beats_it": ["", "", ""],
  "price_tier_comparison": "cheaper | similar | more expensive",
  "ideal_for": "",
  "potential_drawbacks": ["", ""],
  "affiliate_targets": [
    {{ "store": "Amazon", "url": "", "price": "" }},
    {{ "store": "Walmart", "url": "", "price": "" }},
    {{ "store": "Best Buy", "url": "", "price": "" }}
  ],
  "original_price_estimate": "",
  "counterpick_price_estimate": "",
  "regional_stores": {{
    "UK": {{ "store": "Amazon UK", "url": "", "price": "" }},
    "DE": {{ "store": "Amazon DE", "url": "", "price": "" }},
    "AU": {{ "store": "Amazon AU", "url": "", "price": "" }},
    "CA": {{ "store": "Amazon CA", "url": "", "price": "" }},
    "JP": {{ "store": "Amazon JP", "url": "", "price": "" }}
  }}
}}

- "priority_angle": short label of what this counterpick wins on (e.g. "Best Value", "Eco-Friendly", "Longest Battery")
- "original_product_search": exact model name for image search e.g. "Sony WH-1000XM5 Wireless Headphones Black"
- "price_tier_comparison": ONLY one of: "cheaper", "similar", "more expensive"
- regional store URLs: use amazon.co.uk, amazon.de, amazon.com.au, amazon.ca, amazon.co.jp search URLs
- Return ONLY valid JSON. No preamble, no markdown."""

BATTLE_PROMPT = """You are COUNTERPICK BATTLE MODE — an AI judge that compares two products head-to-head.

CATEGORY RULE: Both products should be in the same or similar category. If they are different categories, still judge them fairly.

Analyze both products across all dimensions and declare a winner with detailed reasoning.

Return ONLY this JSON:
{{
  "product_a": "",
  "product_a_search": "",
  "product_b": "",
  "product_b_search": "",
  "category": "",
  "winner": "A | B | TIE",
  "winner_name": "",
  "verdict_summary": "",
  "product_a_price": "",
  "product_b_price": "",
  "scorecard": [
    {{ "dimension": "Value for Money", "a_score": 0, "b_score": 0, "winner": "A | B | TIE", "note": "" }},
    {{ "dimension": "Build Quality", "a_score": 0, "b_score": 0, "winner": "A | B | TIE", "note": "" }},
    {{ "dimension": "Performance", "a_score": 0, "b_score": 0, "winner": "A | B | TIE", "note": "" }},
    {{ "dimension": "Features", "a_score": 0, "b_score": 0, "winner": "A | B | TIE", "note": "" }},
    {{ "dimension": "Ecosystem / Support", "a_score": 0, "b_score": 0, "winner": "A | B | TIE", "note": "" }}
  ],
  "buy_a_if": "",
  "buy_b_if": "",
  "affiliate_a": {{ "store": "Amazon", "url": "", "price": "" }},
  "affiliate_b": {{ "store": "Amazon", "url": "", "price": "" }}
}}

- scores are 1-10
- "winner" in scorecard: "A", "B", or "TIE"
- "verdict_summary": 2-3 sentence overall verdict
- "buy_a_if" / "buy_b_if": one sentence each on who should buy which
- Return ONLY valid JSON. No preamble, no markdown."""

REDDIT_PROMPT = """You are a product research analyst. Based on your knowledge of Reddit discussions, forums, and consumer reviews, summarize what real users say about this product.

Product: {product}

Return ONLY this JSON:
{{
  "product": "",
  "overall_sentiment": "positive | mixed | negative",
  "sentiment_score": 0,
  "loved_for": ["", "", ""],
  "criticized_for": ["", "", ""],
  "common_subreddits": ["", ""],
  "top_insight": "",
  "would_buy_again_percent": 0,
  "sample_quotes": [
    {{ "quote": "", "sentiment": "positive | negative | neutral", "source": "r/subreddit" }},
    {{ "quote": "", "sentiment": "positive | negative | neutral", "source": "r/subreddit" }}
  ]
}}

- "sentiment_score": 1-10 (10 = overwhelmingly loved)
- "would_buy_again_percent": estimated % of users who'd repurchase
- "top_insight": the single most important thing Reddit says about this product
- "sample_quotes": realistic paraphrased quotes that reflect actual community sentiment (NOT invented — reflect real known opinions)
- Return ONLY valid JSON. No preamble, no markdown."""


# ── ROUTES ────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/counterpick", methods=["POST"])
def counterpick():
    data = request.get_json()
    product = data.get("product", "").strip()
    priority = data.get("priority", "best_quality")

    if not product:
        return jsonify({"error": "No product provided"}), 400

    try:
        prompt = COUNTERPICK_PROMPT.replace("{priority}", priority)
        completion = get_groq().chat.completions.create(
            model="llama-3.3-70b-versatile",
            max_tokens=1500,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": f"Find the counterpick for: {product}"}
            ]
        )
        parsed = json.loads(completion.choices[0].message.content)
        return jsonify(parsed)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/battle", methods=["POST"])
def battle():
    data = request.get_json()
    product_a = data.get("product_a", "").strip()
    product_b = data.get("product_b", "").strip()

    if not product_a or not product_b:
        return jsonify({"error": "Both products required"}), 400

    try:
        completion = get_groq().chat.completions.create(
            model="llama-3.3-70b-versatile",
            max_tokens=1500,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": BATTLE_PROMPT},
                {"role": "user", "content": f"Battle: {product_a} vs {product_b}"}
            ]
        )
        parsed = json.loads(completion.choices[0].message.content)
        return jsonify(parsed)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/reddit", methods=["POST"])
def reddit_pulse():
    data = request.get_json()
    product = data.get("product", "").strip()

    if not product:
        return jsonify({"error": "No product provided"}), 400

    try:
        prompt = REDDIT_PROMPT.replace("{product}", product)
        completion = get_groq().chat.completions.create(
            model="llama-3.3-70b-versatile",
            max_tokens=1000,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": f"What does Reddit say about: {product}"}
            ]
        )
        parsed = json.loads(completion.choices[0].message.content)
        return jsonify(parsed)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True, port=5000)
