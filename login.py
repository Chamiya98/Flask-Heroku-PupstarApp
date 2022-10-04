import firebase_admin
from flask import jsonify, Flask
from firebase_admin import credentials, initialize_app, db

app = Flask(__name__)

cred = credentials.Certificate('key.json')

firebase_admin.initialize_app(cred, {'databaseURL': 'https://dogcare-a80bc-default-rtdb.firebaseio.com/'})


@app.route('/login', methods=['GET', 'POST'])
def upload():
    # result = "This is from flask"
    # print("This is my app")

    ref = db.reference("/comment")
    res = ref.get()
    print(res)

    return jsonify(
        message=res,
    )


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)
    # app.run(debug=True)
