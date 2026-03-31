# 🍜 Philly Eats AI — Restaurant Recommender

> Built for the SnowLeopard AI Hackathon by **Kevin Liu & Pranav Shrihari**

A conversational AI web app that helps you discover the best restaurants in Philadelphia. Ask it anything — cuisine, vibe, price range, neighborhood — and it returns real, data-backed recommendations powered by GPT-4o and SnowLeopard's semantic search API.

---

## 🚀 Demo

Ask things like:
- *"Find me a quiet Italian spot in Center City under $30"*
- *"Best BYOB restaurants with high ratings near Old City"*
- *"Plan me a full night out — dinner and dessert in South Philly"*

---

## 🧠 How It Works

```
User → Flask Web UI → LangChain Agent (GPT-4o)
                              ↓
                   SnowLeopard Semantic Search
                              ↓
                  Philadelphia Restaurant Dataset
                              ↓
                  Conversational Recommendations
```

The agent uses GPT-4o as its reasoning engine and calls a `query_restaurants` tool that hits the SnowLeopard API for natural-language semantic search over a rich Philly restaurant dataset. A separate `/plan` endpoint lets the agent orchestrate a full night-out itinerary.

---

## 🛠 Tech Stack

| Layer | Technology |
|---|---|
| Web Framework | Flask 3.x |
| AI Agent | LangChain + GPT-4o (OpenAI) |
| Semantic Search | SnowLeopard API |
| Frontend | HTML/CSS (Jinja2 templates) |
| Config | python-dotenv |

---

## ⚙️ Setup

### 1. Clone the repo
```bash
git clone https://github.com/kliu3816/Kevin_Pranav_hackathon.git
cd Kevin_Pranav_hackathon
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure environment variables

Create a `.env` file in the project root:
```
OPENAI_API_KEY=your_openai_api_key
SNOWLEOPARD_API_KEY=your_snowleopard_api_key
SNOWLEOPARD_DATAFILE_ID=your_datafile_id
```

### 4. Run the app
```bash
python app.py
```

Then open [http://localhost:5000](http://localhost:5000) in your browser.

---

## 📁 Project Structure

```
├── app.py           # Flask routes (/chat, /plan)
├── agent.py         # LangChain agent, tools, and SnowLeopard integration
├── filter.py        # Data filtering utilities
├── templates/       # HTML frontend
├── requirements.txt
└── .env             # (not committed) API keys
```

---

## 🔑 API Keys

You'll need:
- **OpenAI API key** — [platform.openai.com](https://platform.openai.com)
- **SnowLeopard API key + Datafile ID** — provided at the hackathon

---

## 👥 Team

- **Kevin Liu** — [@kliu3816](https://github.com/kliu3816)
- **Pranav**

---

## 📄 License

MIT
