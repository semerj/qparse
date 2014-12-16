import json
import os
import pickle

from bson.objectid import ObjectId
from flask import Flask, render_template, request
from mongokit import Connection, Document
from unidecode import unidecode

from classify import quotex
from corenlp import corenlp

# Mongo configuration
MONGODB_HOST = 'localhost'
MONGODB_PORT = 27017

app = Flask(__name__)
app.config.from_object(__name__)

# connect to the database
conn = Connection(app.config['MONGODB_HOST'], app.config['MONGODB_PORT'])
coll = conn['qparse'].articles

# db models
@conn.register
class Article(Document):
    __database__ = 'qparse'
    __collection__ = 'articles'
    structure = {
        'name': str,
        'paragraphs': [{
            'quote': unicode,
            'speaker': unicode,
            'position': unicode,
            'organization': unicode,
            'fulltext': unicode
        }]
    }

@app.route('/')
def home():
    return render_template('base.html')

@app.route('/browse')
def browse():
    artlist = []
    # get all articles from mongo
    articles = coll.Article.find()
    for a in articles:
        artlist.append({
            'name': a['name'],
            'id': a['_id']
        })

    speakers = coll.aggregate([
        {'$unwind': '$paragraphs'},
        {'$match': {
            'paragraphs.speaker': {
                '$ne': None
                }
            }
        },
        {'$group': {
            '_id': '$paragraphs.speaker'
            }
        }
    ])

    speaklist = [s for s in speakers['result']]


    orgs = coll.aggregate([
        {'$unwind': '$paragraphs'},
        {'$match': {
            'paragraphs.organization': {
                '$ne': None
                }
            }
        },
        {'$group': {
            '_id': '$paragraphs.organization'
            }
        }
    ])

    orglist = [o for o in orgs['result']]

    return render_template('browse.html', articles=artlist, speakers=speaklist, orgs=orglist)

@app.route('/article/<id>')
def story(id):
    article = coll.Article.find_one({'_id': ObjectId(id)})
    return render_template('article.html', article=article)

@app.route('/speaker/<id>')
def speaker(id):
    quotes = coll.aggregate([
        {'$unwind': '$paragraphs'},
        {'$match': {'paragraphs.speaker': id }}
    ])
    quotelist = [q for q in quotes['result']]
    return render_template('speaker.html', name=id, quotes=quotelist)

@app.route('/org/<id>')
def org(id):
    quotes = coll.aggregate([
        {'$unwind': '$paragraphs'},
        {'$match': {'paragraphs.organization': id }}
    ])
    quotelist = [q for q in quotes['result']]
    return render_template('org.html', name=id, quotes=quotelist)


@app.route('/random')
def random():
    article = coll.Article.find_random()
    return render_template('article.html', article=article)

@app.route('/parse', methods=["GET", "POST"])
def parse():
    if request.method == "GET":
        return render_template('submit.html')
    if request.method == "POST":
        # process the story
        # from magic import do.everything
        # pickle this test data to minimize re-parsing for now
        storytext = unidecode(request.form['storytext'])
        # with open('storytext.pickle', 'w') as outfile:
        #     pickle.dump(storytext, outfile)
        # step 1: feed paragraphs to the classifier
        paras, has_quote = quotex(storytext)
        # with open('paras.pickle', 'w') as outfile:
        #     pickle.dump(paras, outfile)
        # with open('has_quote.pickle', 'w') as outfile:
        #     pickle.dump(has_quote, outfile)

        # write it to a text file to feed to the parser
        with open('upload/temp', 'w') as outfile:
            outfile.write(storytext)

        # TODO: this is slow af
        # parsed = corenlp.batch_parse('upload/', 'corenlp-python/javaparser/')

        # there will only ever be one file to parse
        # parsed = next(parsed)
        # pickle this for testing so i don't have to fucking reparse every time
        # print parsed

        # assume there's already a stanfordnlp server running
        # server = jsonrpclib.Server("http://127.0.0.1:8080")
        # return server.parse(storytext)
        # TODO: too slow, it just stalls out without erroring

        # return 'see file'

        #display the results
        with open('out.json', 'r') as infile:
            story = json.load(infile)
        return render_template('article.html', article=story)

if __name__ == '__main__':
    app.run(debug=True)
