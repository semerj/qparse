from __future__ import division
import json
import os
import pickle

from bson.objectid import ObjectId
from flask import Flask, render_template, request
from mongokit import Connection, Document
from unidecode import unidecode

import coreference
import deeplearning
from classify import quotex
from corenlp import corenlp

# Mongo configuration
MONGODB_HOST = 'localhost'
MONGODB_PORT = 27017

app = Flask(__name__)
app.config.from_object(__name__)

# connect to the database
conn = Connection(app.config['MONGODB_HOST'], app.config['MONGODB_PORT'])
coll = conn['qparse'].paragraphs

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
        'quotations': list,
        'paraClass': unicode,
        'speakerID': unicode
    }

@app.route('/')
def home():
    return render_template('base.html')

@app.route('/browse')
def browse():
    artlist = []
    # get all articles from mongo
    article_ids = coll.distinct('story_id')
    for a in article_ids:
        artlist.append({
            'name': a
        })

    speaker_ids = coll.distinct('speaker')
    speaklist = []
    for s in speaker_ids:
        if s:
            speaklist.append({
                'name': s
            })

    # this doesn't do anything, we don't have org data
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

@app.route('/article/<int:id>')
def story(id):
    paras = coll.Paragraph.find({'story_id': id}).sort('para_index')
    article = []
    # splice in span tags
    for p in paras:
        p['paragraph'] = p['paragraph'].replace("``", '<span class="quote">'+"``")
        p['paragraph'] = p['paragraph'].replace("''", "''"+'</span>')
        if p['speaker']:
            for speaker in p['speaker']:
                tagged_speaker = '<span class="speaker">' + speaker + "</span>"
                p['paragraph'] = p['paragraph'].replace(speaker, tagged_speaker)
        article.append(p)


    return render_template('article.html', article=article)

@app.route('/speaker/<id>')
def speaker(id):
    quotelist = coll.Paragraph.find({'speaker': id})
    return render_template('speaker.html', name=id, quotes=quotelist)

@app.route('/org/<id>')
def org(id):
    """
    we don't actually have this data
    """
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
    paras = coll.Paragraph.find({'story_id': story_id}).sort('para_index')
    article = []
    # splice in span tags
    for p in paras:
        p['paragraph'] = p['paragraph'].replace("``", '<span class="quote">'+"``")
        p['paragraph'] = p['paragraph'].replace("''", "''"+'</span>')
        if p['speaker']:
            for speaker in p['speaker']:
                tagged_speaker = '<span class="speaker">' + speaker + "</span>"
                p['paragraph'] = p['paragraph'].replace(speaker, tagged_speaker)
        article.append(p)
    return render_template('article.html', article=article)

@app.route('/eval', methods=["GET", "POST"])
def eval():
    if request.method == "POST":
        for form_id in request.form:
            if '__' in form_id:
                metric, para_id = form_id.split('__')
                val = request.form[form_id]
                para = coll.Paragraph.find_one({"_id": ObjectId(para_id)})
                para[metric] = val
                para.save()


    p = coll.Paragraph.find_random()
    story_id = p['story_id']
    paras = coll.Paragraph.find({'story_id': story_id}).sort('para_index')
    article = []
    # splice in span tags
    for p in paras:
        p['paragraph'] = p['paragraph'].replace("``", '<span class="quote">'+"``")
        p['paragraph'] = p['paragraph'].replace("''", "''"+'</span>')
        if p['speaker']:
            for speaker in p['speaker']:
                tagged_speaker = '<span class="speaker">' + speaker + "</span>"
                p['paragraph'] = p['paragraph'].replace(speaker, tagged_speaker)
        article.append(p)
    return render_template('eval.html', article=article)

@app.route('/accuracy')
def accuracy():
    para_class = {
        "total": coll.Paragraph.find({"paraClass": {"$ne": None}}).count(),
        "correct": {
            "raw": coll.Paragraph.find({"paraClass": "correct"}).count()
        },
        "typeI": {
            "raw": coll.Paragraph.find({"paraClass": "type I"}).count()
        },
        "typeII": {
            "raw": coll.Paragraph.find({"paraClass": "type II"}).count()
        }
    }

    para_class["correct"]['pct'] = 100 *(para_class["correct"]["raw"] / para_class["total"])
    para_class["typeI"]['pct'] = 100 *(para_class["typeI"]["raw"] / para_class["total"])
    para_class["typeII"]['pct'] = 100 *(para_class["typeII"]["raw"] / para_class["total"])

    speaker_id = {
        "total": coll.Paragraph.find({"speakerID": {"$ne": None}}).count(),
        "correct": {
            "raw": coll.Paragraph.find({"speakerID": "correct"}).count()
        },
        "incorrect": {
            "raw": coll.Paragraph.find({"speakerID": "incorrect"}).count()
        },
    }

    speaker_id["correct"]['pct'] = 100 *(speaker_id["correct"]["raw"] / speaker_id["total"])
    speaker_id["incorrect"]['pct'] = 100 *(speaker_id["incorrect"]["raw"] / speaker_id["total"])

    articles_count = len(coll.Paragraph.find({"paraClass": {"$ne": None}})
                            .distinct("story_id"))

    return render_template("accuracy.html",
        para_class=para_class, speaker_id=speaker_id, articles_count = articles_count)

@app.route('/parse', methods=["GET", "POST"])
def parse():
    if request.method == "GET":
        return render_template('submit.html')
    if request.method == "POST":
        # process the story
        # from magic import do.everything

        # TODO: pickle this test data to minimize re-parsing for now
        storytext = unidecode(request.form['storytext'])
        # with open('storytext.pickle', 'r') as outfile:
        #     storytext = pickle.load(outfile)

        # step 1: feed paragraphs to the classifier
        paras, has_quote = quotex(storytext)

        # with open('paras.pickle', 'r') as outfile:
        #     paras = pickle.load(outfile)
        # with open('has_quote.pickle', 'r') as outfile:
        #     has_quote = pickle.load(outfile)

        # TODO: put back
        # write it to a text file to feed to the parser
        with open('upload/temp', 'w') as outfile:
            outfile.write(storytext)

        # TODO: this is slow af
        parsed = corenlp.batch_parse('upload/', 'corenlp-python/javaparser/')

        # there will only ever be one file to parse
        parsed = next(parsed)
        # pickle this for testing so i don't have to fucking reparse every time
        # with open('parsed.pickle', 'r') as outfile:
        #     parsed = pickle.load(outfile)

        # munge the data for chunking
        df_dict = coreference.resolve(paras, has_quote, parsed)

        # TODO: add algorithms for picking out quote, speaker, job, org
        article_groups = deeplearning.group_articles(df_dict)

        JSON_DATA = []
        for article in article_groups:
            JSON_DATA += deeplearning.algorithm(article)

        # add output to database
        for p in JSON_DATA:
            store = coll.Paragraph(p)
            store.save()
        paras = coll.Paragraph.find({'story_id': JSON_DATA[0]['story_id']}).sort('para_index')
        article = []
        # splice in span tags
        for p in paras:
            p['paragraph'] = p['paragraph'].replace("``", '<span class="quote">'+"``")
            p['paragraph'] = p['paragraph'].replace("''", "''"+'</span>')
            if p['speaker']:
                for speaker in p['speaker']:
                    tagged_speaker = '<span class="speaker">' + speaker + "</span>"
                    p['paragraph'] = p['paragraph'].replace(speaker, tagged_speaker)
            article.append(p)

        #display the results
        return render_template('article.html', article=article)

if __name__ == '__main__':
    app.run(debug=True)
