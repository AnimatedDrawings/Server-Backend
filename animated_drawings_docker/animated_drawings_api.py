from flask import Flask

app = Flask(__name__)

@app.route('/ping')
def ping():
    return 'AnimatedDrawings test ping success!!'

@app.route('/return_to_mfa')
def return_to_mfa():
    return 'response from animated drawings'

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port='50')