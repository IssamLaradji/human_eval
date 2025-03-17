import sys, os
import glob

from flask import Flask, request, render_template, jsonify, session
import os, re
import json
import pandas as pd
import copy, time
import numpy as np


form_questions = {}
# Initialize the Flask application
app = Flask(__name__)
app.secret_key = "your_secret_key"
app.config["UPLOAD_FOLDER"] = "uploads"
app.config["JSON_FOLDER"] = "static/json"
app.config["OUTPUT_FOLDER"] = "static/outputs"
app.config["FEEDBACK_FOLDER"] = "feedback_cba"
app.config["RESULTS_FOLDER"] = "results"
app.config["STUDY_FOLDER"] = "static/human_study"
app.config["USERS_FOLDER"] = "static/users"
app.config["DATA_FOLDER"] = "static/datasets"


@app.route("/")
def index():
    """
    Render the index page.

    Returns:
        str: Rendered HTML for the index page.
    """
    return render_template(f"{args.starting_page}.html")


def save_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=4)


# MAIN FUNCTIONS
################


# EVAL FUNCTIONS
# --------------
def get_feedback_path(user, timestamp):
    user_folder = re.sub(r"\W", "_", user)
    feedback_path = os.path.join(args.output_folder, user_folder, timestamp)
    os.makedirs(feedback_path, exist_ok=True)
    return feedback_path


@app.route("/submit-feedback-compare", methods=["POST"])
def submit_feedback_compare():
    """
    Handle submission of feedback data.
    Returns:
        JSON response: Success or error message.
    """
    try:
        # Parse the JSON data from the request
        feedback_data = request.get_json()
        # replace all special characters with "_"
        feedback_path = get_feedback_path(
            user=feedback_data["user"], timestamp=feedback_data["timestamp"]
        )
        map_dict = {
            0: "a",
            1: "b",
            -1: "neither",
            100: "both",
        }
        chosen = map_dict[feedback_data["choice"]]
        comment = feedback_data["text"]
        feedback_fname = os.path.join(feedback_path, "feedback.json")
        feedback_dict = {
            "chosen": chosen,
            "comment": comment,
            "timestamp": feedback_data["timestamp"],
            "question": feedback_data["question"],
        }
        save_json(feedback_fname, feedback_dict)
        print(feedback_dict)
        print("Saved in ", feedback_fname)

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


@app.route("/main")
def main():
    """
    Render the main page.

    Returns:
        str: Rendered HTML for the main page.
    """
    return render_template("main.html")


# def load_predictions(path):
#     """
#     To be customized by user
#     """
#     import pandas as pd

#     df = pd.read_csv("static/datasets/llm_samples_E5_nq_train 2.csv")
#     pred_list = []
#     for i in range(len(df)):
#         pred_dict = df.iloc[i].to_dict()
#         pred_list.append(pred_dict)

#     # img_list = glob.glob(os.path.join(path, "*", "*.jpg"))
#     # img_list = [{"img_path": img} for img in img_list]
#     # assert len(img_list) > 0, f"No images found in {path}"

#     return pred_list


# @app.route("/eval_get_insight_cards", methods=["POST"])
# def eval_get_insight_cards():
#     """
#     Render the main page.

#     Returns:
#         str: Rendered HTML for the main page.
#     """
#     response = request.get_json()
#     data = {}

#     # get image predictions
#     model_1_preds = load_predictions(args.model_1_preds)
#     # model_2_preds = load_predictions(args.model_2_preds)

#     # get random index
#     ind = np.random.choice(len(model_1_preds))
#     model_a = model_1_preds[ind]
#     # # coin flip
#     # if np.random.rand() > 0.5:
#     #     model_a = model_1_preds[ind]
#     #     model_b = model_2_preds[ind]
#     # else:
#     #     model_a = model_2_preds[ind]
#     #     model_b = model_1_preds[ind]

#     # assert all exist
#     # model_a["instruction"] = model_a["instruction"].replace("\n", "<br>")
#     data["insight_card_a"] = render_template(
#         "fragments/output_card.html",
#         model_output=model_a,
#         id="A",
#     )

#     # data["insight_card_b"] = render_template(
#     #     "fragments/output_card.html",
#     #     model_output=model_b,
#     #     id="B",
#     # )

#     data["task"] = args.task_name
#     data["timestamp"] = str(time.time()).replace(".", "")

#     feedback_path = os.path.join(args.output_folder, data["timestamp"])
#     os.makedirs(feedback_path, exist_ok=True)

#     # save in json file
#     save_json(os.path.join(feedback_path, "model_a.json"), model_a)
#     # save_json(os.path.join(feedback_path, "model_b.json"), model_b)
#     # save_json(
#     #     os.path.join(feedback_path, "feedback.json"), {"choice": "", "comment": ""}
#     # )
#     print("saved in ", feedback_path)
#     return jsonify(data)


def load_json(path):
    with open(path, "r") as f:
        data = json.load(f)
    return data


