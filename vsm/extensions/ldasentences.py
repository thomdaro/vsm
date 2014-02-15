import numpy as np

from vsm.corpus import Corpus
from vsm.corpus.util import *
import os


class CorpusSent(Corpus):
    """
    A subclass of Corpus whose purpose is to store original
    sentence information in the Corpus
    
    :See Also: :class: Corpus
    """
    def __init__(self, corpus, sentences, context_types=[], context_data=[], 
		remove_empty=False):
       super(CorpusSent, self).__init__(corpus, context_types=context_types,
		 context_data=context_data, remove_empty=remove_empty)
       self.sentences = np.array(sentences)


    def __set_words_int(self):
        """
        Mapping of words to their integer representations.
        """
        self.words_int = dict((t,i) for i,t in enumerate(self.words))


    def apply_stoplist(self, stoplist=[], freq=0):
        """ 
        Takes a Corpus object and returns a copy of it with words in the
        stoplist removed and with words of frequency <= `freq` removed.
        
	    :param stoplist: The list of words to be removed.
        :type stoplist: list
        
        :type freq: integer, optional
	    :param freq: A threshold where words of frequency <= 'freq' are 
            removed. Default is 0.
            
        :returns: Copy of corpus with words in the stoplist and words of
            frequnecy <= 'freq' removed.

        :See Also: :class:`Corpus`
        """
        if freq:
            #TODO: Use the TF model instead

            print 'Computing collection frequencies'
            cfs = np.zeros_like(self.words, dtype=self.corpus.dtype)
    
            for word in self.corpus:
                cfs[word] += 1

            print 'Selecting words of frequency <=', freq
            freq_stop = np.arange(cfs.size)[(cfs <= freq)]
            stop = set(freq_stop)
        else:
            stop = set()

        for t in stoplist:
            if t in self.words:
                stop.add(self.words_int[t])

        if not stop:
            print 'Stop list is empty.'
            return self
    
        print 'Removing stop words'
        f = np.vectorize(lambda x: x not in stop)
        corpus = self.corpus[f(self.corpus)]

        print 'Rebuilding corpus'
        corpus = [self.words[i] for i in corpus]
        context_data = []
        for i in xrange(len(self.context_data)):
            print 'Recomputing token breaks:', self.context_types[i]
            tokens = self.view_contexts(self.context_types[i])
            spans = [t[f(t)].size for t in tokens]
            tok = self.context_data[i].copy()
            tok['idx'] = np.cumsum(spans)
            context_data.append(tok)

        return CorpusSent(corpus, self.sentences, context_data=context_data,
                            context_types=self.context_types)


    @staticmethod
    def load(file):
        """
        Loads data into a Corpus object that has been stored using
        `save`.
        
        :param file: Designates the file to read. If `file` is a string ending
            in `.gz`, the file is first gunzipped. See `numpy.load`
            for further details.
        :type file: string-like or file-like object

        :returns: c : A Corpus object storing the data found in `file`.

        :See Also: :class: Corpus, :meth: Corpus.load, :meth: numpy.load
        """
        print 'Loading corpus from', file
        arrays_in = np.load(file)

        c = CorpusSent([], [])
        c.corpus = arrays_in['corpus']
        c.words = arrays_in['words']
        c.sentences = arrays_in['sentences']
        c.context_types = arrays_in['context_types'].tolist()

        c.context_data = list()
        for n in c.context_types:
            t = arrays_in['context_data_' + n]
            c.context_data.append(t)

        c.__set_words_int()

        return c

    def save(self, file):
        """
        Saves data from a CorpusSent object as an `npz` file.
        
        :param file: Designates the file to which to save data. See
            `numpy.savez` for further details.
        :type file: str-like or file-like object
            
        :returns: None

        :See Also: :class: Corpus, :meth: Corpus.save, :meth: numpy.savez
        """
	
	print 'Saving corpus as', file
        arrays_out = dict()
        arrays_out['corpus'] = self.corpus
        arrays_out['words'] = self.words
        arrays_out['sentences'] = self.sentences
        arrays_out['context_types'] = np.asarray(self.context_types)

        for i,t in enumerate(self.context_data):
            key = 'context_data_' + self.context_types[i]
            arrays_out[key] = t

        np.savez(file, **arrays_out)
        
    
    def sent_int(self, sent):
        """
        sent : list of strings
            List of sentence tokenization.
            The list could be a subset of existing sentence tokenization.
        """
        tok = self.view_contexts('sentence', as_strings=True)
        sent_li = []
        for i in xrange(len(tok)):
            sent_li.append(sent)
        keys = [i for i in xrange(len(tok)) 
                if set(sent_li[i]).issubset(tok[i].tolist())]
        
        n = len(keys)
        if n == 0:
            raise Exception('No token fits that description.')
        elif n > 1:
            return keys
        return keys[0] 



