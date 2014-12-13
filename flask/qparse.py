from flask import Flask, render_template, request
import json

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('base.html')

@app.route('/story')
def display_story():
    with open('out.json', 'r') as infile:
        story = json.load(infile)
    return render_template('quote.html', story=story)

@app.route('/parse', methods=["GET", "POST"])
def input_form():
    if request.method == "GET":
        return render_template('submit.html')
    if request.method == "POST":
        # process the story
        # from magic import do.everything

        #display the results
        with open('out.json', 'r') as infile:
            story = json.load(infile)
        return render_template('quote.html', story=story)

if __name__ == '__main__':
    app.run(debug=True)