def get_results(path="/mnt/home/projects/ai-bites/human_eval/"):
    import glob, os
    import json

    def load_json(path):
        with open(path, "r") as f:
            return json.load(f)

    # Initialize an empty list to hold the results
    all_results = []
    data = load_json(f"{path}static/datasets/fmds.json")
    # Use glob to find all relevant JSON files
    feedback_files = glob.glob(f"{path}results/fmds/*/*/feedback.json")
    print(f"found {len(feedback_files)}")
    # Loop through each feedback file and read corresponding model files
    for feedback_file in feedback_files:
        # Load feedback
        feedback = load_json(feedback_file)

        # Find corresponding model_a and model_b files
        base_path = feedback_file.rsplit("/", 1)[0]  # Get the base path

        model_a_file = os.path.join(base_path, "model_a.json")
        model_b_file = os.path.join(base_path, "model_b.json")

        # Check if model files exist
        if os.path.exists(model_a_file) and os.path.exists(model_b_file):
            model_a = load_json(model_a_file)
            model_b = load_json(model_b_file)

            # Assuming 'data' is your list of dictionaries and 'feedback' is the dictionary you're checking against
            question_to_find = model_a["question"]

            # Find the index of the dictionary in 'data' that has the same question
            index = next(
                (
                    i
                    for i, item in enumerate(data)
                    if item["question"] == question_to_find
                ),
                None,
            )

            # index will be the index of the matching dictionary or None if not found
            # print("Index of matching question:", index)
            assert index is not None

            # Add a new key to model_a and model_b based on the match
            if model_a["answer"] == data[index]["model1_answer"]:
                model_a["name"] = "model1_answer"
            elif model_a["answer"] == data[index]["model2_answer"]:
                model_a["name"] = "model2_answer"
            else:
                werwer

            if model_b["answer"] == data[index]["model2_answer"]:
                model_b["name"] = "model2_answer"
            elif model_b["answer"] == data[index]["model1_answer"]:
                model_b["name"] = "model1_answer"
            else:
                ewrwerw
            # print(feedback)

            if feedback["chosen"] == "b":
                selected_model_name = model_b["name"]
            elif feedback["chosen"] == "a":
                selected_model_name = model_a["name"]
            else:
                selected_model_name = feedback["chosen"]
            # were
            # Create a result dictionary
            result_dict = {
                "question": model_a["question"],
                # "chosen": feedback["chosen"],
                "chosen": selected_model_name,
                "model1_answer": data[index]["model1_answer"],
                "model2_answer": data[index]["model2_answer"],
            }
            all_results.append(result_dict)
    return all_results


def get_preds_fmds(path, task):
    """
    To be customized by user
    """
    existing = get_results(path="/mnt/home/projects/ai-bites/human_eval/")
    existing = pd.DataFrame(existing)
    existing_questions = set(existing["question"])

    # load json
    with open("static/datasets/fmds.json", "r") as f:
        results = json.load(f)

    results_diff = [
        result
        for result in results
        if result["model1_answer"] != result["model2_answer"]
    ]
    if np.random.rand() > 0.8:
        selected_results = results_diff
        selection_indicator = "results_diff"
    else:
        selected_results = results
        selection_indicator = "results"

    remaining_questions = list(
        set(result["question"] for result in results) - existing_questions
    )
    if len(remaining_questions) > 0:
        selected_results = [
            result
            for result in selected_results
            if result["question"] in remaining_questions
        ]
    print("remaining", len(remaining_questions))
    result = np.random.choice(selected_results)
    model_1_image = {
        "question": result["question"],
        "answer": result["model1_answer"],
        "model_id": "1",
        "wiki_pages": result["wiki_pages"],
    }
    model_2_image = {
        "question": result["question"],
        "answer": result["model2_answer"],
        "model_id": "2",
        "wiki_pages": result["wiki_pages"],
    }

    def format_wiki_links(wiki_pages):
        return "<br><br>".join(
            [
                f"- {page['title']}: <a href='{page['url']}'>{page['url']}</a>"
                for page in wiki_pages
            ]
        )

    model_1_image["wiki_pages"] = format_wiki_links(result["wiki_pages"])
    model_2_image["wiki_pages"] = format_wiki_links(result["wiki_pages"])
    print(selection_indicator)
    return model_1_image, model_2_image


@app.route("/eval_get_insight_cards", methods=["POST"])
def eval_get_insight_cards_bigdoc():
    """
    Render the main page.

    Returns:
        str: Rendered HTML for the main page.
    """
    response = request.get_json()
    task = np.random.choice(["Multimodal MultiHop Question Answering"])
    data = {"user": response["user"]}

    # task = "chart2summary"
    # get image predictions
    model_1_image, model_2_image = get_preds_fmds(args.model_1_preds, task)

    # get random index

    # coin flip
    if np.random.rand() > 0.5:
        model_a = model_1_image
        model_b = model_2_image
    else:
        model_a = model_2_image
        model_b = model_1_image

    # assert all exist

    card = "cards/text_image_card.html"

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

    data["task"] = task
    data["timestamp"] = str(time.time()).replace(".", "_")
    data["criterion"] = (
        "Evaluate based on which model has a better Answer. Use the Wikipedia links to look up the answer"
    )
    feedback_path = get_feedback_path(user=data["user"], timestamp=data["timestamp"])
    # save model a and be
    save_json(os.path.join(feedback_path, "meta.json"), {"task": task})
    save_json(os.path.join(feedback_path, "model_a.json"), model_a)
    save_json(os.path.join(feedback_path, "model_b.json"), model_b)
    print("saved in ", feedback_path)
    return jsonify(data)


if __name__ == "__main__":
    # create port args
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--port", type=int, default=7883)
    parser.add_argument("-s", "--starting_page", type=str, default="paired_output")
    parser.add_argument("-o", "--output_folder", type=str, default="results/fmds")
    parser.add_argument(
        "-m1",
        "--model_1_preds",
        type=str,
        default="static/datasets/phi3_bigdoc",
    )
    parser.add_argument(
        "-m2",
        "--model_2_preds",
        type=str,
        default="static/datasets/phi3_bigdoc",
    )

    # parser.add_argument(
    #     "-t",
    #     "--task",
    #     type=str,
    #     default="svg2image",
    # )

    args = parser.parse_args()

    app.run(debug=True, port=args.port, host="0.0.0.0", use_reloader=False)
