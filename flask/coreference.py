import hashlib
import pandas as pd

def resolve(raw_paras, guesses, parsed):
    """
    Function to take raw text, quote classifier guesses and StanfordNLP parse
    output and runs the coreferencing algorithm on it to prepare it for
    chunking
    """
    columns=['story_id', 'para_num', 'is_quote', 'text', 'chars']
    paras_table = []
    for index, text in enumerate(raw_paras):
        # 0 is a dummy story_id, paras are 1-indexed
        paras_table.append([0, index+1, guesses[index], text, len(text)])
    article = pd.DataFrame(data=paras_table, columns = columns)

    # this is where the action is:
    # replace corefs with canonical names in original text
    sentences_out = []

    # get the character offsets of paragraph breaks
    # so we can match them with sentences
    para_breaks = []
    for index, count in enumerate(article['chars']):
        if index == 0:
            para_breaks.append(0)
        else:
            # add 2 chars for each paragraph break
            para_breaks.append(sum(article['chars'][:index]) + (2 * index))

    print 'number of coref chains:', len(parsed['coref'])

    if 'coref' in parsed:
        corefs =  parsed['coref']
        # make sure it's a list, if there's only one coref
        if type(corefs) is not list:
            corefs = [corefs]
        # flag empty coref chains
        if len(corefs) < 1:
            corefs = None

    sentences = parsed['sentences']

    print 'sentences: ', len(sentences)
    # if only one sentence, make it a list
    if type(sentences) is not list:
        sentences = [sentences]

    paras = []

    # extract a list of persons and their indices in each sentence
    names = set()
    person_locs = []
    for sentence in sentences:
        tokens = sentence['words']
        # if only one token, make it a list
        if type(tokens) is not list:
            tokens = [tokens]
        print 'first token:', tokens[0]

        # create tagged text tuples instead of raw text
        # token format: ['word', {metadata}]
        tagged_sentence = [(t[0], t[1]['PartOfSpeech']) for t in tokens]
        print 'tagged sentence:', tagged_sentence
        # add each sentence to the DF, indexed by story and para
        offset = int(tokens[0][1]['CharacterOffsetBegin'])
        # para index is the largest number in para_breaks that is <= offset
        # default argument catches the last one, where there is no next
        para_index = next((para_breaks.index(b)-1 for b in para_breaks
                           if b > offset), len(para_breaks)-1)
        paras.append([para_index, tagged_sentence, article.iloc[para_index].loc['is_quote']])

    # print 'paragraph splits:', paras
        # aggregate adjacent NER person tags into full names
        i = 0
        people = {}
        while i < len(tokens):
            if tokens[i][1]['NamedEntityTag'] == 'PERSON':
                key = i
                person = tokens[i][0]
                # keep adding to this person string while the next token is also a person
                i += 1
                while tokens[i][1]['NamedEntityTag'] == 'PERSON':
                    person += ' ' + tokens[i][0]
                    i += 1
                people[key] = person
                names.add(person)
            i += 1
        person_locs.append(people)

    if corefs == None:
        # add to data table and move on, no corefs to resolve
        for row in paras:
            sentences_out.append([int(f[:-8]), row[0], row[1], row[2]])

    # sometimes it misses last-name-only references to the same person
    # do another pass on person_locs to reconcile names
    names_to_replace = {}
    for name in names:
        other_names = {n for n in names if n != name}
        # NOTE: this is a naive algorithm, it just picks the first match
        # even though multiple people may have the same last name
        for n in other_names:
            if n in name:
                names_to_replace[n] = name
    for sent in person_locs:
        for loc in sent:
            if sent[loc] in names_to_replace:
                sent[loc] = names_to_replace[sent[loc]]

    print 'indexed persons:', person_locs

    # assemble NERs that correspond to each coref chain
    corefs_text = {}
    corefs_ends = {}
    for coref_chain in corefs:
        indices = {}
        ends = {}

        for mention_index, mentions in enumerate(coref_chain):
            for mention_values in mentions:
                # mention structure: [0:'text', 1:sentence, 2:head, 3:start, 4:end]
                mention_keys = ['text', 'sentence', 'head', 'start', 'end']
                mention = dict(zip(mention_keys, mention_values))
                sent_index = int(mention['sentence'])
                word_start = int(mention['start'])
                word_end = int(mention['end'])
                if word_start in person_locs[sent_index]:
                    # does anything in this chain match an NER person?
                    # IF SO, store whole coref chain,
                    # but only the names and sentence/word indices
                    sent_indices = list({m[1] for m in mentions})
                    for sent in sent_indices:
                        if sent not in indices:
                            indices[sent] = {}
                            ends[sent] = {}
                        # add words
                        words_in_sent = {m[3]: '' for m in mentions
                                             if m[1] == sent}

                        indices[sent].update(words_in_sent)
                        # add endings
                        ends_in_sent = {int(m[3]): int(m[4])
                                            for m in mentions
                                            if m[1] == sent}
                        ends[sent].update(ends_in_sent)
                    break

        if indices:
            # get all NER person hits in the chain
            ners = []
            for sent_index in indices:
                for word in indices[sent_index]:
                    if word in person_locs[sent_index]:
                        ners.append(person_locs[sent_index][word])
            # canonical name is the longest one, not necessarily the first
            name = max(ners, key=len)

            # replace matched indices with name in corefs_text
            for sent_index in indices:
                if sent_index not in corefs_text:
                    corefs_text[sent_index] = {}
                    corefs_ends[sent_index] = {}
                for word in indices[sent_index]:
                    corefs_text[sent_index][word] = name
                    corefs_ends[sent_index].update(ends[sent_index])

    print 'matched coref locations:', corefs_text

    for i in reversed(sorted(corefs_text.keys())):
        # insert any canonical coreference tags
        locs = sorted(corefs_text[i].keys())
        locs.reverse()

        splice = [(loc, corefs_ends[i][loc]) for loc in locs]

        # account for overlapping coreferences
        for index, block in enumerate(splice):
            if index + 1 < len(splice):
                # detect an overlap in character ranges and keep the one that starts first
                if block[0] < splice[index + 1][1]:
                    splice[index] = None

        for index, loc in enumerate(locs):
            # if splice is None, skip it
            if splice[index]:
                # splice the coref tag into the sentence
                end = corefs_ends[i][loc]
                name = corefs_text[i][loc]
                new_sent = paras[i][1][:loc]
                new_sent += [(name, "COREF")]
                new_sent += paras[i][1][end:]
                # make sure it's stored in the original paras list
                paras[i][1] = new_sent

    # generate unique story id
    sent_1 = ' '.join([t[0] for t in paras[0][1]])
    story_id = hashlib.sha224(sent_1).hexdigest()[:7]

    # add to final data structure
    for key, row in enumerate(paras):
        # remember 0 is the dummy story id
        sentences_out.append({
            'sent_index': key,
            'story_id':story_id,
            'para_index':row[0],
            'tagged_sent': row[1],
            'quote_in_para': row[2]
        })
    return sentences_out
    # sentences_out gets passed to the next algorithm