def sim_sent_sent(ldaviewer, sent, print_len=10):
    """
    ldaviewer : ldaviewer object
    sent : sentence index or sentence as a list of words

    Returns
    -------
    sim_sents : numpy array
        (sentence index, probability) as (i, value) pair.
    tokenized_sents : list of arrays
        List containing tokenized sentences as arrays.
    orig_sents : list of strings
        List containing original sentences as strings.
    """
    from vsm.viewer.ldagibbsviewer import LDAGibbsViewer

    corp = ldaviewer.corpus
    ind = sent
    if isinstance(sent, list) and isinstance(sent[0], str):
        ind = corp.sent_int(sent)
    sim_sents = ldaviewer.sim_doc_doc(ind, print_len=print_len, as_strings=False)
    lc = sim_sents['i'][:print_len]
    
    # only returns print_len length
    tokenized_sents, orig_sents = [], []
    for i in lc:
        tokenized_sents.append(corp.view_contexts('sentence', as_strings=True)[i])
        orig_sents.append(corp.sentences[i])

    return tokenized_sents, orig_sents, sim_sents



def file_tokenize(text):
    """
    `file_tokenize` is a helper function for :meth:`file_corpus`.
    
    Takes a string that is content in a file and returns words
    and corpus data.

    :param text: Content in a plain text file.
    :type text: string

    :returns: words : List of words.
        Words in the `text` tokenized by :meth:`vsm.corpus.util.word_tokenize`.
        corpus_data : Dictionary with context type as keys and
        corresponding tokenizations as values. The tokenizations
        are np.arrays.
    """
    words, par_tokens, sent_tokens, sent_orig = [], [], [], []
    sent_break, par_n, sent_n = 0, 0, 0

    pars = paragraph_tokenize(text)

    for par in pars:
        sents = sentence_tokenize(par)

        for sent in sents:
            w = word_tokenize(sent)
            words.extend(w)
            sent_break += len(w)
            sent_tokens.append((sent_break, par_n, sent_n))
            sent_orig.append(sent)
            sent_n += 1

        par_tokens.append((sent_break, par_n))
        par_n += 1

    idx_dt = ('idx', np.int32)
    sent_label_dt = ('sentence_label', np.array(sent_n, np.str_).dtype)
    par_label_dt = ('paragraph_label', np.array(par_n, np.str_).dtype)

    corpus_data = dict()
    dtype = [idx_dt, par_label_dt]
    corpus_data['paragraph'] = np.array(par_tokens, dtype=dtype)
    dtype = [idx_dt, par_label_dt, sent_label_dt]
    corpus_data['sentence'] = np.array(sent_tokens, dtype=dtype)

    return words, corpus_data, sent_orig


def file_corpus(filename, nltk_stop=True, stop_freq=1, add_stop=None):
    """
    `file_corpus` is a convenience function for generating Corpus
    objects from a a plain text corpus contained in a single string
    `file_corpus` will strip punctuation and arabic numerals outside
    the range 1-29. All letters are made lowercase.

    :param filename: File name of the plain text file.
    :type plain_dir: string-like
    
    :param nltk_stop: If `True` then the corpus object is masked 
        using the NLTK English stop words. Default is `False`.
    :type nltk_stop: boolean, optional
    
    :param stop_freq: The upper bound for a word to be masked on 
        the basis of its collection frequency. Default is 1.
    :type stop_freq: int, optional
    
    :param add_stop: A list of stop words. Default is `None`.
    :type add_stop: array-like, optional

    :returns: c : a Corpus object
        Contains the tokenized corpus built from the input plain-text
        corpus. Document tokens are named `documents`.
    
    :See Also: :class:`vsm.corpus.Corpus`, 
        :meth:`file_tokenize`, 
        :meth:`vsm.corpus.util.apply_stoplist`
    """
    with open(filename, mode='r') as f:
        text = f.read()

    words, tok, sent = file_tokenize(text)
    names, data = zip(*tok.items())
    
    c = CorpusSent(words, sent, context_data=data, context_types=names,
                    remove_empty=False)
    c = apply_stoplist(c, nltk_stop=nltk_stop,
                       freq=stop_freq, add_stop=add_stop)

    return c



