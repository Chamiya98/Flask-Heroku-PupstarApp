from __future__ import division, print_function

import base64
import glob
import os
import pickle
import random
import re
from datetime import datetime, date

import numpy as np
import pyodbc
import tensorflow as tf
# Flask utils
from flask import Flask, redirect, render_template, request, flash, jsonify
from gunicorn.config import User
from keras.models import load_model
from nltk import PorterStemmer
from sklearn.decomposition import NMF
from sklearn.feature_extraction.text import TfidfVectorizer

from textAnalysis import text_analysis

# Define a flask app
app = Flask(__name__)
APP_ROOT = os.path.dirname(os.path.abspath(__file__))
# Model saved with Keras model.save()
MODEL_PATH_breed = 'dog_breeds.h5'
MODEL_PATH_disease = 'dog_diseases.h5'
MODEL_PATH_behavior = 'dog_behaviors.h5'
MODEL_PATH = 'model.sav'
ModelPath2 = 'count_vectorizer.sav'
# Load your trained model
model_breed = load_model(MODEL_PATH_breed)
model_disease = load_model(MODEL_PATH_disease)
model_behavior = load_model(MODEL_PATH_behavior)
model_breed.make_predict_function()  # Necessary
model_disease.make_predict_function()
model_behavior.make_predict_function()
# print('Model loaded. Start serving...')re


print('Model loaded. Check http://127.0.0.1:5000/')


# Function for get current date
def date_picker():
    current_datetime = datetime.now()
    date = str(current_datetime.strftime("%Y-%m-%d"))
    return date


# Function for get current date
def date_picker_no_space():
    current_datetime = datetime.now()
    date = str(current_datetime.strftime("%Y%m%d"))
    return date


# Function for generate random number
def random_number():
    rand_no = str(random.randint(10000000, 99999999))
    return rand_no


# Function for generate random number
def random_number_with_date():
    date = date_picker_no_space()
    rand_no = random_number()
    new_rand_no = str(date) + str(rand_no)

    return new_rand_no


def db_connector():

    # cnxn = pyodbc.connect(
    #   'DRIVER={SQL Server};SERVER=34.143.213.182;DATABASE=dogcare;UID=sqlserver;PWD=dogcare123;Trusted_Connection=no')
    # return cnxn

    cnxn = pyodbc.connect(
        'DRIVER={/opt/microsoft/msodbcsql18/lib64/libmsodbcsql-18.1.so.1.1};SERVER=34.143.213.182;DATABASE=dogcare;UID=sqlserver;PWD=dogcare123;TrustServerCertificate=yes')

    return cnxn


cursor1 = db_connector().cursor()


# -----------------------WebsiteConnection---------------------------------------------
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/petcare")
def petcare_page():
    return render_template("/clinics/pet_care.html")

@app.route("/petcare_2")
def petcare_page():
    return render_template("/clinics/pet_care2.html")


# Route for add comment
@app.route('/add_comment', methods=['GET', 'POST'])
def add_comment():
    if request.method == "POST":

        name = request.form.get('name')
        email = request.form.get('email')
        comment = request.form.get('comment')
        clinic_id = request.form.get('id')

        print(name)

        comment_id = int(random_number())
        comment_type = 2  # Already set unknown

        if len(name) == 0 or len(email) == 0 or len(comment) == 0 or len(clinic_id) == 0:
            return jsonify({'error': "Fields are empty!"})

        else:

            sp = text_analysis.get_sentiment_analysis_prediction(str(comment))
            outputs = f'{text_analysis.labels[sp]}'

            if outputs == "Positive":
                comment_type = 1

            elif outputs == "Negative":
                comment_type = 0

            conn = db_connector()
            query = ''' INSERT INTO Comments (CommentID, Name, Email, ClinicID, Content, Type) VALUES (?, ?, ?, ?, ?, ?)'''
            values = (comment_id, str(name), str(email), int(clinic_id), str(comment), int(comment_type))

            cur = conn.cursor()
            cur.execute(query, values)
            conn.commit()
            result = cur.rowcount

            if result > 0:
                return jsonify({'success': "Comment added!"})

            else:
                return jsonify({'error': "Comment not added!"})

    return jsonify("Invalid")


@app.route("/clinic_images")
def clinic_images():
    images_list = []
    for file in glob.glob('static/images/images/team/*.jpg'):
        images_list.append(file)

    return jsonify(images_list)


@app.route('/login', methods=['GET', 'POST'], endpoint='login')
def Login():

    username1 = request.json['username']
    password1 = request.json['password']
    loggeduser = ""

    usr=[]
    print(username1, password1)

    if username1 == "" or password1 == "":
        loginresult = "Please_fill_the_all_fields_!"
    else:
        cursor1.execute("SELECT * FROM users WHERE username = ? AND password = ?",
                        (username1, password1))
        if cursor1.fetchone() is not None:
            loginresult = "Login_Succeeded"
            cursor1.execute("SELECT fullname FROM users WHERE username = ? AND password = ?",
                            (username1, password1))
            loggeduser = cursor1.fetchone()

            for row in loggeduser:
                usr.append([x for x in row])
        else:

            loginresult = "Login_Failed"



    print(loginresult)
    print(loggeduser)

    return jsonify(
        message=loginresult,
        user=usr
    )


@app.route('/signup', methods=['GET', 'POST'], endpoint='signup')
def Login():
    email = request.args.get('email')
    password = request.args.get('password')
    fullname = request.args.get('fullname')

    if email == "" or password == "" or fullname == "":
        loginresult = "Please fill the all fields !"
        queryResult = "Insertion Failed"
    else:
        conn = db_connector()
        query = ''' INSERT INTO users (username, password, fullname) VALUES (?, ?, ?)'''
        values = (email, password, fullname)

        cur = conn.cursor()
        cur.execute(query, values)
        conn.commit()
        loginresult = cur.rowcount
        queryResult = "Inserted"
        # result = cur.rowcount
    return jsonify(
        message=loginresult,
        qresult=queryResult
    )


@app.route('/getDoglist', methods=['GET', 'POST'], endpoint='dogList')
def dogList():
    dog_Array = []
    cursor1.execute("select Dogid, Full_Name from Dogs")

    testt = cursor1.fetchall()

    for row in testt:
        dog_Array.append([x for x in row])

    return jsonify(
        message=dog_Array
    )


@app.route('/insertbehaviorPastData', methods=['GET', 'POST'], endpoint='insterbehaviorpastdata')
def pastDataBehavior():

    #breedName = "Cindy"
    #behavior = "Angry"

    breedName = request.json['dogname']
    behavior = request.json['behavior']

    #rint(request.values)
    #print(breedName)
    #breedName = User.query.filter_by(breedName=request.form['dogname']).first()
    #behavior = User.query.filter_by(behavior=request.form['behavior']).first()

    print(breedName, behavior)
    if breedName == "" or behavior == "":
        loginresult = "No Name Found"
        queryResult = "Insertion Failed"
    else:

        today = date.today()
        print("Today's date:", today)
        cursor1.execute("select Dogid from Dogs where Full_Name= ?", (breedName))
        dogId = cursor1.fetchone()

        insertdogId = int(dogId[0])
        #dogId = int(dogId)
        print("DogId:", dogId)
        conn = db_connector()
        query = ''' INSERT INTO behaviorPastData (behavior, Date, dogId) VALUES (?, ?, ?)'''
        values = (behavior, today, insertdogId)

        cur = conn.cursor()
        cur.execute(query, values)
        conn.commit()
        loginresult = cur.rowcount
        queryResult = "Inserted"

    return jsonify(
        message=loginresult,
        insertRes=queryResult
    )

@app.route('/getcommentsforclinic', methods=['GET', 'POST'], endpoint='getcommentsforclinics')
def getcmntlist():

    #breedName = "Cindy"
    #behavior = "Angry"
    cmnts = []
    clinicId = request.json['id']

    print(clinicId)


    today = date.today()
    print("Today's date:", today)
    cursor1.execute("select * from Comments where ClinicID= ?", (clinicId))
    cmnt = cursor1.fetchall()

    for row in cmnt:
        cmnts.append([x for x in row])

    return jsonify(
        message=cmnts,
    )

@app.route('/getspecificclinicdata', methods=['GET', 'POST'], endpoint='getspecificclinicdatalist')
def getspecificclinicd():

    clinicdata = []
    clinicd = request.json['id']

    print(clinicd)
    cursor1.execute("select * from clinics where ClinicID= ?", (clinicd))
    cmnt = cursor1.fetchall()

    for row in cmnt:
        clinicdata.append([x for x in row])

    return jsonify(
        message=clinicdata,
    )

@app.route('/insertdiseasePastData', methods=['GET', 'POST'], endpoint='insterdiseasepastdata')
def pastDataBehavior():

    #breedName = "Cindy"
    #behavior = "Angry"

    breedName = request.json['dogname']
    behavior = request.json['disease']

    #rint(request.values)
    #print(breedName)
    #breedName = User.query.filter_by(breedName=request.form['dogname']).first()
    #behavior = User.query.filter_by(behavior=request.form['behavior']).first()

    print(breedName, behavior)
    if breedName == "" or behavior == "":
        loginresult = "No Name Found"
        queryResult = "Insertion Failed"
    else:

        today = date.today()
        print("Today's date:", today)
        cursor1.execute("select Dogid from Dogs where Full_Name= ?", (breedName))
        dogId = cursor1.fetchone()

        insertdogId = int(dogId[0])
        #dogId = int(dogId)
        print("DogId:", dogId)
        conn = db_connector()
        query = ''' INSERT INTO diseasePastData (disease, Date, dogId) VALUES (?, ?, ?)'''
        values = (behavior, today, insertdogId)

        cur = conn.cursor()
        cur.execute(query, values)
        conn.commit()
        loginresult = cur.rowcount
        queryResult = "Inserted"

    return jsonify(
        message=loginresult,
        insertRes=queryResult
    )

def get_prediction_probability_label(model, img_path, class_labels):
    img1 = tf.keras.utils.load_img(
        img_path, grayscale=False, color_mode='rgb', target_size=[224, 224],
        interpolation='nearest'
    )
    input_arr = tf.keras.preprocessing.image.img_to_array(img1)
    input_arr = np.array([input_arr])  # Convert single image to a batch.
    input_arr = input_arr / 255
    pred_probs = model.predict(input_arr)[0]

    pred_class = np.argmax(pred_probs)
    pred_label = class_labels[pred_class]
    pred_prob = round(pred_probs[pred_class] * 100, 2)

    return pred_label, pred_prob


breeds_model_path = 'dog_breeds.h5'
# breeds_image_path = ''
breeds_class_labels = [
    'German shepherd',
    'Labrador retriever',
    'Golden retriever',
    'Rottweiler']

UPLOAD_FOLDER = 'static/uploads/'

app.secret_key = "secret key"
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# -------------------Breed app --------------------------------------------------------

@app.route('/breedmain', methods=['GET', 'POST'], endpoint='breed')
def upload():
    if request.method == "POST":

        id = random_number_with_date()
        image = request.json['file']

        if image == None:
            return jsonify({'error': "Image not uploaded"})

        else:

            uploaded_img_path = APP_ROOT + '/static/uploads/breed/'

            if not os.path.exists(uploaded_img_path):
                os.makedirs(uploaded_img_path)

            filename = str(id) + "_breed.png"
            # filename = secure_filename(image.filename)

            img_url = uploaded_img_path + filename
            with open(img_url, "wb") as fh:
                fh.write(base64.b64decode(image))

        breed_pred_label, breed_pred_prob = get_prediction_probability_label(model_breed, img_url,
                                                                             breeds_class_labels)
        # print(breed_pred_label + "Breed")
        # return (breed_pred_label, breed_pred_prob)
        result = breed_pred_label + "& Matching Probability is:" + str(breed_pred_prob)
        # return Response(response=result)
        # return Response(respons)
        return jsonify(
            message=result
        )
    else:
        flash('Allowed image types are - png, jpg, jpeg, gif')
        return redirect(request.url)


