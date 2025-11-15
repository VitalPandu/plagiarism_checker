from flask import Flask, request, jsonify
from flask_cors import CORS

from util import calculate_cosine_similarity, highlight_matching_text
import joblib

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes
model = joblib.load("flask_api/plagiarism_model.pkl")

@app.route("/", methods=["POST"])
@app.route("/check", methods=["POST"])
def check():
    try:
        file1 = request.files['original']
        file2 = request.files['submission']
        text1 = file1.read().decode("utf-8")
        text2 = file2.read().decode("utf-8")

        similarity = calculate_cosine_similarity(text1, text2)
        prediction = model.predict([[similarity]])[0]
        probability = model.predict_proba([[similarity]])[0][1]
        highlight1, highlight2 = highlight_matching_text(text1, text2)

        return jsonify({
            "similarity_score": round(similarity, 4),
            "plagiarized": bool(prediction),
            "probability": round(probability, 4),
            "highlighted_original": highlight1,
            "highlighted_submission": highlight2
        })
    except Exception as e:
        print(str(e))
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True, port=5000)
