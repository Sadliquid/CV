import os, tempfile, json
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from google.cloud import vision

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'serviceAccountKey.json'

app = Flask(__name__)
CORS(app)

with open('category_map.json', 'r') as f:
    category_map = json.load(f)

def analyze_image(image_path):
    client = vision.ImageAnnotatorClient()

    try:
        with open(image_path, 'rb') as image_file:
            content = image_file.read()
        image = vision.Image(content=content)

        response = client.object_localization(image=image)
        objects = response.localized_object_annotations

        if response.error.message:
            raise Exception(f'Error: {response.error.message}')

        detected_objects = [obj.name for obj in objects]
        return detected_objects

    except Exception as e:
        return {'error': str(e)}

def get_recyclable_categories(detected_objects):
    matching_categories = set()
    for category, terms in category_map.items():
        if any(obj in terms for obj in detected_objects):
            matching_categories.add(category)
    return list(matching_categories) if matching_categories else None

def get_best_fitting_category(file_name, image_path, detected_objects, matched_categories):
    # Count matching items in each category
    category_match_count = {category: 0 for category in matched_categories}
    for category in matched_categories:
        terms = category_map.get(category, [])
        category_match_count[category] = sum(1 for obj in detected_objects if obj in terms)

    # Find the category with the highest match count
    best_category = max(category_match_count, key=category_match_count.get)
    highest_count = category_match_count[best_category]

    # Check for ties
    tied_categories = [cat for cat, count in category_match_count.items() if count == highest_count]

    if len(tied_categories) > 1:
        # Perform a more granular analysis using the Vision API
        return granular_analysis_to_resolve_tie(file_name, image_path, tied_categories)

    return best_category

def granular_analysis_to_resolve_tie(file_name, image_path, tied_categories):
    client = vision.ImageAnnotatorClient()

    try:
        with open(image_path, 'rb') as image_file:
            content = image_file.read()
        image = vision.Image(content=content)

        response = client.label_detection(image=image)
        labels = [label.description for label in response.label_annotations]

        if response.error.message:
            raise Exception(f'Error: {response.error.message}')

        # Count label matches for each tied category, with weighted terms for Paper
        label_match_count = {category: 0 for category in tied_categories}
        for category in tied_categories:
            terms = category_map.get(category, [])
            label_match_count[category] = sum(1 for label in labels if label in terms)

            # Add weights for certain labels indicative of Paper
            if "Natural material" in labels or "Brown" in labels:
                if category == "Paper":
                    label_match_count[category] += 1  # Increase weight for Paper

        with open("logs.txt", "a") as f:
            f.write(f"Detected labels for {file_name}: {{ {', '.join(f'\"{label}\"' for label in labels)} }}\n")
            f.write(f"Label match count for {file_name}: {label_match_count}\n")
            f.write("\n")

        # Return the category with the highest label match count
        best_category = max(label_match_count, key=label_match_count.get)
        return best_category if label_match_count[best_category] > 0 else None

    except Exception as e:
        return {'error': str(e)}

@app.route('/', methods=['GET'])
def getIndex():
    return render_template('index.html')

@app.route("/", methods=['POST'])
def postIndex():
    return '[POST] - API is ONLINE.'

@app.route('/upload', methods=['POST'])
def upload_image():
    if 'file' not in request.files or request.files['file'].filename == '':
        return jsonify({'error': 'No file uploaded'}), 400

    file = request.files['file']
    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        file.save(temp_file.name)
        file_path = temp_file.name
        file_name = file.filename

    analysis_result = analyze_image(file_path)

    if isinstance(analysis_result, dict) and 'error' in analysis_result:
        return jsonify({'error': analysis_result['error']}), 400

    detected_objects = analysis_result

    if not detected_objects:
        return jsonify({'result': 'No', 'category': "No match", "items": []}), 200

    recyclable_categories = get_recyclable_categories(detected_objects)

    if recyclable_categories:
        best_category = get_best_fitting_category(file_name, file_path, detected_objects, recyclable_categories)
        if best_category:
            return jsonify({'result': 'Yes', 'category': best_category, "items": detected_objects}), 200

    return jsonify({'result': 'No', 'category': "No match", "items": detected_objects}), 200

if __name__ == '__main__':
    app.run(debug=True)