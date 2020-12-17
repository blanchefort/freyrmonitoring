from natasha import (Doc, 
                     NewsEmbedding, 
                     NewsNERTagger, 
                     Segmenter, 
                     MorphVocab, 
                     NewsMorphTagger)

emb = NewsEmbedding()
ner_tagger = NewsNERTagger(emb)
segmenter = Segmenter()
morph_vocab = MorphVocab()
morph_tagger = NewsMorphTagger(emb)

def lemmatize(text):
    doc = Doc(text)
    doc.segment(segmenter)
    doc.tag_morph(morph_tagger)
    
    for token in doc.tokens:
        token.lemmatize(morph_vocab)
    return [token.lemma for token in doc.tokens]

def ner(text):
    doc = Doc(text)
    doc.segment(segmenter)
    doc.tag_ner(ner_tagger)
    doc.tag_morph(morph_tagger)
    for token in doc.tokens:
        token.lemmatize(morph_vocab)

    for span in doc.spans:
        span.normalize(morph_vocab)
    ner_tokens = []
    for span in doc.spans:
        if span.type in ['PER', 'LOC']:
            tok = ''
            for token in span.tokens:
                tok += ' ' + token.lemma.upper()
            ner_tokens.append((tok.strip(), span.type))
        else:
            ner_tokens.append((span.normal.upper(), span.type))
    
    return set(ner_tokens)