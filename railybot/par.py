import spacy
import dateparser

nlp = spacy.load('en_core_web_sm')

text = 'delay of 3 hours'

doc = nlp(text)

minutes = {
    'hour': 60,
    'minute': 1,
}

scrapper = {
    'NOUN': 0,
    'NUM': 0
}
total_time = 1
for ent in doc.ents:
    if ent.label_ == 'TIME':
        for token in nlp(ent.text):
            if token.pos_ in ['NOUN']:
                try:
                    total_time *= minutes[token.lemma_]
                except:
                    raise Exception('No compatible')
            elif token.pos_ in ['NUM']:
                total_time *= float(token.text)
    break