@app.route('/save_dog_details', methods=['GET', 'POST'], endpoint='save_dog_details')
def save_dog_details():
    if request.method == "POST":

        id = random_number_with_date()
        image = request.json['file']
        detected_breed = request.json['detected_breed']
        full_name = request.json['full_name']
        weight = request.json['weight']
        gender = request.json['gender']
        pet_type = request.json['pet_type']
        dob = request.json['dob']
        user_email = request.json['user_email']

        if (image == None or len(detected_breed) == 0 or len(full_name) == 0 or len(weight) == 0
            or len(gender) == 0 or len(pet_type) == 0 or len(dob) == 0 or len(user_email) == 0):
            return jsonify({'error': "Image not uploaded/Fill details"})

        else:

            uploaded_img_path = APP_ROOT + '/static/uploads/breed/detected/'

            if not os.path.exists(uploaded_img_path):
                os.makedirs(uploaded_img_path)

            filename = str(id) + "_breed.png"
            # filename = secure_filename(image.filename)

            img_url = uploaded_img_path + filename
            with open(img_url, "wb") as fh:
                fh.write(base64.b64decode(image))

            conn = db_connector()
            query = ''' INSERT INTO Dogs (Full_Name, Breed, Weight, Gender, Species, DOB, UserEmail, ImageName) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)'''
            values = (str(full_name), str(detected_breed), str(weight), str(gender), str(pet_type), str(dob), str(user_email), str(filename))

            cur = conn.cursor()
            cur.execute(query, values)
            conn.commit()
            result = cur.rowcount

            if result > 0:
                return jsonify({"status": "success", 'message': "Dog details added!"})

            else:
                return jsonify({"status": "error", 'message': "Dog details not added!"})

        # breed_pred_label, breed_pred_prob = get_prediction_probability_label(model_breed, img_url,
        #                                                                      breeds_class_labels)
        # print(breed_pred_label + "Breed")
        # return (breed_pred_label, breed_pred_prob)
        # result = "Breed is: " + breed_pred_label + "& Matching Probability is:" + str(breed_pred_prob)
        # return Response(response=result)
        # return Response(respons)
        # return jsonify("message=result")
    else:
        flash('Allowed image types are - png, jpg, jpeg, gif')
        return redirect(request.url)


# -----------------------------Behaviour-------------------------------------------

def get_prediction_probability_label_behavior(model, img_path, class_labels):
    img = tf.keras.utils.load_img(
        img_path, grayscale=False, color_mode='rgb', target_size=[224, 224],
        interpolation='nearest'
    )
    input_arr = tf.keras.preprocessing.image.img_to_array(img)
    input_arr = np.array([input_arr])  # Convert single image to a batch.
    input_arr = input_arr / 255
    pred_probs = model.predict(input_arr)[0]

    pred_class = np.argmax(pred_probs)
    pred_label_behavior = class_labels[pred_class]
    pred_prob_behavior = round(pred_probs[pred_class] * 100, 2)

    return pred_label_behavior, pred_prob_behavior


behavior_model_path = 'dog_behaviors.h5'
# breeds_image_path = ''
behavior_class_labels = [
    'Angry',
    'Happy',
    'Sad']


@app.route('/behaviormain', methods=['GET', 'POST'], endpoint='behavior')
def upload():
    if request.method == "POST":

        id = random_number_with_date()
        image = request.json['file']

        if image == None:
            return jsonify({'error': "Image not uploaded"})

        else:

            uploaded_img_path = APP_ROOT + '/static/uploads/behavior/'

            if not os.path.exists(uploaded_img_path):
                os.makedirs(uploaded_img_path)

            filename = str(id) + "_breed.png"
            # filename = secure_filename(image.filename)

            img_url = uploaded_img_path + filename
            with open(img_url, "wb") as fh:
                fh.write(base64.b64decode(image))
        breed_pred_label, breed_pred_prob = get_prediction_probability_label_behavior(model_behavior,
                                                                                      img_url,
                                                                                      behavior_class_labels)
        # print(breed_pred_label + "Breed")
        result = "Mood is: " + breed_pred_label + "& Matching Probability is:" + str(breed_pred_prob)
        md = breed_pred_label

        return jsonify(
            message=result,
            mood=md
        )
    else:
        flash('Allowed image types are - png, jpg, jpeg, gif')
        return redirect(request.url)


# -----------------------------Disease-------------------------------------------

def get_prediction_probability_label_disease(model, img_path, class_labels):
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


disease_model_path = 'dog_diseases.h5'
# breeds_image_path = ''
disease_class_labels = [
    'Fungal & yeast infection',
    'ringworm',
    'shedding and hair loss (alopecia)',
    'skin tumors',
    'ticks']

disease_prescriptions = {
    'Fungal & yeast infection': (
        'Antifungal shampoo',
        'Ketoconazole cream',
        'Itraconazole 100mg capsules',
        'Mycoral cream'
    ),
    'ringworm': (
        'The most common way to treat ringworm in dogs is to use a combination of topical therapy (application of creams, ointments, or shampoos) and systemic therapy (administration of anti-fungal drugs by mouth) ',
        'In order for treatment to be successful, all environmental contamination must be eliminated.',
    ),
    'shedding and hair loss (alopecia)': (
        'Secondary bacterial infections are present, antibiotics may also be prescribed.',
        'Antifungal and Manage shampoo',
        'Rash powder',
        'Nilmange shampoo',
        'Labskin lotion ',
        'Ivermectin 10mg tablets',
        'Ivermectin injection'
    ),
    'skin tumors': (
        'Surgery is often the first step for some the tumors',
        'If the tumor cannot be removed in its entirety or if it has spread to nearby lymph nodes, radiation is commonly used',
        'By these methods\' tumors can be controlled nearly 70% of the time, though recurrence is common',
        'Chemotherapy is often used in combination with surgery and/or radiation therapy ',
        'There is also a vaccine that causes the dog\'s own immune system to attack tumor cells, which often successfully extends the survival time of dogs with oral tumors.'
    ),
    'ticks': (
        'Ticks and Flea shampoo',
        'Asuntol soap',
        'Bayticol EC spray',
        'Nexgrad tablets',
        'Detick solution ',
        'Antick solution',
        'Tikamit solution ',
        'Simperica tablets'
    )
}


@app.route('/disease', methods=['GET', 'POST'], endpoint='disease')
def upload():
    if request.method == "POST":

        id = random_number_with_date()
        image = request.json['file']

        if image == None:
            return jsonify({'error': "Image not uploaded"})

        else:

            uploaded_img_path = APP_ROOT + '/static/uploads/diseases/'

            if not os.path.exists(uploaded_img_path):
                os.makedirs(uploaded_img_path)

            filename = str(id) + "_breed.png"
            # filename = secure_filename(image.filename)

            img_url = uploaded_img_path + filename
            with open(img_url, "wb") as fh:
                fh.write(base64.b64decode(image))

        pred_label_disease, breed_pred_prob_disease = get_prediction_probability_label_disease(model_disease,
                                                                                               img_url,
                                                                                               disease_class_labels)
        # print(breed_pred_label + "Breed")
        # return (breed_pred_label, breed_pred_prob)
        result = "Disease is: " + pred_label_disease + "& Matching Probability is:" + str(breed_pred_prob_disease)
        outdisease = pred_label_disease
        medications = []
        for txt in disease_prescriptions[pred_label_disease]:
            medications.append(txt)
            print(txt)
        # return Response(response=result)
        # return Response(respons)
        return jsonify(
            Disease=result,
            medications=medications,
            outd=outdisease
        )
    else:
        flash('Allowed image types are - png, jpg, jpeg, gif')
        return redirect(request.url)


# -----------------------------Comment Analysis-------------------------------------------
stopwords = [
    'i',
    'me',
    'my',
    'myself',
    'we',
    'our',
    'ours',
    'ourselves',
    'you',
    "you're",
    "you've",
    "you'll",
    "you'd",
    'your',
    'yours',
    'yourself',
    'yourselves',
    'he',
    'him',
    'his',
    'himself',
    'she',
    "she's",
    'her',
    'hers',
    'herself',
    'it',
    "it's",
    'its',
    'itself',
    'they',
    'them',
    'their',
    'theirs',
    'themselves',
    'what',
    'which',
    'who',
    'whom',
    'this',
    'that',
    "that'll",
    'these',
    'those',
    'am',
    'is',
    'are',
    'was',
    'were',
    'be',
    'been',
    'being',
    'have',
    'has',
    'had',
    'having',
    'do',
    'does',
    'did',
    'doing',
    'a',
    'an',
    'the',
    'and',
    'but',
    'if',
    'or',
    'because',
    'as',
    'until',
    'while',
    'of',
    'at',
    'by',
    'for',
    'with',
    'about',
    'against',
    'between',
    'into',
    'through',
    'during',
    'before',
    'after',
    'above',
    'below',
    'to',
    'from',
    'up',
    'down',
    'in',
    'out',
    'on',
    'off',
    'over',
    'under',
    'again',
    'further',
    'then',
    'once',
    'here',
    'there',
    'when',
    'where',
    'why',
    'how',
    'all',
    'any',
    'both',
    'each',
    'few',
    'more',
    'most',
    'other',
    'some',
    'such',
    'no',
    'nor',
    'only',
    'own',
    'same',
    'so',
    'than',
    'too',
    'very',
    's',
    't',
    'can',
    'will',
    'just',
    'don',
    "don't",
    'should',
    "should've",
    'now',
    'd',
    'll',
    'm',
    'o',
    're',
    've',
    'y',
    'ain',
    'aren',
    "aren't",
    'couldn',
    "couldn't",
    'didn',
    "didn't",
    'doesn',
    "doesn't",
    'hadn',
    "hadn't",
    'hasn',
    "hasn't",
    'haven',
    "haven't",
    'isn',
    "isn't",
    'ma',
    'mightn',
    "mightn't",
    'mustn',
    "mustn't",
    'needn',
    "needn't",
    'shan',
    "shan't",
    'shouldn',
    "shouldn't",
    'wasn',
    "wasn't",
    'weren',
    "weren't",
    'won',
    "won't",
    'wouldn',
    "wouldn't"]

