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
        'Bag',
        'Flyer',
        'Brochure',
        'Receipt',
        'Paper bag',
        'Paper packaging',
        'Wrapping paper',
        'Printer paper',
        'Origami',
        'Cardstock',
        'Sticky notes',
        'Poster',
        'Paperboard',
        'Diary',
        'Notepad',
        'Blueprint',
        'Paper napkin',
        'Construction paper',
        'Notebook paper',
        'Calendar',
        'Notebook cover',
        'Paper tray',
        'Invitation card',
        'Greeting card',
        'Ticket',
        'Playing card',
        'Business card',
        'Paper roll',
        'Certificate',
        'Card paper',
        'Broadsheet',
        'Manila paper',
        'Sheet music',
        'Report',
        'Binder paper',
        'Graph paper',
        'Legal pad'
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
        'Bagged packaged goods',
        'Plastic wrap',
        'Cling film',
        'PVC',
        'Acrylic',
        'Polystyrene',
        'Nylon',
        'PET',
        'Polypropylene',
        'Polythene',
        'Shrink wrap',
        'Disposable cup',
        'Disposable cutlery',
        'Plastic cap',
        'Plastic lid',
        'Plastic straw',
        'Packaging film',
        'Blister pack',
        'Plastic pouch',
        'Plastic tube',
        'Plastic utensil',
        'Plastic sheeting',
        'Plastic baggie',
        'Water bottle cap',
        'Plastic bucket',
        'Plastic crate',
        'Plastic barrel',
        'Synthetic rubber',
        'Polyurethane',
        'Plastic handle',
        'Plastic mesh',
        'Plastic ring',
        'Plastic tie',
        'Plastic pellet',
        'Polycarbonate',
        'Plastic insulation',
        'Plastic molding',
        'Plastic clips',
        'Plastic tag',
        'Plastic cover',
        'Plastic rope',
        'Silicone',
        'Plastic canister',
        'Plastic jar',
        'Polyester resin'
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
        'Boxed packaged goods',
        'Folding carton',
        'Display box',
        'Cardboard tube',
        'Cardboard sheet',
        'Cardboard tray',
        'Cardboard divider',
        'Cardboard insert',
        'Cardboard roll',
        'Corrugated sheet',
        'Heavy-duty box'
    ],
    'Wood': [
        'Wood',
        'Wooden box',
        'Timber',
        'Plywood',
        'Pencil',
        'Wood chips',
        'Wood shavings',
        'Firewood',
        'Balsa wood',
        'Hardwood',
        'Softwood',
        'Lumber',
        'Wooden pallet',
        'Wooden crate',
        'Wooden furniture',
        'Bamboo',
        'Wooden utensil',
        'Cork'
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
        'Sportswear',
        'Denim',
        'Lace',
        'Velvet',
        'Leather',
        'Spandex',
        'Nylon fabric',
        'Fleece',
        'Woolen blanket',
        'Silk scarf',
        'Terrycloth',
        'Microfiber',
        'Polyurethane fabric',
        'Down jacket',
        'Jeans',
        'Hoodie'
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
        'Beverage',
        'Aluminium',
        'Steel',
        'Copper',
        'Brass',
        'Iron',
        'Stainless steel',
        'Metal sheet',
        'Metal rod',
        'Wire',
        'Metallic packaging',
        'Aerosol can',
        'Metal tube',
        'Metal lid',
        'Soda can',
        'Bottle cap',
        'Metal frame',
        'Metal tool',
        'Nails',
        'Screws',
        'Metal mesh'
    ]
}

def get_recyclable_categories(detected_objects):
    matching_categories = set()
    for category, terms in category_map.items():
        if any(obj in terms for obj in detected_objects):
            matching_categories.add(category)
    return list(matching_categories) if matching_categories else None

def get_best_fitting_category(image_path, detected_objects, matched_categories):
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
        return granular_analysis_to_resolve_tie(image_path, tied_categories)

    return best_category

def granular_analysis_to_resolve_tie(image_path, tied_categories):
    client = vision.ImageAnnotatorClient()

    try:
        with open(image_path, 'rb') as image_file:
            content = image_file.read()
        image = vision.Image(content=content)

        response = client.label_detection(image=image)
        labels = [label.description for label in response.label_annotations]

        if response.error.message:
            raise Exception(f'Error: {response.error.message}')

        # Count label matches for each tied category
        label_match_count = {category: 0 for category in tied_categories}
        for category in tied_categories:
            terms = category_map.get(category, [])
            label_match_count[category] = sum(1 for label in labels if label in terms)

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

    analysis_result = analyze_image(file_path)

    if isinstance(analysis_result, dict) and 'error' in analysis_result:
        return jsonify({'error': analysis_result['error']}), 400

    detected_objects = analysis_result

    if not detected_objects:
        return jsonify({'result': 'No', 'category': "No match", "items": []}), 200

    recyclable_categories = get_recyclable_categories(detected_objects)

    if recyclable_categories:
        best_category = get_best_fitting_category(file_path, detected_objects, recyclable_categories)
        if best_category:
            return jsonify({'result': 'Yes', 'category': best_category, "items": detected_objects}), 200

    return jsonify({'result': 'No', 'category': "No match", "items": detected_objects}), 200

if __name__ == '__main__':
    app.run(debug=True)