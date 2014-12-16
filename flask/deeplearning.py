
# coding: utf-8

# In[1]:

import pandas as pd
import ast
import csv
import itertools
from nltk import RegexpParser
import pprint
import json
from unidecode import unidecode
pp = pprint.PrettyPrinter(indent=2)


# ### Read CSV as Dict

# In[2]:

df_dict = []
# with open('all_sentences_tagged_indexed__complete.csv') as csvfile:
#     reader = csv.DictReader(csvfile)
#     for key, row in enumerate(reader):
#         data = {}
#         data['sent_index'] = key
#         data['story_id'] = int(row['story_id'])
#         data['para_index'] = int(row['para_index'])
#         data['tagged_sent'] = ast.literal_eval(row['tagged_sent'])
#         data['quote_in_para'] = row['quote_in_para']
#         df_dict.append(data)


# ### Load Single Document

# In[3]:

quote_grammar = '''
NONQUOTE:   { <.*>+ }
            } <``> <.*>+ (<''>|<\'\'>) {
            } <``> <.*>+ (<''>|<\'\'>)? {
            } <``>? <.*>+ (<''>|<\'\'>) {

QUOTE:      { <``> <.*>+ (<''>|<\'\'>) }
            { <``> <.*>+ (<''>|<\'\'>)? }
            { <``>? <.*>+ (<''>|<\'\'>) }
'''


# ### FUNCTIONS

# In[51]:

def find_ngrams(input_list, n):
    return zip(*[input_list[i:] for i in range(n)])


def group_dict_func(list_of_dicts):
    keyfunc = lambda x: x['para_index']
    groups = []
    data = sorted(list_of_dicts, key=keyfunc)
    for k, g in itertools.groupby(data, key=keyfunc):
        groups.append(list(g))
    para_dict_list = []
    for g in groups:
        para_dict = {}
        para_dict['tagged_sent'] = []
        for l in g:
            para_dict['para_index'] = int(l['para_index'])
            para_dict['quote_in_para'] = int(l['quote_in_para'])
            para_dict['story_id'] = int(l['story_id'])
            para_dict['tagged_sent'].append(l['tagged_sent'])
        para_dict_list.append(para_dict)
    return para_dict_list


def parsing_function(ARTICLE_DICT, i, lookahead=0, featurenames='', getquotes=False):
    cp = RegexpParser(quote_grammar)
    list_of_sents = ARTICLE_DICT[i+lookahead]['tagged_sent']
    paragraph_quote_dict = {}
    number_of_sections = 0
    for key, sent in enumerate(list_of_sents):
        tree = cp.parse(sent)
        for subtree in tree.subtrees():
            if subtree.label() == 'NONQUOTE' or subtree.label() == 'QUOTE':
                paragraph_quote_dict[number_of_sections] = subtree
                number_of_sections += 1
            if getquotes and subtree.label() == 'QUOTE':
                ARTICLE_DICT[i]['quotations'].append(' '.join(s[0] for s in subtree))


    for key in paragraph_quote_dict.keys():
        if paragraph_quote_dict[key]._label == 'NONQUOTE':
            inverse_tuple_chunk = zip(*paragraph_quote_dict[key].leaves())
            pos_tags = inverse_tuple_chunk[1]
            words = inverse_tuple_chunk[0]
            pos_bigrams = find_ngrams(pos_tags, 2)
            word_bigrams = find_ngrams(pos_tags, 2)

            if 'said' in words and 'COREF' in pos_tags:
                said_match_indices = [x for x, y in enumerate(pos_tags) if y == 'COREF']
                matching_corefs = []
                for index in said_match_indices:
                    matching_corefs.append(words[index])
                ARTICLE_DICT[i]['feature_said_coref' + featurenames] = matching_corefs

            if ('COREF', u'VBD') in pos_bigrams and 'said' not in words:
                pos_match_indices = [x for x, y in enumerate(pos_bigrams) if y == ('COREF', u'VBD')]
                matching_pos_words = []
                for index in pos_match_indices:
                    matching_pos_words.append(words[index])
                ARTICLE_DICT[i]['feature_coref_vbd' + featurenames] = matching_pos_words

            if (u'VBD', 'COREF') in pos_bigrams and 'said' not in words:
                pos_match_indices = [x for x, y in enumerate(pos_bigrams) if y == (u'VBD', 'COREF')]
                matching_pos_words = []
                for index in pos_match_indices:
                    matching_pos_words.append(words[index+1])
                ARTICLE_DICT[i]['feature_vbd_coref' + featurenames] = matching_pos_words

            if 'COREF' in pos_tags:
                said_match_indices = [x for x, y in enumerate(pos_tags) if y == 'COREF']
                matching_corefs = []
                for index in said_match_indices:
                    matching_corefs.append(words[index])
                ARTICLE_DICT[i]['feature_coref_only' + featurenames] = matching_corefs

            if (u'NNP', u'NNP') in pos_bigrams:
                pos_match_indices = [x for x, y in enumerate(pos_bigrams) if y == (u'NNP', u'NNP')]
                matching_pos_words = []
                for index in pos_match_indices:
                    matching_pos_words.append(words[index+1])
                ARTICLE_DICT[i]['feature_nnp_nnp' + featurenames] = matching_pos_words

            if (u'NNS', u'NNP') in pos_bigrams:
                pos_match_indices = [x for x, y in enumerate(pos_bigrams) if y == (u'NNS', u'NNP')]
                matching_pos_words = []
                for index in pos_match_indices:
                    matching_pos_words.append(words[index+1])
                ARTICLE_DICT[i]['feature_nns_nnp' + featurenames] = matching_pos_words

            if (u'NNP', u'NNS') in pos_bigrams:
                pos_match_indices = [x for x, y in enumerate(pos_bigrams) if y == (u'NNP', u'NNS')]
                matching_pos_words = []
                for index in pos_match_indices:
                    matching_pos_words.append(words[index+1])
                ARTICLE_DICT[i]['feature_nnp_nns' + featurenames] = matching_pos_words

    return ARTICLE_DICT

