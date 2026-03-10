# COUNTERPICK ⚡

> AI-powered product alternative finder — find better, cheaper, greener, or longer-lasting alternatives to any product in seconds.

![Python](https://img.shields.io/badge/Python-3.10+-blue?style=flat-square&logo=python)
![Flask](https://img.shields.io/badge/Flask-3.0+-black?style=flat-square&logo=flask)
![Groq](https://img.shields.io/badge/Groq-LLaMA_3.3_70B-orange?style=flat-square)
![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)

---

## What is Counterpick?

Counterpick is a Flask web app powered by the **Groq AI API (LLaMA 3.3 70B)** that helps you find the best alternative to any product. Type in any product, choose your priority, and get an instant AI-generated counterpick with detailed reasoning, pricing, specs, and buy links.

---

## Features

### ⚡ Counterpick Search
Enter any product and get the best alternative based on your chosen priority:
- **Best Quality** — highest performing product regardless of price
- **Cheapest** — best product that costs significantly less
- **Eco-Friendly** — most sustainable or ethically made alternative
- **Best Battery** — best battery life or power efficiency
- **Most Durable** — most rugged and long-lasting option

### ⚔️ Battle Mode
Compare two products head-to-head with an AI-generated scorecard across 5 dimensions: Value, Build Quality, Performance, Features, and Ecosystem.

### 🏆 Top 10 Rankings
Get the definitive top 10 best products in any category with scores, specs, pros/cons, and buy links.

### 🏛️ Hall of Fame
Browse 50+ product categories and discover the undisputed #1 winner in each — backed by cross-platform consensus from Amazon, Reddit, Wirecutter, The Verge, and YouTube.

### 🔴 Reddit Pulse
See what real Reddit users say about any product — sentiment score, loved/criticized lists, top insight, and sample community quotes.

### 🌍 Regional Pricing
Switch between US, UK, CA, AU, DE, and JP storefronts for localized buy links.

### 📤 Share Card
Download a PNG of your counterpick result or copy a text summary to share anywhere.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python + Flask |
| AI | Groq API — LLaMA 3.3 70B Versatile |
| Frontend | Vanilla JS + HTML/CSS (single template) |
| Fonts | Bebas Neue, Space Mono, DM Sans |
| Images | Multi-proxy client-side fetching (DuckDuckGo, Bing, Google, Amazon) |

---

## Getting Started

### 1. Clone the repo

```bash
git clone https://github.com/chadbarcelo7/Counterpick.git
cd Counterpick
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Get a free Groq API key

Sign up at [console.groq.com](https://console.groq.com) — it's free.

### 4. Set your API key and run

**Windows (PowerShell):**
```powershell
$env:GROQ_API_KEY="your_groq_api_key_here"
python app.py
```

**Mac / Linux:**
```bash
export GROQ_API_KEY="your_groq_api_key_here"
python app.py
```

### 5. Open in your browser

```
http://localhost:5000
http://localhost:5000/halloffame
```

---

## Project Structure

```
Counterpick/
├── app.py                    # Flask backend + all API routes + AI prompts
├── requirements.txt          # Python dependencies
├── templates/
│   ├── index.html            # Main app (search, battle, top 10, Reddit pulse)
│   └── halloffame.html       # Hall of Fame page (50+ categories)
└── README.md
```

---

## API Routes

| Route | Method | Description |
|-------|--------|-------------|
| `/` | GET | Main app page |
| `/halloffame` | GET | Hall of Fame page |
| `/api/counterpick` | POST | Find a product alternative |
| `/api/battle` | POST | Compare two products head-to-head |
| `/api/top10` | POST | Get top 10 products in a category |
| `/api/halloffame` | POST | Get the #1 winner in a category |
| `/api/reddit` | POST | Get Reddit sentiment for a product |
| `/api/image` | GET | Server-side product image proxy |

---

## Requirements

```
flask>=3.0.0
groq>=0.9.0
gunicorn
```

---

## Deployment

### Deploy to Render (free)

1. Push your code to GitHub
2. Go to [render.com](https://render.com) → New → Web Service
3. Connect your repo
4. Set:
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn app:app`
5. Add environment variable: `GROQ_API_KEY` = your key
6. Click Deploy

---

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GROQ_API_KEY` | ✅ Yes | Your Groq API key from console.groq.com |

---

## License

MIT — free to use, modify, and distribute.

---

## Author

Built by [@chadbarcelo7](https://github.com/chadbarcelo7)

---

> ⚠️ Always verify product details and prices before purchasing. AI-generated recommendations are for informational purposes only.
