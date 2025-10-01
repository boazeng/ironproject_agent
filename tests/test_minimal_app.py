from flask import Flask, render_template

app = Flask(__name__)
app.config['TEMPLATES_AUTO_RELOAD'] = True

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/status')
def status():
    return {"status": "ok", "message": "Server is running"}

if __name__ == '__main__':
    print("Starting minimal Flask server...")
    app.run(host='0.0.0.0', port=5002, debug=True)