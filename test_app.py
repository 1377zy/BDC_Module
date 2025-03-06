from flask import Flask

app = Flask(__name__)

@app.route('/')
def hello():
    return "Hello, World! The server is running."

@app.route('/analytics')
def analytics():
    return "This is the analytics page. If you can see this, the server is working correctly."

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
