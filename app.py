from flask import Flask, request, jsonify, render_template
from agent import ask, search_restaurants_raw, plan_night

app = Flask(__name__)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    user_message = data.get("message", "").strip()
    if not user_message:
        return jsonify({"error": "Empty message"}), 400
    try:
        reply = ask(user_message)
        restaurants = search_restaurants_raw(user_message)
        return jsonify({"reply": reply, "restaurants": restaurants})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/plan", methods=["POST"])
def plan():
    data = request.get_json()
    user_message = data.get("message", "").strip()
    if not user_message:
        return jsonify({"error": "Empty message"}), 400
    try:
        result = plan_night(user_message)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True, port=5000)