comments = ['"Best Vet Clinic in the area, from the front desk check in , to the doctor\'s visit to the check out !!!"',
            'Great people. they treat your pet like you do.Helped out a lot in taking care of my very sick rat terrier.shots for my pug mix painless for both of us',
            'Love the people the care and the availability',
            'The staff seems to really care about my dog.',
            'Always a stress free visit for both my dog and myself',
            'Professional And caring!!',
            'Overall positive experience for pet and pet parent! Excellent care from professional staff.',
            'Helps to go to a place I trust.',
            'Vets are very attentive and caring. They do not seem rushed but rather take time to sit with you for\n discussion. They are gentle with the pets. The environment is new and clean. \nThe staff and assistants are very friendly and patient.',
            'This place is ABSOLUTELY GARBAGE in terms of service and professionalism.',
            'This veterinarian place is are so much expensive the charge’s ,ho having pet as we was look same \nfamily member ,saddly get my dog fitz ,we bring to here coz why the place is near to us,emergency \ntime like that chrging for dog like this its not',
            'I called them and wanted to take my dog who is in quite a critical condition. The person who \nanswered the phone kept on telling me not to bring the dog because it was 6pm and they close at\n 7pm. He said that the the Dr can have a look at the …',
            'Pretty terrible place. Injected my cat with an antibiotic and she developed a large ulcer at the \nsite of injection. Right now she is struggling to heal. There is a descent chance that she might die \nbecause of this. Don’t take your animal there despite the ratings they have.',
            "No care for the Dog at all, solely money orientated, good place to go if you are rich and don't care \nfor the animals health.",
            "No humanity and terrible service, doctors don't seem to know what they are doing but will \nhappily give false …",
            'My pet dog died after two weeks of a surgery, the surgery was to remove her abdomen because \nit had gotten infected since I Was not given any antibiotic for healing the infection had gone \nfrom the blood flow to her Kidney. …',
            "Please don't take you dog here.They killed my 3 month old doberman puppy by charging 6000 rupees.\n Money is not a problem for me but my puppy's life was so important.",
            'Friendly and professional. No long waits.',
            'Very bad people. My kitten was seriously sick and when I called them they asked me from where \nI am and told me not to come because they wont take the people from our place. ',
            'The Vets are really good and they take such care to our pets. Highly recommend.',
            "I personally love this place, it's a very clean hospital for our pets and the doctors are very experienced\n and very caring.",
            'Very good hospital for pets Kind staff and qualified',
            'Friendly and knowledgeable staff.',
            "Don't ever  ever take your Pets here if you love them.",
            'I left my dog with them for a week at the pet v care boarding in Veluvana place. ',
            ' Never recommending this boarding place to anybody.',
            " I am not an expert in dogs health. I had a 3 year old golden retriever. took her to petvcare,\n she didn't eat for sometime and had a womb infection",
            "Please don't take your pet to this hospital if you really love and care your pet. They just want to earn \nmoney but they dont even know to diagnose the pet properly",
            'Worst service and Veterinarians were not qualified',
            'Please do not bring your animals to this PetsVcare Clinic. They all are fake and training doctors.\n They killed my 3 months old healthy puppy with their wrong injections for money.',
            'Good place, does vaccinations fast they pet shop above has all the things u need',
            'Poor patient care and absolute medical negligence !',
            'Highly recommended! They have all the facilities in town to take care of your pet! The doctors are \nvery kind too!',
            'My pet is always been taken care by some amazing and kind hearted doctors.',
            'Totally irresponsible vets . Diagnosed that my dog had an enlarged heart and a brain condition',
            'Service is good. Great place to do surgeries for you pet. Doctors and staff were very friendly and helful. ',
            'Really good caring for pets..and  kind , well trained staff.',
            'I had a bad experience with the pets V care animal boarding house at the veluwana place,\nit was very difficult to find the place since it has no signboard to that place as well no directions',
            'I m very upset with this hospital and i dont recommend it to anyone.Avoid it',
            'Wonderful place. Certainly recommend the drive up just to get the best treatment for my pup.',
            "I took my kitten he had a small injury and it was. Bleeding I took the kitten there n  the dctr didn't \nexplain wht injections there givingn they gave 4 injection n ceyline n took 1500/-  n i took it home n\n also the kitten is still In pain n still bleeding.",
            'Good vets and amazing helpers. Took great care of our dog and explained everything in detail',
            'Really great place. Their pharmacy is stocked well. The lead doctor sanjeevani is amazing at the care \ngiven.',
            'Dont ever take your pet to this horrible clinic.my pet dog died because of them.she was not properly \ndiagnosed by them.They didnt give her a single medicine except a saline',
            'The vets are so caring and take good care of the pets. Very kind and personal care given to the animals.',
            'Friendly staff and Doctors.',
            "If you want to kill your dogs with vets help that is the best place...My 3 dogs got killed there ....\nNasty place which kills your dog with the help of vets and their so called medicines ...\nthey do not give the reason for the dog's death ....PetsVcare Kurunegala change your board to petsVkill not care...",
            'Good Customer Service.Vetrenerarians are kind to pets.Also hospital open until 11 pm.\nThe hospital space is bit limited.',
            'Takes good care of your dog!! Highly recommend!!!',
            'happy with the service specially doctor who visit to my place was very helpful and friendly and the \nhelper also best person',
            'Great service and extended hours. Doctors treats pets with love.',
            'Really a nice place for animals i have ever seen. So much caring and kindness from staffs and doctors.',
            'Highly recommended! They have all the diagnostic systems and a good laboratory there as well.\nI take my pet there..',
            'More like PetsVDontCare. Paid a large sum for hospitalization with for dirty cages, complete \nneglect and rough handling of animals',
            'Good place for Pets.Not only dogs and cats.They are treating other pets like birds as well',
            'Very efficient and friendly Doctors and crew.',
            'No complaint ever.... so good with my little dog .',
            'Saved two of my pets! Highly recommend.',
            'Due to the negligence and misdiagnosis by the doctors, my dog died! \nThey should change their name to PETS V KILL!',
            'Mobile service not gd. Taking all day to come. & Minor staff doesn’t know how to talk to Pet owners',
            'unreasonable cost they paid for my dog...very very disappointed...never recommend anyone..',
            'worst place ever killed my kitten with mild illness',
            'Doctor is good with animals and knows his stuff. Place is a bit small though so there tends to be a \nsmall queue.',
            'Excellent Service',
            'Not recommend',
            'Highly not reliable!!',
            " don't recommend the male doctor. My dog got worse after the injection given by the male doctor.",
            'Reliability, Responsiveness',
            'Very good place. Value for money, convinient and friendly staff. Your pets will get the best care.',
            'Best vet care in the area.',
            'absolutely caring and excellent doctor.',
            'Doing like bigginers medical not good',
            'Really a kind doctor',
            'They provided a very good and and a  professional service. Can recommend for other pet lovers.',
            'They provide a good service. Everyone working there are very kind to animals and courteous.',
            "Their service is very poor. They really don't love animals and they treat animals just as objects \nwhich bring them money",
            'One of the best veterinary practice in the country',
            'Not a qualified doctor. Always just give 3 injections without properly diagnosing the animals. \nMy cat died even though he said it will be fine after weeks of treatment',
            'My dog died after being misdiagnosed by the doctor, we could have checked what was wrong given him\n the right medicine but the biggest mistake we did was trusting this doctor.',
            "Just a place of business! Money is all they care. They don't even know how to recognize the pet's \nproblem by its symptoms!",
            ' PLEASE DO NOT BRING YOUR PET TO THIS PLACE',
            'Not recommended. No matter what the issue is they just treat with 3 injections saying infection. \nPoor knowledge. Money oriented!',
            'They don’t even recognize the illness of my puppy where they carelessly given a wrong treatment \nwhich end up with death of my loving puppy',
            "Worst Experience ever the person here doesn't help animals who were treated from a different vet ",
            'IF YOU LOVE YOUR PET THEN DONT TAKE THEM HERE',
            'Good place for pet treatments.',
            'Highly recommend doctor.',
            'This is a best place to treat your pets, Doctors are very  carm, VERY CLEAN place, charges are also \nvery reasonable',
            'Hi viewers, i visited this place  really nice and clean , veterinarian who attend my pet really well\n experienced, at once he found the sickness and treated very well,',
            'Super my dog had good service and and they treated my dog as their dog',
            "this is a good place with good doctors and good service . they have card payments I took my cat to this\n doctor and its it's too good caring . expensive but it is very good .",
            'Good doctor, very kind calm and he knows to examin a pet well.. can garantee 100%',
            "Fast service and a good doctor. I personally recommend you take you're pets here if they require \nmedical attention.",
            'Very caring and friendly vetinarian. Reasonable charges and simple advice to follow',
            "Very good service and also open 24 hrs it's like a human hospital, very good",
            'A very nice and Friendly doctor. Good service.',
            'These vets are the worst.',
            'A kind, good service.i recommend',
            'Very bad poor service',
            'Excellent customer and pet care.',
            'Very happy to have my dog with this vet 😁',
            'Absolutely fantastic people and great professionals! ',
            'This place is ABSOLUTELY GARBAGE in terms of service and professionalism.',
            'the doctor was really nice! Very kind, and you could ask anything from them',
            'Although a good institution provides a kind service',
            'Very dedicated and loyal doctors. ',
            'Very good service experienced hands.. ',
            'Don’t take your animal there despite the ratings they have',
            'Cheers to the Entire Team Highly recommend.',
            'A good place for the animal. The doctor treats animals with full care.',
            'Very efficient doctor and support staff',
            "Good service. More Care about pet's",
            'Highly recommend this place.',
            'Best place for care ur pets Good and friendly doctors',
            'Excellent pet care hospital!',
            'The doctor and staff were really good.',
            "Not going here again and definitely don't recommend it.",
            'Great team.',
            'Really a great place with real caring doctors and staff....',
            'have very good experience with my dog at this hospital, highly recommended',
            'They dont have any respect to the poor animals in our area. Highly disappointed with them.',
            'I would highly recommend this hospital and these doctors.',
            'Friendly and professional. No long waits.',
            'The Vets are really good and they take such care to our pets. Highly recommend.',
            'One of the best and the most experienced animal hospitals in Sri Lanka.',
            'Very professional service given by the medical team to all the Pets.',
            'Very good hospital for pets Kind staff and qualified',
            'Friendly and knowledgeable staff.',
            "Don't ever ever take your Pets here if you love them.",
            'Never recommending this boarding place to anybody.',
            'Prices may be higher but your pet is in good hands. Friendly staff. Recommend.',
            'The clinic is very caring and accommodating from the vets to the reception team.',
            'The care given is excellent',
            'Great job. Highly recommend this place.',
            'Pet vet is hands down the worst place ever.',
            'They have a lot of in-house diagnostic and boarding facilities as well. Highly recommended!',
            'I wouldn’t recommend this place to anyone.',
            'To add to frustration they didn’t care at all and we had to forcefully get it done. Very unprofessional. I don’t know why people are talking highly about this place. Highly unreliable and unethical. Those who consider their pets as one of their  “family member” would understand my frustration.',
            "The worst ever boarding place for your poor pets.Don't ever board your pet here.They don't even give water to your poor fellow. ",
            'They had all the facilities our pet needed and the safeness they had was very good',
            'Provide very good service. Lot of attention given to annimals. Very helpfull doctors and staff.',
            'Good place to find all the essentials needed for your dog. Pets are cared with love and affection. Medical reports can be collected in one day.',
            'I took my Himalayan cat to this place twice and every time I go there his symptoms got worse than before. They injected four vaccines to my cat when I kept repeatedly saying that he has an allergy to vaccines.',
            'They have so many employees but no responsibility  they dont care animals just do medicines. Doctor also same. poor value . dont go there',
            "Not a wonderful place as their motto isn't ' A stitch in time saves nine'. Adamant in doing everything their way of treating animals with less consultation with the owner of the pet, thus the only concern is to increase costs beyond reasonable treatment.",
            'Killed my dog out of medical negligence. Misdiagnosed the disease, made us bring him there for a wrong course of treatments',
            "Unprofessional doctors. They want only money taking unwanted test and giving medicines. Please don't go to this place.",
            'Good staff here. I was there for an emergency for my dog and they were very quick and responsive. Great service!',
            'Great place with caring staff. They have more than 10 tables and enough staff to keep you from being in a queue. They even have laboratory, scanning facilities and mobile veterinary service. Highly recommended!',
            'They are too much expensive for street dogs service. I am very disappointed',
            'They are only focus on tests and money, not the animal.\nThe doctors are not clever and experienced enough to identity deceases and illness.',
            'They are doing treatment very kindly',
            'Very good service ,specially  staff very good .highly appreciated .',
            'Providing a good service. Highly recommend for all of your pet care needs',
            'Highly recommended place for your puppies to get their treatments.',
            'I would not recommend anyone to go to this place,My personal experience with them treating my pet was terrible and i know others who had bad experience as well',
            "Don't recommend  this place for grooming service",
            "This place is not good. Doctors  are not well trained.  My Dog's vaccine dose has changed and now my dog has cataracts. Please don't go to this place. They are taking only money.",
            'Extremely slow and poor service. They didn’t check on any of the pets who comes in, all they do is ignore until the pets are out of control',
            'Great place. They provide ambulance service. Good friendly staff.',
            "This useless place, they count only money, don't go there,",
            "Exactly a week ago I took my lovely kitty to this place since she was not feeling well. That was the first and last visit. They took an xray, then gave an injection, then gave us two pills and ask us to come back in 5 days.  They didn't mention anything about her condition is poor and feeling I got is things are fine. Unfortunately she passed away same night. Just few hours after visiting this horrible place.  I have sent them a message via their Website, Facebook page and finally email without any response.   Poor soul was lost due to medical negligence of this place. This is our horrible experience.",
            "Took good care of my cat. Now he's healthy and back with action. A wonderful and friendly place.\n",
            'good place. have good service.',
            'They are just considering about the money instead of saving pet. So many people have faced on bad experience there. Not recommended at all',
            'They take caring pets and very kindly',
            'The doctors are very helpful. This is a place with a operation theatre too. I would say this is the best animal hospital in the area. Frieny staff and so caring.',
            'The clinic is really nice, spacious and the environment is really good. The doctor is also a kind person. ',
            'Has a very friendly set of veterinarians, with a wide variety of services available for both cats and dogs.\nLike',
            "3 of my dogs died after going here , after asking around I found out that a lot of my friends dogs also died within 3 days of going here, plz don't take your dogs here,",
            'Well equipped experience doctors rate place that will take care of your pet',
            'One of the Best Animal care hospital in the area. Experienced, friendly and caring staff.\nLike',
            'skilled & kind staff.Modern facility with all the gear.Can count on to get the job done !',
            'Great place to get your pet attended to.',
            'Good and very professional place for the pet',
            'Not a good place at all!! They only need money! Don’t ever take ur pets to this place.',
            'The best care for dogs. Doctor is kind and helpful.',
            'very good service, they are well equipped and the staff is  friendly and helpful',
            'All vetenary services under one roof\nThey have all facilities and well experienced doctors',
            'Qualified doctors and enough space for parking ..Open most of the times',
            'They care pets like there own family',
            "It's really a hospital for animals with an operating theater for all types of surgeries,  and scanning.",
            'Poor service',
            'Good service for a very reasonable medical charges. Clean and neat vet clinic.',
            'Modern vet hospital for your pet. Have wide variety of facilities available. Treatment depends on the doctor who is doing the shift.Went there two times, two different doctors, two different charges for the same treatment',
            'High chargers, and couldn’t save the cat after treating it for more than 3 days, for the same treatment 2 different doctors take two different charges. And no use of treatment at all even though the charge is higher. We couldn’t save our pet',
            'Perfect Service. Friendly Doctor & Staff. Really carefully',
            'Its a very good pet hospital the veterinarian doctor treet very pet as there own',
            'Trust for pet care',
            'Recommend place to board your puppy safe and clean. Very kind staff.',
            "Please don't go to that damn hospital if you love your pet. #SHAME On These Money Minded People",
            'Very poor professionalism. As my dog was taken to this hospital for a fractured leg and ended up with a highly cost procedure with no proper results. Ultimately  we lost our dog due to post complications.Highly unsatisfied with their service. Please be mindful when your consulting them.\n',
            "Doctors are very carering. And has laboratory facilities for testing. Has a in-house boarding for animals if owners are leaving their houses for few days and don't want to keep their pets all alone in the house. Has a pet store as well.",
            'First place I have been to in Sri Lanka where they don’t just see their role as a source of income and instead show love towards our pets. Very happy with the service here.',
            'Very disappointed service. Caring only about money,',
            'Well equipped pet accessories shop and and a huge place that has all services you can imagine for a dog',
            "Service is good. We didn't wait much. Hope there's more option for pup food and other products for puppies' hygiene.",
            'Doctors are really attentive and took very good care of my pet. They are equipped with all the necessary services',
            'Well,many things to say about this place. This place is all about money. Very costly.They are poor in identifying the real sickness of your pet.',
            "DON'T GO THERE !!!!!  MONEY MONEY MONEY !!!!\nIf you want a dead pet and an empty pocket this is the place to go.",
            'ery reliable and a friendly place for your loved ones.',
            'Good facilities to board your Dogs when you go out of town.',
            'The best facilities for animal care I have seen in Sri Lanka ..',
            'Absolute torture of animals and worst animal hospital ever.  No empathy or kindness towards animals except by one or two people.',
            'Brilliant, up-to-date equipment and competent doctors!',
            'Provide excellent service for pets like dogs, cats, rabbits etc.. all kinds of facilities like medical care, pet items, foods and emergency medical services etc.. The service provided is superb.',
            'This place is only about money. I went there just to give deworming  which cost 200/- but they have charged 1250/- including opd charges of 850/- i dont know how they charged opd charges my kitten was not even sick. All the time we went for vaccine or something they do the same thing. Just for a vaccine we have to pay over 3000 bill every time. Every time They manage to make a unreasonable bill including various charges. Not recommended',
            'They are not professional at all',
            "No way to handle emergency cases and the cleanliness is zero outta 5.don't deserve even a single star",
            'They were extremely careless! As a result they killed my cat! My cat was in extreme pain when we brought it to the vet for scanning',
            "if you love your pets and don't want them to die please don't go here ever!",
            'One of the best veterinary surgeons we have ever met. He has the knack of diagnosing any problem very accurately and treating it accordingly. The place has enough space for several animals to be treated and to wait in line. We highly recommend him.',
            "The best veteran I have ever met... He's well knowledgeable, ability to identify & prescribe right medicines, very kind to animals",
            'I took my labrador to him for past years . He had a fluid retention problem and dr wanasinghe never tried to identify the underlying cause of his problem. Didnt take any test of my dog',
            'I took my cat with a breathing difficulty, there was a very young doctor and a grumpy old woman. They gave him 3 injections (without any tests) and saline. An hour later I lost my cat. The worst part is they refuse to tell me what medication they even gave. I suggest you to stay the hell away from this place..',
            'Very organized. Dr. Wanasinghe and the other lady doctor is amazing. Everyone is super friendly. Treated my dogs well. My go to vet',
            'This place is horrible, dont deserve 1 star even. The doctors are  not well experienced  specially Dr Wanashinge and Whenever you take your pet they give injections (random) without proper lab examinations/test. I do not recommend this place.',
            'Best pet care in the area.',
            'If you really care for your pets do not ever go to this place they are just killing animals.',
            "Last week one of my best friend's cat was sick and taken to this hopital for treatments. And the lady doctor who was available that time injected a wrong medicine and cat died yesterday after suffering a lot . One careless mistake all it took . I never recommend this place.",
            "The doctor here is very kind and knows what he's doing.\nCharges are average and the best is that they are open any day. Ask for Dr Wanasighe, better call before you go.",
            "I had great faith in Dr Wanasinghe that was until my Cocker Spaniel died because he was unable to diagnose her despite visiting with the same problem for 2 years. I used to beg him to scan her and he used to say no need nothing like that. That is when I decided to stop going there. I don't know what happened to him but he definitely has lost his touch with the animals and does not care anymore about them. Always in a hurry to get them out.",
            'Dr. Wanasinghe is the best vet we have ever taken our dogs to. He has a way with animals and his diagnosis has been spot on every time. Thank you Dr.',
            'A veterinary hospital where you can know that your pets are in good hands. Doctor Wanasinghe is truly supportive and gentle with the pets.',
            'Very caring and knowledgeable staff, especially the assistant, he was very patient and friendly. Dr Wannasinghe was very patient and explained what was wrong with our kolla (dog). Thank you!',
            'One of the best vets in the vicinity. The premises could do with a new coat of paint. Staff is kind and courteous. Call before your visit unless you like to hang around.',
            'Very kind and caring all staff for Animals also clients highly recommended place iam client from over 10 yrs',
            'Never go to this place if you really love your pet the doctors are really reckless and have expired medicines. i lost my dog because of their irresponsible  treatments.\n4',
            'Experienced and highly qualified doctors. One of the best veterinary hospitals in Sri Lanka. Staff is very kind and friendly.',
            "My friend's cat was sick and taken to this hopital for treatments. After that injected a wrong medicine and cat died yesterday. One careless mistake all it took . I never recommend this place.",
            'If you love the pet then think before you go to this place. Only money concern, no love or care for the pets..I lost all the faith on  Dr Wanasinghe & this place. I lost my Cat.',
            'Good place. Friendly staff and the doctor is friendly too. Went to treat my cat',
            "Very happy to take my pet here. Hospital's hospitality is very good and they are very kind to pets.",
            'Dr. Wanasinghe is very experienced doctor who loves and cares animals. This is an animal clinic and not a pet boarding place or hospital.',
            "Don't go to this place... this isn't a hospital. I lost my cat because of this place. If you love your pets don't even think to go to this place. Worst place ever....",
            'Excellent service by doctor & assistants.',
            "One of my friends cat got injected a wrong medicine and the poor soul had died.very careless.and do not recommend to anyone.I wouldn't even give one star.I gave it just to make this review and aware others.",
            'If you love your pets don’t go to this place,because they don’t know how to treat animals. So please think twice before you go there.',
            'I am warning you! do not go to this place.My dog was dead because of a wrong injection that recommended from this clinic.',
            'Nice place and doctor is very kind towards to the pets. Highly recommended.',
            'Run but just one doctor and a few helpers but the effort and care towards the pets is amazing! Very genuine and very thorough',
            'Dr. Wanasinghe is a well experienced Veterinarian who is so kind and caring towards your pets.',
            'Good place to treat your Pet',
            'Dr Wanasinghe is amazing and very patient. Handles all the animals with love and care. Definitely recommend.',
            'Our dog had parvo and so was so close to death but these people saved him in a few days.. Love the place.. Kind people and individual attention..',
            'Very irresponsible and careless. Do not visit this hospital for the sake of love for your pet..you’ll experience the worst service!',
            'Good spacious place.',
            'I will never recommend this place. I lost my puppy after The treatment of doctor.',
            "These people are so careless towards pets... Please don't even think to go to this place if you love your pets.",
            'Highly recommended',
            "Very poor service! Do not take your pets here!!! My cousin's cat was injected a wrong medicine and the poor soul is no more.",
            'Good doctors avaliable. Recommended for your pet.',
            'Well kind doctor.  Dr Wanasinghe knows what to do exactly.  Treating animal buddies so kindly.',
            'Do not go to this place. One of my friends cats died because of injecting a wrong medicine after going through hell.',
            'Very caring Doctor,  we are very happy with the service we received',
            'Very good veterinary clinic. The vets are very kind and helpful',
            'Worst place. Don’t try this place. They haven’t any responsibility about pets and medicines.',
            'Very good place for pet lovers',
            'dont go this place if you love your pet i lost my cat',
            'If you love your pets never ever go to this godforsaken place.',
            'Good clinic',
            'Very kind hospital for pets',
            'Probably the best veterinary centre in the area.',
            'All time favourite place',
            'Nice hospital and recommended for dogs.',
            'Nice place. Kind docters',
            'Can recommend to every one…',
            'Very good service.',
            'Helpfull and kind',
            'It was my first time at a veterinary clinic today to have a stray neighbourhood cat vaccinated and checked.',
            'Great service, Great Doctors & Supporting staff!!',
            'Very fast and efficient care, Doctors know what they are doing and pets seem to be very comfortable going there',
            'Highly recommended... They provide the best care for your loved pet... Very friendly staff.. Reliable... Reasonable prices...and the Pet taxi is an added bonus service as well...  The clinic is spacious and has a comforting environment..',
            'Very good staff and doctors. They  do care for your pet as you do. Keep up the good work.',
            'Nice place. Caring staff. Highly recommended!',
            'Very good care of pets, by vets and nurses who seem to really care about the animals.',
            'the doctor has no experience at all. our dog was taken with low fever and after the injection dose they gave, he got high fever and died in 2 days.',
            'This is highly recommended. Very competent and caring. My pup loves this place and the doctors.\n',
            "Please don't go to that damn hospital if you love your pet. #SHAME On These Money Minded People",
            'Very poor professionalism. As my dog was taken to this hospital for a fractured leg and ended up with a highly cost procedure with no proper results. Ultimately  we lost our dog due to post complications.Highly unsatisfied with their service. Please be mindful when your consulting them.',
            'Really unrealiable and staff that doesnt care about the pets or know what they are doing. They nearly killed my German that was in perfect health. So dont go there if you want your pet alive',
            "Left my 4 month old kitten for four days and he was mistrated, abadoned and traumatized. He was in the 'luxury' cage but there wasn't anything luxury about it. They haven't cleaned the cages, wasn't given the food which was promised and he was left traumatized for a couple of days afterwards. Wouldn't recommend at al",
            'Very disappointed service. Caring only about money,',
            'Great experience on my first visit with doggo. Got a FBC and other tests done in 20 mins and a proper consultation from Dr Eranda -based on the report.',
            "I'm disgusted with thsi hospital\nMy cats back legs were became swollen and he was unable to wlaj all of a sudden and he was crying loudly so as our ect was not available we took him here",
            'Doctors are really attentive and took very good care of my pet. They are equipped with all the necessary services.',
            'Very good place for your pets boarding needs. Friendly staff as always.',
            'Well,many things to say about this place. This place is all about money. Very costly.They are poor in identifying the real sickness of your pet. They recommended me to undergo a surgery for my pet which is not the correct decision at all.',
            "DON'T GO THERE !!!!!  MONEY MONEY MONEY !!!!",
            'Very reliable and a friendly place for your loved ones.',
            'Absolute torture of animals and worst animal hospital ever.  No empathy or kindness towards animals except by one or two people',
            'Brilliant, up-to-date equipment and competent doctors!',
            'They do a really lousy job and charge a premium which is twice the price of the other vet hospitals. ',
            ' Please do not take your pet to this place ever.',
            'This place is only about money. I went there just to give deworming  which cost 200/- but they have charged 1250/- including opd charges of 850/- i dont know how they charged opd charges my kitten was not even sick.',
            'Best hospital for the pets. Well experienced and friendly doctors and supporting staff. Excellent service. Highly recommended.',
            'I never recommend this hospital to anyone and all the pet groups because this hospitals’ doctors and staff only money minded and very inhuman',
            'Was amazed by the facilities that were available there. They had facilities for blood testing, x ray, ultra sound scanning, Enabling proper diagnosis and treatment in a scientific manner.',
            'Best place to take your pet for their Veterinary care, never seen better staff and customer service, very friendly people and has everything your dog chould wish for',
            'Professional service with caring and friendly doctors. Reasonable prices. Value for money. Highly recommend.',
            'Poor service even the cost is really  higher than other places . They are not even friendly at all. Very bad service. I do not recommend this place.',
            'I have visited this place for nearly two years and I can highly recommend this place as very suitable for anybody looking for good veterinarians. All doctors (senior and junior) treat the pets with utmost care and attention. Very pleasant looking place with caring people. Thank you pet pals.',
            'Highly recommended. My cats have been coming here for more than two years for treatments and their shots and they get the right treatment every time and get cured. The doctor is very experienced. Cat handling and caring is excellent. Thank u pet pals. Keep it up!',
            'Highly recommended. My cats have been coming here for more than two years for treatments and their shots and they get the right treatment every time and get cured. The doctor is very experienced. Cat handling and caring is excellent. Thank u pet pals. Keep it up!',
            'This place is simply amazing. Staff here loves animals and treat them with utmost care and love. Most importantly their medication works.  Prices are reasonable. Only thing they can improve is parking.',
            "I called i said i was coming and they said they are open but i reached there and i couldn't find anyone …",
            'I was very pleased with the service I received for my dog.Thank you very much for saving my dog. And I really appreciated your wonderful service. Highly recommended.',
            "Thanks for saving my puppy's life. Dr wickramasinghe if I not mistaken he is a god doctor who saved my pup's life from tick fever. Because I had two pups and I pup got dided after giving an InjectInjection at Fauna veterinary hospital battaramulla. This is a very good place for pets. Thanks",
            'Excellent care given for the pet with good advise and follow up. Highly recommended.',
            'They do not know what they do. Avoid this place if your pet is in a critical condition.',
            'My dog suffering from thyroid problem and now he is recovering from it. Thank u pet pals for  visiting. Really happy with the service and highly recommended.',
            "Kind and caring doctors. My dog was cured in no time. Best vet i've been to. Recommend to all pet lovers",
            'Very good mobile visit service. Professional staff and very caring doctors. Highly reccomended.',
            'A place which feels normal breeds should not be treated well. Only an advertising and money making agenda. No true feelings for pets.',
            'love the way the doctors at pet pals treat my dog and they are providing a great service..\nThanks a lot pet pals',
            'One of the best pet hospital for my pets..thank you pet pals.',
            'Great service. Good place for all the animal lovers.',
            'Really friendly service, good caring staff.',
            "I've visiting him for last 20 years, best doctor for animals i have ever met.",
            'My queen Cat....may little cat ...has gone today..treatments did not work on her..',
            'Very good doctor.he can understand any situation looking at the pet.best doctor.',
            'Very disappointed with the service and will never recommend taking your dog for any emergencies due to the lack of care and basic decency.',
            'Highly recommended... They provide the best care for your loved pet... Very friendly staff.. Reliable... Reasonable prices...and the Pet taxi is an added bonus service as well...  The clinic is spacious and has a comforting environment..',
            'the doctor has no experience at all. our dog was taken with low fever and after the injection dose they gave, he got high fever and died in 2 days.',
            'Not a qualified doctor. Always just give 3 injections without properly diagnosing the animals. My cat died even though he said it will be fine after weeks of treatment',
            "But on the 3rd day my cat died, he was just 1year old, he had many more years ahead, I blame myself for taking my cat to this place, I should've known better.",
            "Just a place of business! Money is all they care. They don't even know how to recognize the pet's problem by its symptoms! ",
            "Just a place of business! Money is all they care. They don't even know how to recognize the pet's problem by its symptoms! ",
            'PLEASE KINDLY NOT TO VISIT THIS PLACE which took my loving puppy’s life away from me. They don’t even recognize the illness of my puppy where they carelessly given a wrong treatment which end up with death of my loving pupp',
            'Do not Visit this Clinic, He KILLS PETS.',
            "Worst Experience ever the person here doesn't help animals who were treated from a different vet sergeon",
            "I took my 2 month old puppy there the doctor who was there gave 3 injections and the worm treatment together I bought the puppy home within 5 minutes my puppy died. I was looking after my puppy like a baby u killed it. I tell everyone who take their pets there if u want to see ur pet alive pls don't take to this clinic.",
            'IF YOU LOVE YOUR PET THEN DONT TAKE THEM HERE',
            'Worst hospital ever.. I took my little puppy to this hospital.. he put some injections and my puppy died after some time.. poor service.',
            "What a fake Vet! Zero knowledge. Don't take your pet to this place.",
            "If you love your pet's life do not go there please.",
            'Super my dog had good service and and they treated my dog as their dog',
            'KR pet hospital mentions 24 hours service but I took my dog their yesterday early morning 4 am but place was closed we knocked the door rang the bell but no one responded and even didn’t answer the phone after all my dog died suffered with sick',
            'Good doctor, very kind calm and he knows to examin a pet well.. can garantee 100%',
            "Fast service and a good doctor. I personally recommend you take you're pets here if they require medical attention.",
            'Very caring and friendly vetinarian. Reasonable charges and simple advice to follow',
            'good care to your pet',
            "Very good service and also open 24 hrs it's like a human hospital, very good",
            'Good Dr. respons really well even at a emergency situation',
            'Very good and fast service by the doctor.\nRecommended',
            'These vets are the worst.',
            'Their phone numbers never work.',
            'A kind, good service.i recommend',
            'Very bad poor service',
            'One of the best vets in the town. Highly recommend this place!!! Very clean and friendly staff!!!',
            'They provided a very good and and a  professional service. Can recommend for other pet lovers.',
            'They provide a good service. Everyone working there are very kind to animals and courteous.\nSometimes they may get busy as there are lot of animals being brought in and they give good care. So please be patient with them if you have to wait for sometime!',
            'The doctors at Dr.pet hospital Saved my dogs life....so thank you',
            'This place was an excellent surgery + clinic when starting and gradually turned worse and I too experienced it in the time being',
            'The best Animal Hospital I ever know. Have a lot to write, but rather than reading mine, just go and see... how much they care about the animals with full of love! Very friendly staff. Keep maintaining your good job!',
            'Highly recommend this place .I brought my pet there for medical help and I’m very happy with the care and outcome of the treatments. They truly care about the animals and their overall health and recovery , Dr Nuwan and the staff are really friendly and knowledgeable. Thanks heaps to Dr Nuwan and all the staff very much .',
            "Their service is very poor. They really don't love animals and they treat animals just as objects which bring them money. And once things go wrong they give excuses but somehow charges money.i have personal experience with them. Do not recommend this place. Don't take your pets to them.This place is only money oriented",
            'Good place. Very kind doctors and staff. Very well attended in detail manner. I would recommend the place for anyone who loves pet.',
            'Best place for treating your pet\nDoctors and all other members are very kind',
            'Thank god for such places... It functions 24 hrs.. a life saver. Priced reasonable.. thank you',
            'I highly recommend this place. Dr. Nuwan and the team always provide a very professional and quality service which you cannot find in many other places. They are well equipped and qualified.',
            'The best place for your pets. Quick service. Do all kinds of surgery. Parking for 4 cars. But you can easily park by the road if the parking is full.\nThey have all the pet food and medicines.',
            "Don't even think about to go this place. All the Doctors are trainee and they don't know about the medicine. But the cost is very high",
            'Even prices are bit high, they provide great service. Home visit service is the best privilege I can pin point as a pet owner.',
            "I'm not sure about their veterinary knowledge which should be the most important thing. I lost my puppy due to a stroke. I was taking my 17 months old boxer to them for four days, they said it was a urine infection. I saw my puppy getting weaker everyday and told them which they didn't take seriously",
            'Great service for all the animals and good co-operative staff. The doctors and the staff is so kind and helpful. They treated my pet very well. I highly recommend this place for all animals. Thank you so much doctors and staff for taking care of my dog.',
            "Took my pet after a Cobra bite. Doctor there instantly put the blame on us bringing the pet very late. They were keen on giving vial after vial of anti venoms, very insensitive staff. My daughter had to tell them to check of the running fever. My pet died after few hours. The doctor vanished after that. I had to pocket out a exorbitant amount. The amount doesn't matter if the pet lived. They didn't even prepare my kids for this..they were hoping that my pet would get better. So dissapointed.",
            'Good place to treat your pet',
            'Highly recommended. The staff is very friendly and always prepared to help. Including the owner, Dr. Nuwan. They also have a pet boarding facility too.',
            "I contacted the number listed on 10/12/2020 because their board advertises mobile pet care services. My dog was with a swollen face and it was getting worse. I was told they could only visit the next day morning and to give a piriton for the time being. When contacted the next day morning I was told they will give me a call and come. However I am yet to hear from them at the time of writing (9.30pm on 11/12/2020). Any kind of communication would have been appreciated at times of panic so that I won't be waiting, depending on non-existent service",
            'Great Place to treat your PET. Friendly and fast service.',
            'Best vet hospital to take your pet. They have all the labs to take reports, they are very cleaned and A/C. There staff is very kind and helpful. They take care of the pet very well. Price is reasonable. They examine the pet very well and give the medications',
            'Worst pet hostpital. All are training doctors. Go here if you want you never want to see your pet again.',
            'Extremely disappointing service! Brought in an emergency case for xrays after calling and making sure Xray service is available.',
            "They're treating pets very well. Very kind people.\nHighly recommended",
            'Quick Service, Treated my Pet in few minutes , Good Team Work',
            'Excellent doctors. Your dog is secured with them. Just a suggestion......... The prices should be affordable to the customer.',
            'A really good place to treat your pet. Have surgery facilities and vets Treat the animals kindly. Can also buy pet food and other accessories to your pet.',
            'Owner veterinary has a very high attitude and never want to listen to full history of my pet. His staff vets also are lack of discipline',
            'Very professional  place.. all staff try hard to help you..',
            'Great place. They are very caring. They even pet your animals till they get treatments. One day my cat was sick and was waiting for the doctor. And another doctor was holding and her kissing her till head doctor came to attend. They really passionate about animals. Was able to save my kitties so many times. Highly recommend!',
            'worst place..\nTheir negligence killed my two innocent kittens. Please dont take your pets here.\nHighly dissapointed',
            'Very friendly and professional staff, love this place and how they treat to animals, also parking available and fully air conditioned. keep up all good work !! all the best !!',
            'Great service and very friendly staff makes Dr.Pet stands head and shoulders above the rest of the pet clinics. Great place to buy some quality pet products too.',
            'Worse places visited and my 3 years old chihuahua was going to die without proper treatment.  They are money suckers. They do not care for pets .do not visit this place again other than a small problem.',
            'Great Customer Service.. everything what a pet needs, its hear. This is what we need. There are so many other places too but this one is very much unique which makes it the best place for pets with no doubts. The people, the stuff that we see there, Everything seems on point and nice.',
            'A very good place for your pet. Well experienced doctors and crew',
            "Please don't go. They don't know how to do the treatments.  My dog died because their treatments. Worst doctor ever",
            'A loveable place for pets. Warm and caring staff. Most of the time crowded but you get a unique preferenece. Experienced doctors.',
            "My cat was limping and the doctor suggested nothing wrong after a X-Ray. She is still limping, If you can't diagnose something like that even after a X-Ray, You must be terrible at your job.",
            'Very kindly good  service',
            'Don’t go this place they don’t love animals and they need only money.',
            "I was in a hurry when my dog was in terrible shape.The doctors and the staff is very polite and friendly.\nVery good service and they're so kind…",
            'Great service and takes good care of pets.',
            "Don't bring your pet to there. Many people lost their pets due to poor examine.\n",
            'Great service and care for pets. Doctors available at all hours during service time. Open from 7am to 10pm in the evening.',
            'Good service and highly recommended.',
            'The staff was so kind and i had a good service.',
            'Superb service  & The Best Animal Clinic',
            'Real nice place to take your pet. They even perform surgeries. Very friendly staff who love pets and pretty good at their job. They do home visits too.',
            'Good place with kind and good care for your pets. I have many good experiences with stray animals.',
            "Can't approve so much.It seems to be a luxury place that charges a lot of money.",
            "Dr.nuwan is the worst person .He doesn't even care about animals ",
            'Worst place to take your beloved pets',
            'Very poor service...not recommend at all.',
            'A very helpful place. All the veterinarians are very keen about getting their patients up & about as soon as possible',
            'Not recommended no experienced doctors',
            'Busy place but good care for pets',
            'Very convenient, full day time available, newly renovated, OPD instant attention, more than 4 surgery desks available.',
            'I doubt their knowledge on medicine',
            "  i've seen how they diagnose. Which is very wrong. Be careful very careful  they do marketing well but diagnosis is questionable",
            'good service. it is very popular in the neighbourhood. In addition to the medical services can purchase pet food/ collars / leashes',
            'A good place for veterinary care. Staff is friendly, kind and knowledgeable. Highly recommended…',
            'Best veterinary hospital in kadawatha,Good service quality with all facilities!',
            'An awesome place with kind attention. Highly recommond',
            'Only place to treat your per with kindness.',
            'Price is too hight',
            'Disgusting service',
            'Very expensive',
            'Terrible service . Very irresponsibly treat pets. Cannot recommend at all',
            'they are less responsible for the lives of young children. If your puppies have problems, do not bring Dr.Pet.',
            "f you have love for an animal, don't bring it here. That's all there is to it.",
            'eterinarians who treat animals kindly. Their services are reasonably priced. …',
            'One of the best veterinary doctors in town. Dedicated and attention to detail. Highly recommend',
            'Knowledgeable doctor. Well stocked pet shop within the premises',
            'Excellent service and excellent doctor',
            'Highly not recommending to take your pet here. The wrong treatments to my dog ended up been dead.',
            'Been there for years and the best vet ever',
            "I have been taking my pets to her for the last 15 years. She's a kind and caring veterinarian.",
            "If you want your pet to survive don't even think of taking them to her. Her attitude is also not professional, her main focus is on money.",
            'Don’t even think of taking your pet to her if you love your furry friend! She was the one that killed my golden Retriever, she gave the wrong medicine and he died of toxicity.',
            'I came to this place. Honda service  thyenawa. Mage ballage rash eka ikmanin sanipa kale doctor. Thank you',
            "Very disappointed and she doesn't even know how to talk ",
            'The doctors and staff are very kind, friendly and talented..Love this place and highly recommended',
            "This doctor treated really good earlier but now all he need is money. He ( Dr. Chandrasiri)doesn't even speak properly with the guardian of the pet. So how does he treat correctly. I lost my best friend because  of this man. He knows about it ofcourse. He let her die. Don't ever take your pets to this man if you really love. He is a dog killer !!!.",
            'Amazing experience they are treating my cat so well',
            "DOG KILLER. NEVER EVER COME HERE.\nAll Hype in his treatment but lack of insight.\nHis treatments are highly costly but can't treat extreme cases like a tick fever.",
            'Great care, and a Greater staff!',
            'This place doesn’t even deserve one star. 3 animals, including one of my own suffered from this place. DO NOT GO HERE whatsoever!! WORST WORST vet.',
            'Friendly doctor',
            "\nThis exactly is why you can't always trust reviews. I heard that this place was good but I got a bad doctor",
            'HATED IT',
            "Very experienced doctor and he's very patient and kind to all the animals and people who go to the clinic. His charges are very reasonable",
            'Do not take your pets here. Both doctors do not take any case serious. Pets will end up suffering and die',
            "Don't ever bring your pet here if you wish them to be alive",
            "This ignorant doctor knows only one injection which he uses on every animal he gets his hands with. And next day your pet dies. If you stay around couple of hours you can see how many pets he's killing.....",
            'Very good treatment doctor was very kind & well experience . I recommend',
            'best animal hospital ever.',
            'Doctors are very friendly and good care and service to the animals',
            'Well experienced Vets. Very reputed place.',
            'The worst pet care ever, Two men who knows nothing about animal care showed up.. they didn’t even want to check our cat.',
            'we regret for our ignorance trusting such services..this definitely is not the best care, they should call themselves the worst care…',
            'Again these people do not care about lives of animals they just care about the money.',
            'They do not care about the lives of pets but they value the money. ',
            'Really bad place! Don’t take your pet here',
            'This place just wants your money and not anything else.',
            " I don't think I can recommend such a place for anyone",
            'Worst place ever!!! These people take lives for granted.',
            'Customer service is really poor.',
            "They simply want your money. None of these people have a heart. They don't even take care of the pet properly. Please don't ever take your pet to this place.",
            'This place treats to various kind of pets. This animal hospital is really work hard. Staff has patience and also they are kind to the pets',
            'Please do not take your pets here',
            'They have no experienced staff. All are under training.',
            'The doctor is so disrespectful',
            'The services are as accordance with the name as it is. Can have the best care service for your pet. Truly deserves five stars.',
            "Never diagnoses the sicknesses properly, asks for medicine from the animals owners since they don't even have the most basic antibiotics LOL!!!",
            'Really good doctors, will handle pets in a excellent manner, in case of an emergency I always choose best care. Well recommended place!',
            'Typically a busy place. ',
            'These people dont love animals at all, on the very first day itself one of the nurses lifted my  cat ',
            'Very poor professionalism. As my dog was taken to this hospital for a fractured leg and ended up with a highly cost procedure with no proper results. Ultimately  we lost our dog due to post complications.Highly unsatisfied with their service. Please be mindful when your consulting them.',
            "Doctors are very carering. And has laboratory facilities for testing. Has a in-house boarding for animals if owners are leaving their houses for few days and don't want to keep their pets all alone in the house. Has a pet store as well.",
            'Took my German Sheperd for a simple procedure and they made a mistake with the medi that led to stomach ulcers',
            'Excellent service offered by all levels of staff from receptionist to assistants, nurses to doctors who are all absolutely kind hearted and caring treating pets with absolute care providing speedy swift professional service. ',
            'First place I have been to in Sri Lanka where they don’t just see their role as a source of income and instead show love towards our pets. Very happy with the service here.',
            'Very disappointed service. Caring only about money,',
            'Well equipped pet accessories shop and and a huge place that has all services you can imagine for a dog',
            'Great experience on my first visit with doggo. Got a FBC and other tests done in 20 mins and a proper consultation from Dr Eranda -based on the report.',
            'Professional service. Prompt attention provided to your pet from the moment you walk-in. Talented doctors and the staff is extremely friendly and helpful.',
            "Don't play with innconet lives u jerks I am very angry",
            'Very professional service, good care given to my pet by a vet, for reasonable prices! They have a shop available for dog food,shampoo, grooming items as well.',
            'Doctors are really attentive and took very good care of my pet. They are equipped with all the necessary services.',
            'Very good place for your pets boarding needs. Friendly staff as always.',
            '9 months ago\nWell,many things to say about this place. This place is all about money. Very costly.They are poor in identifying the real sickness of your pet',
            'If you want your pet to suffer, lose your money and finally lose your pet, then visit this place for sure.',
            "I dont know why these people are playing with innocent fellow's lives by knowing that they cannot speak even.I dont know how they eat with all these money by cheating on poor animal's lves.",
            'If you want a dead pet and an empty pocket this is the place to go.',
            "They may look like the most caring people but all they want is your MONEY. Doctors have no skill at all, 3 weeks in still couldn't diagnose correctly. They will make you come again and again just for your money.",
            'Very reliable and a friendly place for your loved ones.',
            'Good facilities to board your Dogs when you go out of town.',
            'Absolute torture of animals and worst animal hospital ever.',
            '  No empathy or kindness towards animals except by one or two people.',
            'They do a really lousy job and charge a premium which is twice the price of the other vet hospitals. When you criticize them or give them feedback regarding their poor service they blacklist customers.',
            'Please do not take your pet to this place ever.',
            'Rover is a wonderful place that treats animals going beyond mere business. The state of art facilities are excellent and highly conducive to animal comfort',
            'Best hospital for the pets. Well experienced and friendly doctors and supporting staff. Excellent service. Highly recommended.',
            'I never recommend this hospital to anyone and all the pet groups because this hospitals’ doctors and staff only money minded and very inhuman',
            'I would recommend this place to anyone who has a pet. ',
            'Best place to take your pet for their Veterinary care, never seen better staff and customer service, very friendly people and has everything your dog chould wish for.',
            'the damn doctors are not qualified. Stupid',
            "Pls we also love pets pls don't go to rover because they are good to take a huge amount of money only",
            'Good place to treat your pet',
            "It is the worst place for pets.....Ig you really love your pet....don't step on to that place for whatever the reason.",
            'Very glad to recommend Rover Vet hospital,to anyone looking for a dedicated, professional and caring service.',
            'Cleanest animal hostpital that I have ever visited. Comparing to best care their service is better and efficient and also cheap rates are available in rover.',
            'Exellent service place for your pet',
            'Friendly staff.. who knew how to handle my doggie.. Dr. Was really nice too',
            'Highly recommended place with director Dr finally find my dog sickness',
            'If you love your pet do not go there. They only care about money.',
            'Dont take your pet here, they care money only. Just money nothing else.',
            'Friendly staff and Dr Thilini was very helpful and gave us alot of information on how to look after our little girl.',
            'the worst place for pets , they need only money , they dont love animals at all , I dont reccomand this place',
            'This is the best private veterinary hospital',
            "Bad, experiance only after your money they will never care about your pet the way you do, please don't be fooled by their surface appearance as a high class highly caring place, I would never recommend this place to anyone.",
            'Unprofessional staff. Support staff had clipped my dogs nails- taking them off completely in one instance. Torturous to the animal. Avoid',
            'miss diagnosed one of my friends dogs and it passed away today. horrible service and mostly about money',
            "It's a very expensive place. ",
            "This hospital only care about money. This is too bad. Don't go there with your animal. U will realize soon.",
            'Fantastic service especially by Dr Eranda Rajapakse and his nursing team',
            "Place is clean with sufficient parking. From what I've seen, they have all necessary facilties to treat your pet.",
            'Very Impressed with the kind and helpful staff n vets I met when we took our red-eared-slider for a treatment.',
            "All depend on money don't go they only think about money not our pets",
            "Don't go. A place who think about money without thinking about life.",
            "Very sad. Don't recommend",
            'I heard a very sad story about this hostpital client .if you love your animal dont take him to this hell',
            'Amazing place and fantastic doctors to take care of your pets…',
            'It is extremely unhygienic!!!',
            'A good hospital filled with a bunch of vets who are energetic and kind towards pets.',
            'Avoid this place for the love of your pet. What horrible experience for a pet grooming.',
            'Very good veterinary service',
            'Great place for animals to be treated',
            'only money driven. Very expensive.  go only if you have extra amount of cash.',
            'It is a total rip off. Test after test for no reason.',
            'Very friendly staff. Very well equipped.',
            'Just a money focused business. No care on animals.',
            'Highly recommend for all the animals.',
            'Awesome service. Very friendly',
            'Animal killing place... never recommend this rude place',
            'Unnecessary billings based in money mater only',
            'The best veterinary care in Sri Lanka',
            'Well equipped with qualified and friendly vets',
            'Nice welcoming place. Good and friendly staff.',
            'Not recommend to anyone. only money driven place.',
            'Worst..only cares about money.',
            'Good health service and recommend',
            "DON'T GO THERE !!!!!  MONEY MONEY MONEY !!!!",
            'Not recommended',
            'This is not a suitable place to take your pet. Money greedy people without any concern.',
            'Such a bad place',
            'I have been to this place with couple of my pets ,a very good service and a caring vet. Highly recommended.',
            'Highly NOT recommend.',
            'Bonus is my dog is always happy to go back!',
            'Everyone we have spoken to has been so helpful and provided helpful guidance and reassurance.',
            'ZERO STARS.A horrible experience over the phone trying to get a sick guinea pig treatment. ',
            'Truly a special place for our beloved pets to be well looked after',
            'Very disappointed with this clinic.',
            'Excellent clinic! Efficient service and very friendly. Wonderful vet care!',
            'If you have a late night emergency, they will do everything they can to help. Highly recommended.',
            'I can highly recommend taking your pet to Fernlea at Kingswood, Bristol. They also have another practice at nearby Hanham.',
            'Brilliant, friendly family run vets',
            'Really lovely and reliable practice and we shall be returning soon for further treatments. ',
            'Excellent knowledge and friendly service.',
            'Thanks for Really good service from all the staff and very caring with my two cats today.',
            'Staff are so helpful and caring they go beyond to make sure your pet is ok.',
            'Lovely vets. Very supportive of cat rescues. Lovely people.',
            'Friendly staff, professional service and my dog always comes home happy and smelling great!',
            "I can't recommend these guys enough,",
            "Amazing staff! My dog is always happy when going and coming home. And by far the best groom he's ever had!",
            'Very disappointed with this kennel ',
            'Both my dogs come back from here happy and healthy, they really enjoy their home from home holiday',
            'Nasty, rude management.',
            'Always had good experiences with our dogs here.',
            'Best service as always, she always came back happy and well looked after',
            'Very good care of our 🐕 fantastic. Would definitely recommend',
            'Great Service as always & Rockie always happy to stay.',
            'Friendly staff will definitely use again',
            'Really rude staff. I wouldn’t recommend at all.',
            'Terrible experience - rude people',
            'Great place',
            'All the staff were brilliant my dog nearly died and due to their expertise they saved him',
            'Would 100% recommend.',
            'Train your staff properly and get more staff - discussing service!',
            'They really care for the pets they treat and their customer service is kind and sensitive.',
            'My cats have felt cared for, respected and in safe hands. ',
            'Unfriendly and poor service.',
            'Absolutely brilliant. ',
            'Dangerous and totally untrustworthy insurance money grabbers. Never leave your dog with them',
            'I have always had really good service and they treat my little dog with gentleness and love.',
            'Absolutely fantastic care of my cat when an emergency arose out of nowhere. ',
            'No vets are cheap but I have always had amazing care provided for my cats and would highly recommend.',
            'Fantastic veterinary practice.',
            'I would definitely recommend this vet hospital to everyone.',
            'Very happy with the service from all involved.',
            'Excellent veterinary practice always very helpful.',
            'Great veterinary surgery, with additional branches across the city.',
            'Superb service, I would happily recommend them based on what I experienced today.',
            'Fantastic practice. Truely dedicated in giving every pet the best possible care. ',
            'Able to establish positive working relationships with humans as well as animals.',
            'We have always felt our pets are in very good hands here and would recommend them to everyone!',
            'They are amazing, helpful, and really chilled out',
            'Thanks to the vets and nurses for minding him so well.',
            'Hand on heart the most dedicated, caring and professional team I have had the pleasure of dealing with. ',
            'Very nice atmosphere, prices very reasonable. Highly recommended',
            "The receptionist hasn't the most comforting of attitude but gives good advice",
            'Excellent service ,good advice , These vets will take the very best care for your pet .',
            'Super with advice attention and helpfulness . Recommend this service',
            'Their service and sincerity and true love of animals is unbelievably touching. ',
            'Great vets! I think they are honest, if they don’t think your pet needs to be seen - they will tell you.',
            'Always excellent treatment here. ',
            'All the staff I have encountered are friendly and really care about your animals.',
            'excellent care & great results as my dog made a speedy recovery - many thx',
            'Long wait and very expensive compared to other local vet. Sadly, even though close, will not go back',
            'Great service. Feel safe leaving our dog with them.',
            "Wouldn't help end my dogs life as I'm not a long term client!",
            'Would give 0 stars they don’t know what they are doing they uneducated',
            'Fantastic. Always know my animals are in fantastic hands with lovely and caring vets and nurses.',
            'Great vets really lovely helpful friendly staff',
            'Will not recommend this vet going forward. ',
            "Avoid them if you have another vet to go to. Don't expect them to ask about your pet and have concerns for their health after all.",
            'The accuracy of the diagnosis of a sick animal is 100%. ',
            'A very professional approach to the client. Very friendly service.',
            'Highly recommended this veterinary practice... ',
            'Best vets in this area in my opinion, friendly staff that keeps you updated about your pets.',
            'Absolutely disgusted!! ',
            'Very unprofessional and rude dealing with an upset customer.',
            'I think park veterinary is amazing they have always been very good when dealing with my dog 🐕',
            'The staff and vet were lovely people!',
            "Upto now they have been fantastic, can't fault them.",
            'will I attend these vets very very rude staff would not recommend this place',
            'I have since read an adequate level of reviews I am only sorry I did not do beforehand!',
            'Friendly staff you leave your pet with them while they assess them ring you for a consultation then collect pet and meds..',
            'I’d never use your service again & would suggest potential future clients to look elsewhere! ',
            'I will necever recommend...',
            'Reading all these bad reviews money orientated absolutely correct do not take your pets here.',
            'Absolutely brilliant caring vets took great care of my cats neutering and follow up appointments',
            'Great place! Welcoming, they take good care of your Pets. ',
            'Not a place I would ever take my pets again .I lost my dog due to dental work .',
            'All the care about is money not animals.',
            'The staff were extremely nice and were understanding of any problems I had ',
            'Very good super helpful and aftercare is well appreciated your pet is in safe hands 😀',
            'Someone, "put money minded" . I have to agree with them money first pet second. ',
            'Appalling service. Unprofessional and impersonal. Exorbitant prices. No accountability.',
            'We have nothing bad to say about this practice and would highly recommend them',
            'please take your beloved pet somewhere else.',
            'Im sick of them and am going to try somewhere else because I pay a fortune for nothing!!',
            'This is absolutely worst place to take your pet to.',
            'Very good service and friendly staff',
            'Took good care of my fur baby. Lovely staff.',
            'Quick & easy & efficient service at Park Vets.',
            'Very good vets who take very good care of your pets. ',
            'Dr. Suraj is the best Veterinarian Surgeon I have ever met.. Since he is a person with fondness for animals, he provides the best care for pet. Highly recommend his service..',
            'very kind doctor and great. our kitty was half dead. From one day our kitty got better and she is totally fine now thanks to Dr Suraj.',
            'One of the best pet care center near Piliyandala. Doctor is very friendly with the animals.',
            "Two of my kittens died after poor diagnosis. Good for basic check-ups. When u talk to certain doctors u know that they are confident of their work. Such confidence lacks here. Drugs are asked to be continued even though the animal doesn't respond to the medicine, & that, as happened with my kittens,  results in death.",
            'Please do not go to this place if you want to save your pets! Registered under a lady doctor’s name but her husband does the treatments ! Not sanitary ! Poorly cleaned and horrible service .so please there are more places out there go check from them but not here',
            "Please don't bring your pets here, especially if they need to be treated for vital injuries or illnesses",
            "This vet only cares about status and wealth and not about animals. Please don't make the same mistake as my family and be weary and bring your pet elsewhere.",
            'I am not satisfied with your service.',
            'The place have a very good service. Very professional and very clean',
            'Kind and friendly vets .treated my pets properly and handled them with care.overall its a good clinic.',
            'Went there to get my dog chipped the lady doctor who came out said she doesnt do it and her husband does it, but the clinic was open. Got me thinking if the doctor isnt capable of chipping a dog, how can they treat other diseases\n1',
            'Professional veterinarians with excellent knowledge in pet animal diseases and care.',
            'So expensive service..😐 u should think twice about it..👎 and need to pay much attention for the animal before treat..doctor if u read this,plz pay attention to the animals current situation not for the just only money👌',
            'The vet is very friendly and takes great care of your animal.',
            'quick service , you better find out the number and go that will make things easy',
            'Quick service, Not crowded and friendly environment.',
            'No parking space',
            "The doctor is always late. Today we came to get a scan done. We came at 5.15pm. it says that the doctor is available every day at 5.30pm . It's 6.40pm and still the doctor did not come. Very unprofessional.",
            'The Doctors are excellent,  I have been going Dr.Gunawardana for over 20 years, Dr. Dilani is fantastic too',
            'Best animal hospital in town. They provide services which is listed in the photograph below. There is plenty of space for parking also. They are even open on holidays. They managed to recover my dog who was bitten by a snake. So thankful for the staff and docs',
            "If you are really love your animal or pet please don't go to this place.",
            'These people are not professional.  ',
            'The doctor of this hospital is not a responsible person. Go to some other good hospital.',
            "Never on time . Any company that doesn't follow time should be rated low.despite what other qualities they preserve.wasted 1.5 hours with out  a doctor.",
            'The hospital did not attend to a very sickly animal for over 45 minutes and the animal eventually passed away. The vets are also extremely slow at their service and unprofessional. Would not recommend.\nLike',
            "The doctor is always bloody late !!! No respect whatsoever for his customers. It's not like we come for free treatment !",
            'Highly recommend. Doctors show genuine care for your pets. Mine always recover quickly. ',
            'Only regret I have is not finding this place earlier. All doctors are well experienced and prices are reasonable.',
            'Only regret I have is not finding this place earlier. All doctors are well experienced and prices are reasonable.',
            'Went for xray of our pet. Fast ,good service.',
            'Took my puppy there for her shots and they treated her with love and even thought hey were super busy, they were fast and efficient. I will definitely return.',
            'I have take treatment for my pets from this hospital.  It is duecare very well.',
            'Low standard vets. Not professional. Not trained. Have no scanning equipment.',
            'nable to examine a dogs PROM to diagnose leg pain. Advised me to drive 300km to a veterinary training university! Waste of time.',
            'Very Expensive prices for the service and medicines',
            "Do not go there. If you go there always check dog's medicine with other qulified veterinary",
            'I will Never recommend  to anyone  .',
            'My dog was half life when she was taken to this place. But this doctors seve her life with quick  diagnosis and medicine',
            'Best Place to take you pet.They are very caring about your Pet.\nWith all the facilities it is the best place that I have visited.',
            'Worst place ever . Please dont take your pet there',
            'Very good treatment and also very kindness one lady Doctor who cares so much our thanks specially to her, keep up your good work. Thank you.',
            "Visitors will loose their entire day due to negligence by the chief doctor's visiting time pattern",
            'Good service,main female vet was so nice staff is okey too',
            'Grate place for your pet and you. The doctors are very kind.',
            'Very kind staff and good service',
            'Very unprofessional. Will not make the mistake of visiting again.',
            'I think this is the best animal hospital in Sri lanka',
            "Good place to dog's",
            'I have no satisfaction with their services.',
            'Crowded place with no que system. Time waste and no advice from doctor. Just busy to see next.',
            'I have no satisfaction with their services.',
            'Not good',
            'Nice Vetranary treating place with qualified doctors Specially good for pets.',
            'A good place for those who care about their pets!!',
            'The service rendered by the vet surgeon is excellent!',
            'we’ve lost our 2 beloved pets because of their carelessness and wrong diagnosis . never ever recommend for anyone..',
            'Poor diogenes and negligence. I lost my 3 kittens because of their stupidity. Most of the time they priscribe medicine even without checking the animal propaly. If you love your pet please dont go to this hell hole.',
            "It's time we pet owners open up a separate fb page for all the dear pets that had died here in this facility. ",
            'The trainee doctors doesn’t have experience to identify threats levels, my Labrador just died, they did all the scans+xrays ++, but first aid was not there, asked to come after a week. A day after (today) he died. ',
            'Not the very best place if your pet get sick.',
            'I went there to show my cat who was very sick, they did not check her at all',
            "This is going to be long because I don't have a very good feelings about this place.",
            "I regret admitting my puppy to this hospital which resulted in my puppys' unnecessary and painful death. ",
            'A good diagnosis takes good care of your pet and prescribes medication',
            'A best caring place for animals..Doctors, nurses and all the staff were very kind and helpful.',
            'All service available for animal care. The best.',
            'Been here four hours now and still no one attending my pet. Disappointed and disgusted!',
            'They have every equipment but they are very slow. Expect to wait around 3 hours to get a shot. Seriously a very very long wait',
            "Service is useless. People who work there think it is their property. Don't waste your time here",
            'The staff always caring about pets and treat well.',
            'Do NOT recommend!',
            'Very slow treatments!',
            ' You can also purchase accessories and certain medications plus vitamins and shampoos for your pet at the clinic.',
            'friendly doctor,nice place, reasonable price, highly recommend ',
            'Highly recommended this place. We have  been taking our Cocker Spaniels to this place for more than 4 years and the service and treatment we have received is perfect.',
            'Attention to details of the vet surgeon Kapila is excellent',
            'Good service well trained friendly doctor',
            'Very clean and organized.',
            'Very friendly and knowledgeable. Dr Tuff was amazing and very caring towards our pet.   Thank you!',
            'Have always taken great care with our fur-kids. Staff are amazing, friendly and genuinely care about our pets!',
            'Great staff. Friendly, kind and genuinely concerned about you and your animals.',
            'No empathy whatever at the loss of our pet?',
            "heartless poor service!!! If it wasn't for the condition of our pet we would have driven to GFW or Clarenville.",
            "Mauled my rabbit and wouldn't stop when I told her to. My rabbit was freaking out and because she wouldn't take her hands off of her she went into shock and died",
            "Extremely high prices for less than good, rushed service. You're better off taking your pet elsewhere.",
            'The workers are very friendly, and your pet/pets are in good hands',
            'Very caring and friendly staff.',
            'Friendly staff, seem to genuinely care about customers and animals',
            'Great clinic. Amazing staff!',
            'Very helpful',
            'Excellent care by the Gander clinic. Thanks so much!',
            'Amazing staff and service',
            'Always done amazing with our pets . Caring staff. Will use again',
            'Had some poor experiences here. Will be driving to SA vet from now on.']


