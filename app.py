import os, tempfile
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from google.cloud import vision

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'serviceAccountKey.json'

app = Flask(__name__)
CORS(app)

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

# Training data
category_map = {
    'Paper': [
        'Paper',
        'Towel',
        'Newspaper',
        'Magazine',
        'Notebook',
        'Cards',
        'Envelope',
        'Tissue',
        'Book',
        'Bag'
    ],
    'Plastic': [
        'Plastic',
        'Box',
        'Bottle',
        'Container',
        'Cup',
        'Bag',
        'Tub',
        'Jug',
        'Cutlery',
        'Straws',
        'Trays',
        'Packaged goods',
        'Food packaging',
        'Bubble wrap',
        'Spoon',
        'Fork',
        'Tableware',
        'Drink',
        'Juice',
        'Soda',
        'Water',
        'Beverage',
        'Bottled and jarred packaged goods',
        'Bagged packaged goods'
    ],
    'Cardboard': [
        'Cardboard',
        'Corrugated cardboard',
        'Cardboard packaging',
        'Carton',
        'Packaged goods',
        'Cereal box',
        'Shipping box',
        'Box',
        'Moving boxes',
        'Gift box',
        'Boxboard',
        'Boxed packaged goods'
    ],
    'Wood': [
        'Wood',
        'Wooden box',
        'Timber',
        'Plywood',
        'Pencil'
    ],
    'Textile': [
        'Textile',
        'Top',
        'Towel',
        'Cloth',
        'Fabric',
        'Cotton',
        'Polyester',
        'Wool',
        'Satin',
        'Silk',
        'Rags',
        'Clothing',
        'Clothes',
        'Towels',
        'Bed linens',
        'Curtains',
        'Socks',
        'Hats',
        'Scarves',
        'Bedding',
        'Jackets',
        'Shorts',
        'Outerwear',
        'Hat',
        'Scarf',
        'Sweaters',
        'Shirts',
        'Pants',
        'Dresses',
        'Skirts',
        'Sleepwear',
        'Sportswear'
    ],
    'Metal': [
        'Metal',
        'Bottle',
        'Container',
        'Can',
        'Foil',
        'Spoon',
        'Fork',
        'Tableware',
        'Tin can',
        'Canned packaged goods',
        'Drink',
        'Juice',
        'Soda',
        'Water',
        'Beverage'
    ]
}

def get_recyclable_categories(detected_objects):
    matching_categories = set()
    for category, terms in category_map.items():
        if any(obj in terms for obj in detected_objects):
            matching_categories.add(category)
    return list(matching_categories) if matching_categories else None

def confirm_category_with_label_detection(image_path, initial_categories):
    client = vision.ImageAnnotatorClient()

    try:
        with open(image_path, 'rb') as image_file:
            content = image_file.read()
        image = vision.Image(content=content)

        response = client.label_detection(image=image)
        labels = [label.description for label in response.label_annotations]

        if response.error.message:
            raise Exception(f'Error: {response.error.message}')

        label_matches = {category: 0 for category in initial_categories}
        for category in initial_categories:
            terms = category_map.get(category, [])
            label_matches[category] = sum(1 for label in labels if label in terms)

        confirmed_category = max(label_matches, key=label_matches.get) if label_matches else None
        return confirmed_category if label_matches[confirmed_category] > 0 else None

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

    analysis_result = analyze_image(file_path)

    if isinstance(analysis_result, dict) and 'error' in analysis_result:
        return jsonify({'error': analysis_result['error']}), 400

    detected_objects = analysis_result

    if not detected_objects:
        return jsonify({'result': 'No', 'category': "No match", "items": []}), 200

    recyclable_categories = get_recyclable_categories(detected_objects)

    if recyclable_categories:
        # Execute label detection to confirm category if multiple categories are detected
        if len(recyclable_categories) > 1:
            confirmed_category = confirm_category_with_label_detection(file_path, recyclable_categories)
            if confirmed_category:
                return jsonify({'result': 'Yes', 'category': confirmed_category, "items": detected_objects}), 200

        return jsonify({'result': 'Yes', 'category': recyclable_categories, "items": detected_objects}), 200
    else:
        return jsonify({'result': 'No', 'category': "No match", "items": detected_objects}), 200

if __name__ == '__main__':
    app.run(debug=True)