def jsonify_sents(paragraph):
    tagged_sentences_pos = [item for sublist in paragraph for item in sublist]
    tagged_sentences = []
    for word in tagged_sentences_pos:
        if word[1] == 'COREF':
            tagged_sentences.append('< {}:{} >'.format(unidecode(word[0]), 'PERSON'))
        else:
            tagged_sentences.append(word[0])

    return ' '.join(tagged_sentences)


def group_articles(list_of_dicts):
    groups = []
    keyfunc = lambda x: x['story_id']
    data = sorted(list_of_dicts, key=keyfunc)
    for k, g in itertools.groupby(data, key=keyfunc):
        groups.append(list(g))
    return groups


def algorithm(ARTICLE):
    ARTICLE_DICT = group_dict_func(ARTICLE)
    LAST_PARA_INDEX = len(ARTICLE_DICT) - 1
    cp = RegexpParser(quote_grammar)
    for i, j in enumerate(ARTICLE_DICT):
        ARTICLE_DICT[i]['quotations'] = []
        if ARTICLE_DICT[i]['quote_in_para'] == 1:
            parsing_function(ARTICLE_DICT=ARTICLE_DICT, i=i, lookahead=0, featurenames='', getquotes=True)

            if j['para_index'] == 0:
                '''First paragraph'''
                if ARTICLE_DICT[i+1]['quote_in_para'] == 1:
                    parsing_function(ARTICLE_DICT=ARTICLE_DICT, i=i, lookahead=1, featurenames='_ahead')

            elif j['para_index'] == LAST_PARA_INDEX:
                '''Last paragraph'''
                if ARTICLE_DICT[i-1]['quote_in_para'] == 1:
                    parsing_function(ARTICLE_DICT=ARTICLE_DICT, i=i, lookahead=-1, featurenames='_back')

            elif j['para_index'] < LAST_PARA_INDEX:
                '''Middle paragraph'''
                parsing_function(ARTICLE_DICT=ARTICLE_DICT, i=i, lookahead=1, featurenames='_ahead')
                parsing_function(ARTICLE_DICT=ARTICLE_DICT, i=i, lookahead=-1, featurenames='_back')

    ARTICLE_DF = pd.DataFrame(ARTICLE_DICT).fillna(0)

    JSON_LIST = []
    column_names = list(ARTICLE_DF.columns.values)
    for index, row in ARTICLE_DF.iterrows():
        JSON_DICT = {}
        JSON_DICT['quotations'] = row.quotations
        JSON_DICT['paragraph'] = jsonify_sents(row.tagged_sent)
        JSON_DICT['quote_in_para'] = row.quote_in_para
        JSON_DICT['para_index'] = row.para_index
        JSON_DICT['story_id'] = row.story_id
        if row.quote_in_para == 1:
            if 'feature_said_coref' in column_names and row.feature_said_coref:
                JSON_DICT['speaker'] = list(set(row.feature_said_coref))
            elif 'feature_vbd_coref' in column_names and row.feature_vbd_coref:
                JSON_DICT['speaker'] = list(set(row.feature_vbd_coref))
            elif 'feature_coref_vbd' in column_names and row.feature_coref_vbd:
                JSON_DICT['speaker'] = list(set(row.feature_coref_vbd))
            elif 'feature_coref_only' in column_names and row.feature_coref_only:
                JSON_DICT['speaker'] = list(set(row.feature_coref_only))
            elif 'feature_said_coref_back' in column_names and row.feature_said_coref_back:
                JSON_DICT['speaker'] = list(set(row.feature_said_coref_back))
            elif 'feature_coref_only_back' in column_names and row.feature_coref_only_back:
                JSON_DICT['speaker'] = list(set(row.feature_coref_only_back))
            elif 'feature_coref_vbd_back' in column_names and row.feature_coref_vbd_back:
                JSON_DICT['speaker'] = list(set(row.feature_coref_vbd_back))
            elif 'feature_vbd_coref_back' in column_names and row.feature_vbd_coref_back:
                JSON_DICT['speaker'] = list(set(row.feature_coref_vbd_back))
            elif 'feature_nnp_nnp' in column_names and row.feature_nnp_nnp:
                JSON_DICT['speaker'] = list(set(row.feature_nnp_nnp))
            elif 'feature_nnp_nns' in column_names and row.feature_nnp_nns:
                JSON_DICT['speaker'] = list(set(row.feature_nnp_nns))
            elif 'feature_nns_nnp' in column_names and row.feature_nns_nnp:
                JSON_DICT['speaker'] = list(set(row.feature_nns_nnp))
            elif 'feature_nnp_nnp_back' in column_names and row.feature_nnp_nnp_back:
                JSON_DICT['speaker'] = list(set(row.feature_nnp_nnp_back))
            elif 'feature_nnp_nns_back' in column_names and row.feature_nnp_nns_back:
                JSON_DICT['speaker'] = list(set(row.feature_nnp_nns_back))
            elif 'feature_nns_nnp_back' in column_names and row.feature_nns_nnp_back:
                JSON_DICT['speaker'] = list(set(row.feature_nns_nnp_back))
            elif 'feature_said_coref_ahead' in column_names and row.feature_said_coref_ahead:
                JSON_DICT['speaker'] = list(set(row.feature_said_coref_ahead))
            elif 'feature_vbd_coref_ahead' in column_names and row.feature_vbd_coref_ahead:
                JSON_DICT['speaker'] = list(set(row.feature_vbd_coref_ahead))
            elif 'feature_coref_vbd_ahead' in column_names and row.feature_coref_vbd_ahead:
                JSON_DICT['speaker'] = list(set(row.feature_coref_vbd_ahead))
            elif 'feature_coref_only_ahead' in column_names and row.feature_coref_only_ahead:
                JSON_DICT['speaker'] = list(set(row.feature_coref_only_ahead))
            elif 'feature_nnp_nnp_ahead' in column_names and row.feature_nnp_nnp_ahead:
                JSON_DICT['speaker'] = list(set(str(row.feature_nnp_nnp_ahead)))
            elif 'feature_nnp_nns_ahead' in column_names and row.feature_nnp_nns_ahead:
                JSON_DICT['speaker'] = list(set(str(row.feature_nnp_nnp_ahead)))
            elif 'feature_nns_nnp_ahead' in column_names and row.feature_nns_nnp_ahead:
                JSON_DICT['speaker'] = list(set(str(row.feature_nnp_nnp_ahead)))
            else:
                JSON_DICT['speaker'] = ['Robert J. Glushko']
        elif row.quote_in_para == 0:
            JSON_DICT['speaker'] = None
        JSON_LIST.append(JSON_DICT)
    return JSON_LIST