def dir_tokenize(chunks, labels, chunk_name='article', paragraphs=True):
    """
    """
    words, chk_tokens, sent_tokens, sent_orig = [], [], [], []
    sent_break, chk_n, sent_n = 0, 0, 0

    if paragraphs:
        par_tokens = []
        par_n = 0
        
        for chk, label in zip(chunks, labels):
            print 'Tokenizing', label
            pars = paragraph_tokenize(chk)

            for par in pars:
                sents = sentence_tokenize(par)

                for sent in sents:
                    w = word_tokenize(sent)
                    words.extend(w)
                    sent_break += len(w)
                    sent_tokens.append((sent_break, label, par_n, sent_n))
                    sent_orig.append(sent)
                    sent_n += 1

                par_tokens.append((sent_break, label, par_n))
                par_n += 1

            chk_tokens.append((sent_break, label))
            chk_n += 1
    else:
        for chk, label in zip(chunks, labels):
            print 'Tokenizing', label
            sents = sentence_tokenize(chk)

            for sent in sents:
                w = word_tokenize(sent)
                words.extend(w)
                sent_break += len(w)
                sent_tokens.append((sent_break, label, sent_n))
                sent_orig.append(sent)
                sent_n += 1

            chk_tokens.append((sent_break, label))
            chk_n += 1

    idx_dt = ('idx', np.int32)
    label_dt = (chunk_name + '_label', np.array(labels).dtype)
    sent_label_dt = ('sentence_label', np.array(sent_n, np.str_).dtype)
    corpus_data = dict()
    dtype = [idx_dt, label_dt]
    corpus_data[chunk_name] = np.array(chk_tokens, dtype=dtype)

    if paragraphs:
        par_label_dt = ('paragraph_label', np.array(par_n, np.str_).dtype)
        dtype = [idx_dt, label_dt, par_label_dt]
        corpus_data['paragraph'] = np.array(par_tokens, dtype=dtype)
        dtype = [idx_dt, label_dt, par_label_dt, sent_label_dt]
        corpus_data['sentence'] = np.array(sent_tokens, dtype=dtype)
    else:
        dtype = [idx_dt, label_dt, sent_label_dt]
        corpus_data['sentence'] = np.array(sent_tokens, dtype=dtype)

    return words, corpus_data, sent_orig



def dir_corpus(plain_dir, chunk_name='article', paragraphs=True,
               nltk_stop=True, stop_freq=1, add_stop=None, corpus_sent=True):
    """
    `dir_corpus` is a convenience function for generating Corpus
    objects from a directory of plain text files.

    `dir_corpus` will retain file-level tokenization and perform
    sentence and word tokenizations. Optionally, it will provide
    paragraph-level tokenizations.

    It will also strip punctuation and arabic numerals outside the
    range 1-29. All letters are made lowercase.

    :param plain_dir: String containing directory containing a 
        plain-text corpus.
    :type plain_dir: string-like
    
    :param chunk_name: The name of the tokenization corresponding 
        to individual files. For example, if the files are pages 
        of a book, one might set `chunk_name` to `pages`. Default 
        is `articles`.
    :type chunk_name: string-like, optional
    
    :param paragraphs: If `True`, a paragraph-level tokenization 
        is included. Defaults to `True`.
    :type paragraphs: boolean, optional
    
    :param nltk_stop: If `True` then the corpus object is masked 
        using the NLTK English stop words. Default is `False`.
    :type nltk_stop: boolean, optional
    
    :param stop_freq: The upper bound for a word to be masked on 
        the basis of its collection frequency. Default is 1.
    :type stop_freq: int, optional

    :param corpus_sent: If `True` a CorpusSent object is returned.
        Otherwise Corpus object is returned. Default is `True`. 
    :type corpus_sent: boolean, optional

    :param add_stop: A list of stop words. Default is `None`.
    :type add_stop: array-like, optional

    :returns: c : Corpus or CorpusSent
        Contains the tokenized corpus built from the input plain-text
        corpus. Document tokens are named `documents`.
    
    :See Also: :class: Corpus, :class: CorpusSent, :meth: dir_tokenize,
        :meth: apply_stoplist
    """
    chunks = []
    filenames = os.listdir(plain_dir)
    filenames.sort()

    for filename in filenames:
        filename = os.path.join(plain_dir, filename)
        with open(filename, mode='r') as f:
            chunks.append(f.read())

    words, tok, sent = dir_tokenize(chunks, filenames, chunk_name=chunk_name,
                              paragraphs=paragraphs)
    names, data = zip(*tok.items())
    
    if corpus_sent:
        c = CorpusSent(words, sent, context_data=data, context_types=names,
			remove_empty=False)
    else:
        c = Corpus(words, context_data=data, context_types=names)
    c = apply_stoplist(c, nltk_stop=nltk_stop,
                       freq=stop_freq, add_stop=add_stop)

    return c