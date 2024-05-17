from flask import Flask, request, render_template, jsonify, redirect, url_for

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('home.html')


@app.route('/index')
def index():
    return render_template('index.html', title = 'Home Page', heading = 'Welcome to Flask', content = 'Hello, Flask!')


@app.route('/about')
def about():
    return "This is the about page"


@app.route('/contact', methods = ['GET', 'POST'])
def contact():
    if request.method == 'POST':
        username = request.form['username']
        return f"Hello, {username}"
    return "Hello, stranger"


@app.route('/data')
def data():
    return jsonify({'key1': 'value1', 'key2': 'value2'})


@app.route('/go-to-home')
def go_to_home():
    return redirect(url_for('home'))


if __name__ == '__main__':
    app.run()