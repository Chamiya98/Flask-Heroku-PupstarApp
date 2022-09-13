from flask import jsonify, Flask

app = Flask(__name__)


@app.route('/login', methods=['GET', 'POST'])
def upload():
    result = "This is from flask"
    print("This is my app")

    return jsonify(
        message=result,
    )


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)
    # app.run(debug=True)
