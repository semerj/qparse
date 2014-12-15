import json
import os

from mongokit import Connection, Document

# Mongo configuration
MONGODB_HOST = 'localhost'
MONGODB_PORT = 27017

# connect to the database
conn = Connection(MONGODB_HOST, MONGODB_PORT)
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

filepath = 'parsed/'
files = [f for f in os.listdir(filepath)]

for f in files:
    with open(filepath + f, 'r') as infile:
        story = json.load(infile)
    a = conn.Article()
    a['name'] = f
    for para in story:
        a['paragraphs'].append(para)
    a.save()
