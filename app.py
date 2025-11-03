from flask import Flask, request, render_template, session
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing import image
import numpy as np
import os
import base64

app = Flask(__name__)
app.secret_key = 'something-unique-and-secret'
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

model = load_model("tomato_disease_model.h5")
class_names = [
    'Tomato___Bacterial_spot',
    'Tomato___Early_blight',
    'Tomato___Healthy',
    'Tomato___Late_blight',
    'Tomato___Leaf_Mold',
    'Tomato___Septoria_leaf_spot',
    'Tomato___Spider_mites',
    'Tomato___Target_Spot',
    'Tomato___Tomato_Yellow_Leaf_Curl_Virus',
    'Tomato___Tomato_mosaic_virus'
]

recommendation_dict = {
    'Tomato___Bacterial_spot': [
        "Remove and destroy infected leaves.",
        "Apply copper-based fungicide.",
        "Rotate crops annually."
    ],
    'Tomato___Early_blight': [
        "Apply recommended fungicide.",
        "Water at soil, not leaves.",
        "Remove plant debris at end of the season."
    ],
    'Tomato___Healthy': [
        "No disease detected. Keep monitoring."
    ],
    # Extend with specific steps for all classes.
}
pesticide_list = [
    "Copper Oxychloride",
    "Mancozeb",
    "Chlorothalonil",
    "Neem Oil",
    "Imidacloprid"
]

def get_quality_trend(history):
    if not history:
        return 'N/A', 'bad'
    healthy = sum(1 for record in history if record['prediction'] == 'Tomato___Healthy')
    ratio = healthy / len(history)
    if ratio > 0.7:
        return "Good", 'good'
    elif ratio > 0.4:
        return "Needs Improvement", 'medium'
    else:
        return "Bad", 'bad'

@app.route('/', methods=['GET', 'POST'])
def index():
    if 'history' not in session:
        session['history'] = []
    prediction = None
    recommendations = []
    img_preview = None

    if request.method == 'POST':
        img_file = request.files['image']
        img_data = img_file.read()
        img_b64 = base64.b64encode(img_data).decode('utf-8')
        filename = img_file.filename
        img_path = os.path.join(UPLOAD_FOLDER, filename)
        with open(img_path, 'wb') as f:
            f.write(img_data)

        img = image.load_img(img_path, target_size=(128, 128))
        img_array = image.img_to_array(img) / 255.0
        img_array = np.expand_dims(img_array, axis=0)

        pred = model.predict(img_array)
        class_idx = np.argmax(pred)
        prediction = class_names[class_idx]
        recommendations = recommendation_dict.get(prediction, ["See an agronomist for tailored advice."])

        # Update session history
        history = session['history']
        history.append({
            "name": filename,
            "b64": img_b64,
            "prediction": prediction
        })
        session['history'] = history
        img_preview = img_b64
        os.remove(img_path)
    else:
        # On GET, show the most recent as preview
        if session['history']:
            img_preview = session['history'][-1]['b64']
            prediction = session['history'][-1]['prediction']
            recommendations = recommendation_dict.get(prediction, ["See an agronomist for tailored advice."])

    history = session.get('history', [])
    quality_status, quality_bar = get_quality_trend(history)
    return render_template(
        'index.html',
        prediction=prediction,
        recommendations=recommendations,
        img_preview=img_preview,
        history=history[-5:][::-1],  # Last 5, newest first
        quality_status=quality_status,
        quality_bar=quality_bar,
        pesticide_list=pesticide_list
    )

@app.route('/reset')
def reset():
    session['history'] = []
    return ('', 204)

if __name__ == '__main__':
    app.run(debug=True)
