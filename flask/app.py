from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def index():
    # Bu komut 'templates' klasöründeki index.html'i arar
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)