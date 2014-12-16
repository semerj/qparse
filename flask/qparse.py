import json
import os
import pickle

from bson.objectid import ObjectId
from flask import Flask, render_template, request
from mongokit import Connection, Document
from unidecode import unidecode

import coreference
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
class Paragraph(Document):
    __database__ = 'qparse'
    __collection__ = 'paragraphs'
    structure = {
        'para_index': int,
        'story_id': int,
        'paragraph': unicode,
        'speaker': list,
        'quote_in_para': int,
        'quotations': list
    }

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
    p = coll.Paragraph.find_random()
    story_id = p['story_id']
    article = coll.Paragraph.find({"story_id": story_id})
    return render_template('article.html', article=article)

@app.route('/parse', methods=["GET", "POST"])
def parse():
    if request.method == "GET":
        return render_template('submit.html')
    if request.method == "POST":
        # process the story
        # from magic import do.everything

        # TODO: pickle this test data to minimize re-parsing for now
        # storytext = unidecode(request.form['storytext'])
        with open('storytext.pickle', 'r') as outfile:
            storytext = pickle.load(outfile)

        # step 1: feed paragraphs to the classifier
        # paras, has_quote = quotex(storytext)

        with open('paras.pickle', 'r') as outfile:
            paras = pickle.load(outfile)
        with open('has_quote.pickle', 'r') as outfile:
            has_quote = pickle.load(outfile)

        # TODO: put back
        # write it to a text file to feed to the parser
        # with open('upload/temp', 'w') as outfile:
        #     outfile.write(storytext)

        # TODO: this is slow af
        # parsed = corenlp.batch_parse('upload/', 'corenlp-python/javaparser/')

        # there will only ever be one file to parse
        # parsed = next(parsed)
        # pickle this for testing so i don't have to fucking reparse every time
        with open('parsed.pickle', 'r') as outfile:
            parsed = pickle.load(outfile)

        # munge the data for chunking
        coreference.resolve(paras, has_quote, parsed)

        # TODO: add algorithms for picking out quote, speaker, job, org

        #display the results
        story = coll.Article.find_random()
        return render_template('article.html', article=story)

if __name__ == '__main__':
    app.run(debug=True)