# %% md
# App
# %%
class Text_Analysis():

    def __init__(self):

        model_filename = 'model.sav'
        count_vectorizer_filename = 'count_vectorizer.sav'
        self.labels = ['Negative', 'Positive']

        self.model = pickle.load(open(model_filename, 'rb'))
        self.count_vectorizer = pickle.load(open(count_vectorizer_filename, 'rb'))

    def text_cleaning(self, text):
        review = re.sub("[^a-zA-Z]", ' ', text)
        review = review.lower()
        review = review.split()
        ps = PorterStemmer()
        review = [ps.stem(word) for word in review if not word in set(stopwords)]
        review = ' '.join(review)
        return review

    def get_sentiment_analysis_prediction(self, text):
        '''
        NOTE:
        get_sentiment_analysis_prediction function returns 0 or 1
        0 : comment classified as negative comment
        1 : comment classified as positive comment
        '''
        txt = self.text_cleaning(text)
        arr_txt = self.count_vectorizer.transform([txt]).toarray()
        return self.model.predict(arr_txt)[0]

    def get_topics_words(self, comments, no_topics=10, no_words_per_topic=10):
        tfidf = TfidfVectorizer(max_df=0.95, min_df=2, stop_words="english")
        dtm = tfidf.fit_transform(comments)
        nmf = NMF(n_components=no_topics)
        nmf.fit(dtm)
        topics_words = []
        for topic in nmf.components_:
            topics_words.append([tfidf.get_feature_names_out()[i] for i in topic.argsort()[-no_words_per_topic:]])
        return topics_words

    def separate_positive_negative_comments(self, comments):
        positive_comments = []
        negative_comments = []
        for comment in comments:
            if self.get_sentiment_analysis_prediction(comment) == 1:
                positive_comments.append(comment)
            else:
                negative_comments.append(comment)

        return positive_comments, negative_comments

    def get_topics_positive_negative_comments(self, comments):
        positive_comments, negative_comments = self.separate_positive_negative_comments(comments)

        topics_positive_comments = self.get_topics_words(positive_comments)
        topics_negative_comments = self.get_topics_words(negative_comments)

        return topics_positive_comments, topics_negative_comments


