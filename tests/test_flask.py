from flask import Flask

app = Flask(__name__)

@app.route('/')
def hello():
    return '<h1>Flask Test Server Running!</h1><p>The Flask server is working correctly.</p>'

if __name__ == '__main__':
    print("Starting test Flask server on http://localhost:5000")
    app.run(host='0.0.0.0', port=5000, debug=False)