from flask import Flask, render_template, jsonify
import os

app = Flask(__name__)

@app.route('/')
def index():
    """Serve the main page"""
    return render_template('index.html')

@app.route('/test')
def test():
    """Test route"""
    return "Test route is working!"

@app.route('/api/latest-analysis')
def get_latest_analysis():
    """Return minimal analysis data"""
    return jsonify({
        'file': None,
        'analysis': None,
        'pdf_path': None
    })

@app.route('/api/files')
def get_files():
    """Return available files"""
    return jsonify({
        'success': True,
        'files': []
    })

@app.route('/api/select-file', methods=['POST'])
def select_file():
    """Handle file selection"""
    return jsonify({
        'success': True,
        'message': 'File selected successfully'
    })

if __name__ == "__main__":
    print("Minimal IRONMAN starting on http://localhost:5005")
    app.run(debug=False, host='127.0.0.1', port=5005, use_reloader=False)