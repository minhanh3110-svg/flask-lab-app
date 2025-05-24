from flask import Flask, render_template, request, session
app = Flask(__name__)
app.secret_key = 'secret'

@app.route('/')
def index():
    return render_template("index.html", log=None, staff="")

if __name__ == "__main__":
    app.run(debug=True)
