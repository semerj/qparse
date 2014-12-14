from corenlp import corenlp
from flask import Flask, render_template, request
import json
import os

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('base.html')

@app.route('/browse')
def browse():
    filepath = 'parsed/'
    files = [f for f in os.listdir(filepath)]
    return render_template('browse.html', files=files)

@app.route('/story/<filename>')
def story(filename):
    filepath = 'parsed/'
    with open(filepath+filename, 'r') as infile:
        story = json.load(infile)
    return render_template('quote.html', story=story, title=filename)

@app.route('/parse', methods=["GET", "POST"])
def parse():
    if request.method == "GET":
        return render_template('submit.html')
    if request.method == "POST":
        # process the story
        # from magic import do.everything
        storytext = request.form['storytext']
        # write it to a text file to feed to the parser
        with open('upload/temp', 'w') as outfile:
            outfile.write(storytext.encode('utf8'))

        # TODO: this is slow af
        parsed = corenlp.batch_parse('upload/', 'corenlp-python/javaparser/')

        # there will only ever be one file to parse
        parsed = next(parsed)
        # print parsed

        # assume there's already a stanfordnlp server running
        # server = jsonrpclib.Server("http://127.0.0.1:8080")
        # return server.parse(storytext)
        # TODO: too slow, it just stalls out without erroring

        # return 'see file'

        #display the results
        with open('out.json', 'r') as infile:
            story = json.load(infile)
        return render_template('quote.html', story=story)

if __name__ == '__main__':
    app.run(debug=True)