# @app.route('/comment', methods=['GET', 'POST'], endpoint='textAnalysis')
# def upload():
#     good_comments = int(0)
#     bad_comments = int(0)
#     unknown_comments = int(0)
#     arr = array.posnegComments = []
#     # t = []
#     # global pos_input_text
#     # if request.method == 'POST':
#     con = db_connector()
#     cursor = con.cursor()
#     cursor.execute("Select ClinicID from clinics")
#     counter = 1
#     # t.append(mycursor.fetchall())

#     t = cursor.fetchall()

#     print(t)

#     # Dict = {1: 'Geeks', 2: 'For', 3: 'Geeks'}
#     # i = 0
#     # i: object
#     for i in t:

#         print("ClinicId:", i)
#         cursor.execute('''SELECT Content FROM Comments WHERE ClinicID = ?''', i[0])
#         # getclinic = "Select Content from Comments where ClinicID=%s"
#         # values = (i)
#         # cursor.execute(getclinic, values)

#         result = cursor.fetchall()

#         for x in result:
#             arr.append(x)
#             sp = text_analysis.get_sentiment_analysis_prediction(str(x))
#             outputs = f'{text_analysis.labels[sp]}'
#             print(outputs)
#             if outputs == "Positive":

#                 good_comments = int(good_comments) + 1