if __name__ == '__main__':

    # # Write all Citizen-Quotes articles to JSON

    # In[ ]:

    citizen_quotes_groups = group_articles(df_dict)

    JSON_DATA = []
    for article in citizen_quotes_groups:
        JSON_DATA += algorithm(article)

    with open('citizen_quotes.json', 'w') as outfile:
        json.dump(JSON_DATA, outfile)


# # Examples in nonquote section
#
# ### Said, coref + Coref, said
# ```
# [(u'Jason Overman', 'COREF'), (u'said', u'VBD'), (u'.', u'.')]
#
# [(u'said', u'VBD'), (u'Bonnie Trinclisti', 'COREF'), (u'.', u'.')]
#
# [(u'said', u'VBD'), (u'Peter Straus', 'COREF'), (u',', u','), (u'Peter Straus', 'COREF'), (u'.', u'.')]
# ```

# ### Said, with stuff in between coref
# ```
# [(u'said', u'VBD'), (u'California', u'NNP'), (u'State', u'NNP'), (u'Parks', u'NNP'), (u'Foundation', u'NNP'), (u'president', u'NN'), (u'Elizabeth', u'NNP'), (u'Goldstein', u'NNP'), (u'.', u'.')]
#
# [(u'said', u'VBD'), (u'LandPaths', u'NNP'), (u"'", u'POS'), (u'executive', u'JJ'), (u'director', u'NN'), (u'Craig', u'NNP'), (u'Anderson', u'NNP'), (u'.', u'.')]
# ```

# ### Said, non-person speaking
# ```
# [(u'Reducing', u'VBG'), (u'the', u'DT'), (u'number', u'NN'), (u'of', u'IN'), (u'peace', u'NN'), (u'officers', u'NNS'), (u'could', u'MD'), (u'reduce', u'VB'), (u'state', u'NN'), (u'parks', u'NNS'), (u"'", u'POS'), (u'expenses', u'NNS'), (u'by', u'IN'), (u'at', u'IN'), (u'least', u'JJS'), (u'a', u'DT'), (u'few', u'JJ'), (u'million', u'CD'), (u'dollars', u'NNS'), (u',', u','), (u'the', u'DT'), (u'report', u'NN'), (u'said', u'VBD'), (u'.', u'.')]
# ```

# ### Coref, VBD (e.g. "added")
# ```
# [(u'The', u'DT'), (u'steps', u'NNS'), (u'Muni', 'COREF'), (u'is', u'VBZ'), (u'taking', u'VBG'), (u',', u','), (u'Ed Reiskin', 'COREF'), (u'added', u'VBD'), (u',', u',')]
# ```
