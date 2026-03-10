from flask import Flask, render_template, request, jsonify
from groq import Groq
import json
import os

template_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
app = Flask(__name__, template_folder=template_dir)

client = None

def get_groq():
    global client
    if client is None:
        client = Groq(api_key=os.environ.get("GROQ_API_KEY", ""))
    return client


# ── PROMPTS ───────────────────────────────────────────────────────────────────

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

- "priority_angle": short label e.g. "Best Value", "Eco-Friendly", "Longest Battery"
- "original_product_search": exact model name for image search e.g. "Sony WH-1000XM5 Wireless Headphones Black"
- "price_tier_comparison": ONLY one of: "cheaper", "similar", "more expensive"
- regional store URLs: use amazon.co.uk, amazon.de, amazon.com.au, amazon.ca, amazon.co.jp search URLs
- Return ONLY valid JSON. No preamble, no markdown."""


BATTLE_PROMPT = """You are COUNTERPICK BATTLE MODE — an AI judge that compares two products head-to-head.

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
- "sample_quotes": realistic paraphrased quotes reflecting real known opinions
- Return ONLY valid JSON. No preamble, no markdown."""


TOP10_PROMPT = """You are COUNTERPICK TOP 10 — an expert product ranker.

Given a product category, return the definitive top 10 ranked list of the best products available right now.

Rules:
- Only REAL, widely available products. No invented brands or models.
- Rank by overall value, reputation, features, and consumer satisfaction.
- Each product must be distinct — no duplicates.
- Cover a range of price points where possible.
- Never break JSON format.

Return ONLY this JSON:
{{
  "category": "",
  "category_icon": "",
  "ranking_basis": "",
  "last_updated": "2025",
  "products": [
    {{
      "rank": 1,
      "name": "",
      "product_search": "",
      "brand": "",
      "tagline": "",
      "price_estimate": "",
      "price_tier": "budget | mid-range | premium | ultra-premium",
      "score": 0,
      "best_for": "",
      "key_specs": ["", "", ""],
      "pros": ["", ""],
      "cons": [""],
      "buy_url": "",
      "award": ""
    }}
  ]
}}

- "score": overall score out of 100
- "price_tier": one of: "budget", "mid-range", "premium", "ultra-premium"
- "award": optional label like "Best Overall", "Best Budget", "Editor's Pick" — leave empty string if none
- "buy_url": Amazon search URL e.g. https://www.amazon.com/s?k=Product+Name
- "product_search": exact model name for image search e.g. "Sony WH-1000XM5 Wireless Headphones"
- Return ONLY valid JSON. No preamble, no markdown."""


HALL_OF_FAME_PROMPT = """You are COUNTERPICK HALL OF FAME — the world's most authoritative product ranking engine.

For a given product category, return the single #1 WINNER product backed by cross-platform consensus:
Amazon ratings, Reddit opinions, YouTube reviews, Wirecutter, The Verge, RTINGS, Tom's Guide.

Rules:
- Only REAL, widely available products.
- The winner must be genuinely dominant — not just popular, but the consensus best.
- Never invent fake reviews or fake sources.
- Never break JSON format.

Return ONLY this JSON:
{
  "category": "",
  "category_icon": "",
  "category_description": "",
  "winner": {
    "name": "",
    "brand": "",
    "product_search": "",
    "tagline": "",
    "why_it_wins": "",
    "price_estimate": "",
    "price_tier": "budget | mid-range | premium | ultra-premium",
    "overall_score": 0,
    "scores": {
      "value": 0,
      "performance": 0,
      "build_quality": 0,
      "features": 0,
      "user_satisfaction": 0
    },
    "key_specs": ["", "", "", ""],
    "pros": ["", "", ""],
    "cons": ["", ""],
    "best_for": "",
    "not_for": "",
    "buy_url": "",
    "platform_reviews": [
      { "platform": "Amazon", "rating": "", "quote": "", "verdict": "positive" },
      { "platform": "Reddit", "rating": "", "quote": "", "verdict": "positive" },
      { "platform": "Wirecutter", "rating": "", "quote": "", "verdict": "positive" },
      { "platform": "The Verge", "rating": "", "quote": "", "verdict": "positive" },
      { "platform": "YouTube Community", "rating": "", "quote": "", "verdict": "positive" }
    ],
    "runner_up": "",
    "runner_up_reason": "",
    "award_label": ""
  }
}

- "overall_score": 0-100
- "scores": each 0-10
- "why_it_wins": 2-3 sentences on why this beats all others
- "platform_reviews": realistic consensus quotes reflecting actual known sentiment. Ratings like "4.7/5", "9.2/10", "#1 Pick"
- "verdict": "positive", "mixed", or "negative"
- "award_label": e.g. "🏆 Category Champion", "👑 Undisputed Winner", "⭐ Editor's Choice"
- "price_tier": one of: "budget", "mid-range", "premium", "ultra-premium"
- "buy_url": Amazon search URL e.g. https://www.amazon.com/s?k=Product+Name
- Return ONLY valid JSON. No preamble, no markdown."""


# ── ROUTES ────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/halloffame")
def halloffame():
    return render_template("halloffame.html")


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
            model="llama-3.3-70b-versatile", max_tokens=1500,
            response_format={"type": "json_object"},
            messages=[{"role": "system", "content": prompt},
                      {"role": "user", "content": f"Find the counterpick for: {product}"}])
        return jsonify(json.loads(completion.choices[0].message.content))
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
            model="llama-3.3-70b-versatile", max_tokens=1500,
            response_format={"type": "json_object"},
            messages=[{"role": "system", "content": BATTLE_PROMPT},
                      {"role": "user", "content": f"Battle: {product_a} vs {product_b}"}])
        return jsonify(json.loads(completion.choices[0].message.content))
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
            model="llama-3.3-70b-versatile", max_tokens=1000,
            response_format={"type": "json_object"},
            messages=[{"role": "system", "content": prompt},
                      {"role": "user", "content": f"What does Reddit say about: {product}"}])
        return jsonify(json.loads(completion.choices[0].message.content))
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/top10", methods=["POST"])
def top10():
    data = request.get_json()
    category = data.get("category", "").strip()
    if not category:
        return jsonify({"error": "No category provided"}), 400
    try:
        completion = get_groq().chat.completions.create(
            model="llama-3.3-70b-versatile", max_tokens=3000,
            response_format={"type": "json_object"},
            messages=[{"role": "system", "content": TOP10_PROMPT},
                      {"role": "user", "content": f"Give me the top 10 best products for: {category}"}])
        return jsonify(json.loads(completion.choices[0].message.content))
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/halloffame", methods=["POST"])
def hall_of_fame():
    data = request.get_json()
    category = data.get("category", "").strip()
    if not category:
        return jsonify({"error": "No category provided"}), 400
    try:
        completion = get_groq().chat.completions.create(
            model="llama-3.3-70b-versatile", max_tokens=2000,
            response_format={"type": "json_object"},
            messages=[{"role": "system", "content": HALL_OF_FAME_PROMPT},
                      {"role": "user", "content": f"Who is the undisputed #1 winner in: {category}"}])
        return jsonify(json.loads(completion.choices[0].message.content))
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True, port=5000)
