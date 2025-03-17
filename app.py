import sys
import os
import glob
import re
import json
import time
import numpy as np
import pandas as pd
from pred_utils import get_image_preds
from flask import Flask, request, render_template, jsonify, session

# ============================================================================
# CONFIGURATION
# ============================================================================

# Initialize the Flask application
app = Flask(__name__)
app.secret_key = "your_secret_key"
app.config["UPLOAD_FOLDER"] = "uploads"
app.config["JSON_FOLDER"] = "static/json"

# Global variables
form_questions = {}

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================


def save_json(path, data):
    """Save data to a JSON file with proper indentation."""
    with open(path, "w") as f:
        json.dump(data, f, indent=4)


def load_json(path):
    """Load data from a JSON file."""
    with open(path, "r") as f:
        data = json.load(f)
    return data


def get_feedback_path(user, timestamp):
    """
    Create and return a path for storing user feedback.

    Args:
        user (str): Username
        timestamp (str): Timestamp for the feedback

    Returns:
        str: Path to the feedback directory
    """
    user_folder = re.sub(r"\W", "_", user)
    feedback_path = os.path.join("results", user_folder, timestamp)
    os.makedirs(feedback_path, exist_ok=True)
    return feedback_path


# ============================================================================
# ROUTES
# ============================================================================


@app.route("/")
def index():
    """
    Render the index page.

    Returns:
        str: Rendered HTML for the index page.
    """
    return render_template("main.html")


@app.route("/main")
def main():
    """
    Render the main page.

    Returns:
        str: Rendered HTML for the main page.
    """
    return render_template("main.html")


@app.route("/submit-feedback-compare", methods=["POST"])
def submit_feedback_compare():
    """
    Handle submission of feedback data comparing two models.

    Returns:
        JSON response: Success or error message.
    """
    try:
        # Parse the JSON data from the request
        feedback_data = request.get_json()

        # Get path for storing feedback
        feedback_path = get_feedback_path(
            user=feedback_data["user"], timestamp=feedback_data["timestamp"]
        )

        # Map numeric choice to text representation
        map_dict = {
            0: "a",
            1: "b",
            -1: "neither",
            100: "both",
        }
        chosen = map_dict[feedback_data["choice"]]
        comment = feedback_data["text"]

        # Create feedback dictionary and save it
        feedback_fname = os.path.join(feedback_path, "feedback.json")
        feedback_dict = {
            "chosen": chosen,
            "comment": comment,
            "timestamp": feedback_data["timestamp"],
            "question": feedback_data["question"],
        }
        save_json(feedback_fname, feedback_dict)
        print(feedback_dict)
        print("Saved in", feedback_fname)

        # Return a success response
        return jsonify(
            {"status": "success", "message": "Feedback submitted successfully!"}
        )

    except Exception as e:
        # Handle any errors that occur
        print("Error:", e)
        return (
            jsonify({"status": "error", "message": "Failed to submit feedback."}),
            500,
        )


@app.route("/eval_get_insight_cards", methods=["POST"])
def eval_get_insight_cards():
    """
    Generate insight cards for evaluation by comparing outputs from two models.

    Returns:
        JSON: Data containing insight cards and metadata
    """
    response = request.get_json()
    task = np.random.choice(list(tasks.keys()))
    data = {"user": response["user"]}

    # Get image predictions for both models
    model_1_images = get_image_preds(args.model_1_preds, task)
    model_2_images = get_image_preds(args.model_2_preds, task)

    # Select random index and randomly assign models to A/B positions
    ind = np.random.choice(len(model_1_images))
    if np.random.rand() > 0.5:
        model_a = model_1_images[ind]
        model_b = model_2_images[ind]
    else:
        model_a = model_2_images[ind]
        model_b = model_1_images[ind]

    # Render templates for both models
    card = "text_image_card.html"
    data["insight_card_a"] = render_template(
        card,
        model_output=model_a,
        id="A",
    )
    data["insight_card_b"] = render_template(
        card,
        model_output=model_b,
        id="B",
    )

    # Add metadata
    data["task"] = task
    data["timestamp"] = str(time.time()).replace(".", "_")
    data["criterion"] = tasks.get(task, "No criterion found for this task")

    # Save model data
    feedback_path = get_feedback_path(user=data["user"], timestamp=data["timestamp"])
    save_json(os.path.join(feedback_path, "meta.json"), {"task": task})
    save_json(os.path.join(feedback_path, "model_a.json"), model_a)
    save_json(os.path.join(feedback_path, "model_b.json"), model_b)
    print("saved in", feedback_path)

    return jsonify(data)


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    # Parse command line arguments
    import argparse

    parser = argparse.ArgumentParser(description="Model evaluation server")
    parser.add_argument(
        "-p", "--port", type=int, default=7883, help="Port to run the server on"
    )
    parser.add_argument(
        "-m1",
        "--model_1_preds",
        type=str,
        default="static/data/sample_model_a",
        help="Path to model 1 predictions",
    )
    parser.add_argument(
        "-m2",
        "--model_2_preds",
        type=str,
        default="static/data/sample_model_b",
        help="Path to model 2 predictions",
    )
    parser.add_argument(
        "-t",
        "--tasks",
        type=str,
        default="static/data/sample_tasks.json",
        help="Path to tasks definition file",
    )

    args = parser.parse_args()

    # Validate paths
    assert os.path.exists(
        args.model_1_preds
    ), f"Model 1 predictions path does not exist: {args.model_1_preds}"
    assert os.path.exists(
        args.model_2_preds
    ), f"Model 2 predictions path does not exist: {args.model_2_preds}"
    assert os.path.exists(args.tasks), f"Tasks file does not exist: {args.tasks}"

    # Load tasks
    with open(args.tasks) as f:
        tasks = json.load(f)

    # Start the Flask application
    app.run(debug=True, port=args.port, host="0.0.0.0", use_reloader=False)
