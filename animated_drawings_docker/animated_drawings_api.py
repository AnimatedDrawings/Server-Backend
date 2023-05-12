from flask import Flask

app = Flask(__name__)

@app.route('/test_ping')
def test_ping():
    return 'AnimatedDrawings test ping success!!'

if __name__ == '__main__':
    app.run(host='0.0.0.0', port='50')