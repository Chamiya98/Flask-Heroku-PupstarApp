from __future__ import division, print_function
# coding=utf-8
import sys
import os
import glob
import re
from tkinter import Image
import cv2

import numpy as np
import tensorflow as tf
# Keras
from keras.applications.imagenet_utils import preprocess_input, decode_predictions
from keras.models import load_model
from keras.preprocessing import image

# Flask utils
from flask import Flask, redirect, url_for, request, render_template, Response, flash, jsonify
from werkzeug.utils import secure_filename

# from gevent.pywsgi import WSGIServer

# Define a flask app
app = Flask(__name__)

# Model saved with Keras model.save()
MODEL_PATH = 'dog_behaviors.h5'

# Load your trained model
model = load_model(MODEL_PATH)
model.make_predict_function()  # Necessary
# print('Model loaded. Start serving...')

# You can also use pretrained model from Keras
# Check https://keras.io/applications/
# from keras.applications.resnet50 import ResNet50
# model = ResNet50(weights='imagenet')
# model.save('')
print('Model loaded. Check http://127.0.0.1:5000/')


def get_prediction_probability_label(model, img_path, class_labels):
    img = tf.keras.utils.load_img(
        img_path, grayscale=False, color_mode='rgb', target_size=[224, 224],
        interpolation='nearest'
    )
    input_arr = tf.keras.preprocessing.image.img_to_array(img)
    input_arr = np.array([input_arr])  # Convert single image to a batch.
    input_arr = input_arr / 255
    pred_probs = model.predict(input_arr)[0]

    pred_class = np.argmax(pred_probs)
    pred_label = class_labels[pred_class]
    pred_prob = round(pred_probs[pred_class] * 100, 2)

    return (pred_label, pred_prob)


breeds_model_path = 'dog_behaviors.h5'
# breeds_image_path = ''
breeds_class_labels = [
    'Angry',
    'Happy',
    'Sad']

UPLOAD_FOLDER = 'static/uploads/'

app.secret_key = "secret key"
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/behavior', methods=['GET', 'POST'])
def upload():
    file = request.files['file']
    if file.filename == '':
        flash('No image selected for uploading')
        return Response(response="No Image Selected")
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        # print('upload_image filename: ' + filename)
        flash('Image successfully uploaded and displayed below')
        # return render_template('index.html', filename=filename)
        # f = open("", "r")
        breeds_image_path = './static/uploads/' + filename
        breed_pred_label, breed_pred_prob = get_prediction_probability_label(model, breeds_image_path,
                                                                             breeds_class_labels)
        # print(breed_pred_label + "Breed")
        # return (breed_pred_label, breed_pred_prob)
        result = "Mood is: " + breed_pred_label + "& Matching Probability is:" + str(breed_pred_prob)
        # return Response(response=result)
        # return Response(respons)
        return jsonify(
            message=result
        )
    else:
        flash('Allowed image types are - png, jpg, jpeg, gif')
        return redirect(request.url)


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)
    # app.run(debug=True)
