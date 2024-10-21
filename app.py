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
        'Paper bag',
        'Paper towel',
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
        'Plastic box',
        'Plastic bottle',
        'Plastic container',
        'Plastic cup',
        'Plastic bag',
        'Plastic wrap',
        'Plastic tub',
        'Plastic jug',
        'Plastic cutlery',
        'Plastic straws',
        'Plastic trays',
        'Bottle',
        'Container',
        'Packaged goods',
        'Food packaging',
        'Bag',
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
        'Metal bottle',
        'Metal container',
        'Aluminium can',
        'Aluminium foil',
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
        return jsonify({'error': 'Bad image data or processing error', 'details': analysis_result['error']}), 400

    detected_objects = analysis_result

    if not detected_objects:
        return jsonify({'result': 'No', 'category': "No match", "items": []}), 200

    recyclable_categories = get_recyclable_categories(detected_objects)

    if recyclable_categories:
        return jsonify({'result': 'Yes', 'category': recyclable_categories, "items": detected_objects}), 200
    else:
        return jsonify({'result': 'No', 'category': "No match", "items": detected_objects}), 200

if __name__ == '__main__':
    app.run(debug=True)