#             elif outputs == "Negative":
#                 bad_comments = int(bad_comments) + 1

#             else:
#                 unknown_comments = int(unknown_comments) + 1

#         final_output = "Clinic Id:", counter, "Good comment Count: ", good_comments, "\n", "Bad comment Count: ", bad_comments, "\n", "unknown comments Count : ", unknown_comments, "."
#         print(final_output)
#         sql = '''Insert Into comment_analysis(ID, good_comment_count, bad_comment_count, unknown_comment_count, ClinicID) Values (?, ?, ?, ?, ?)'''
#         val = (int(random_number()), good_comments, bad_comments, unknown_comments, counter)
#         cursor.execute(sql, val)
#         db_connector().commit()
#         queryresult = cursor.rowcount
#         print(queryresult)

#         good_comments = int(0)
#         bad_comments = int(0)
#         unknown_comments = int(0)

#         # postrendingWords, negtendingwords = text_analysis.get_topics_positive_negative_comments(str(arr))
#         # print(arr)
#         # for lst in postrendingWords:
#         # print(lst)
#         # %%
#         # for lst in negtendingwords:
#         # print(lst)
#         counter += 1
#     return jsonify(
#         Result=final_output
#         # Result=final_output
#         # POStopicWords=postrendingWords,
#         # NEGtopicWords=negtendingwords
#     )
#     # i = + 1
#     # i = + 1


# i = +1
@app.route('/getCinicList', methods=['GET', 'POST'], endpoint='cliniclist')
def upload():
    resarr = []

    cursor1.execute(
        "SELECT cm.ClinicID,c.Name,c.Address, c.imageref,  sum(Case when cm.Type=1 then 1 else 0 end) as good, sum(Case when cm.Type=0 then 1 else 0 end) as bad, sum(Case when cm.Type=2 then 1 else 0 end) as unknown, count(*) as all_count FROM Comments cm inner join clinics c on c.ClinicID = cm.ClinicID group by cm.ClinicID, c.Name, c.Address, c.imageref")

    testt = cursor1.fetchall()
    # json_output = json.dumps(testt)
    for row in testt:
        resarr.append([x for x in row])
    resarr  # or simply data.append(list(row))
    return jsonify(
        message=resarr,
    )


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)
    # app.run(debug=True)
