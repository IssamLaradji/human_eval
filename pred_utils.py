import os
import json


def get_image_preds(path, task):
    """
    Get image predictions for a specific task.

    Args:
        path (str): Path to the predictions directory
        task (str): Task name

    Returns:
        list: List of image prediction data
    """
    img_list = []
    for folder in os.listdir(path):
        folder_path = os.path.join(path, folder)
        image_input = os.path.join(folder_path, "image.png")
        with open(os.path.join(folder_path, f"{folder}.json")) as f:
            image_meta = json.load(f)

        image_output = os.path.join(folder_path, f"{task}.png")
        if not os.path.exists(image_output):
            continue

        img_list.append(
            {
                "path": path,
                "prompt": image_meta["user_input"]["content"],
                "image_input": image_input,
                "image_output": image_output,
            }
        )

    assert len(img_list) > 0, f"No images found in {path}"
    print("Found", len(img_list), "images")
    return img_list
