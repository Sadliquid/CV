import os
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from google.cloud import vision

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'serviceAccountKey.json'

app = Flask(__name__)
CORS(app)

def analyze_image(image_path):
    client = vision.ImageAnnotatorClient()

    with open(image_path, 'rb') as image_file:
        content = image_file.read()
    image = vision.Image(content=content)

    response = client.object_localization(image=image)
    objects = response.localized_object_annotations

    detected_objects = [obj.name for obj in objects]

    if response.error.message:
        raise Exception(f'Error: {response.error.message}')

    return detected_objects

# Training data
category_map = {
    'Paper': [
        'Paper', 
        'Newspaper', 
        'Magazine', 
        'Notebook', 
        'Cards', 
        'Envelope', 
        'Tissue', 
        'Paper bag', 
        'Paper towel', 
        'Book',
        'Cardboard',
        "2D barcode",
        "Boxed packaged goods"
    ],
    'Plastic': [
        'Plastic', 
        'Plastic bottle', 
        'Bottle', 
        'Plastic container', 
        'Plastic cup', 
        'Plastic bag', 
        'Plastic wrap', 
        'Food packaging', 
        'Plastic tub', 
        'Plastic jug', 
        'Plastic cutlery', 
        'Plastic straws', 
        'Plastic trays', 
        'Bubble wrap'
    ],
    'Cardboard': [
        'Cardboard', 
        'Carton', 
        'Corrugated cardboard', 
        'Box', 
        'Cereal box', 
        'Pizza box (clean)', 
        'Shipping box', 
        'Toilet paper roll', 
        'Cardboard packaging', 
        'Egg carton', 
        'Shoe box', 
        'Moving boxes', 
        'Gift box', 
        'Cardboard tubes', 
        'Boxboard'
    ],
    'Wood': [
        'Wood', 
        'Timber', 
        'Wooden box', 
        'Wood scraps', 
        'Wood chips', 
        'Bamboo', 
        'Wooden stakes', 
        'Plywood'
    ],
    'Textile': [
        'Textile', 
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
        'Jackets'
    ],
    'Metal': [
        'Metal', 
        'Tin can', 
        'Aluminium can', 
        'Metal bottle', 
        'Metal container', 
        'Steel can', 
        'Aluminium foil', 
        'Metal scraps', 
        'Metal packaging',
        'Batteries', 
        'Metal pipes', 
        'Screws', 
        'Nuts',
        'Bolts',
    ]
}

def get_recyclable_category(detected_objects):
    for category, terms in category_map.items():
        if any(obj in terms for obj in detected_objects):
            return category
    return None

@app.route('/', methods=['GET'])
def getIndex():
    return render_template('index.html')

@app.route("/", methods=['POST'])
def postIndex():
    return '[POST] - API is ONLINE.'

@app.route('/upload', methods=['POST'])
def upload_image():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400

    file = request.files['file']
    file_path = f'/tmp/{file.filename}'
    file.save(file_path)

    detected_objects = analyze_image(file_path) # Get the detected objects in the image using Vision API

    if detected_objects == []:
        return jsonify({'result': 'No', 'category': "No match", "items": []}), 200

    recyclable_category = get_recyclable_category(detected_objects) # Simplify the dectected objects to a common category

    if recyclable_category:
        return jsonify({'result': 'Yes', 'category': recyclable_category, "items": detected_objects}), 200
    else:
        return jsonify({'result': 'No', 'category': "No match", "items": detected_objects}), 200

if __name__ == '__main__':
    app.run(debug=True)