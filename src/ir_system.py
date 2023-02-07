import re
from collections import defaultdict, OrderedDict
import math
from src.utils import Heap
from tqdm import tqdm
import numpy as np


class IRSystem():
    
    def __init__(self, dataset):
        self.corpus = dataset()
        self.index = Index(self.corpus)
        self.N = len(self.corpus)

    def search(self, query):
        """This function return the top 10 documents of a query"""
        query_vector = self.get_query_vector(query)

    def get_query_vector(self, query):
        query_vector = np.zeros(len(self.index))
        for term in query:
            if term in self.index:
                query_vector[self.index[term].position] = 1

        # normalize
        query_vector = query_vector/np.linalg.norm(query_vector)
        return query_vector
    
    def get_doc_vectors(self):
        doc_vectors = []
        for docid in range(self.N):
            doc_vectors.append(self.get_doc_vector(docid))
        return doc_vectors

    def get_doc_vector(self, docid):
        doc_vector = np.zeros(len(self.index))
        for term in self.corpus[docid]:
            if term in self.index:
                doc_vector[self.index[term].position] = self.index.tf_idf(term, docid, self.N)
        # normalize
        doc_vector = doc_vector/np.linalg.norm(doc_vector)            
        return doc_vector
   
    def get_doc_vector_from_query(self, query):
        vectors = {}
        for term in query:
            if term in self.index:
                for docid, _ in self.index[term]:
                    if docid in vectors:
                        vectors[docid][self.index[term].position()] = self.index.tf_idf(term, docid, self.N)
                    else:
                        vectors[docid] = np.zeros(len(self.index))
                        vectors[docid][self.index[term].position()] = self.index.tf_idf(term, docid, self.N)
        # normalize
        for docid in vectors:
            if np.linalg.norm(vectors[docid]) > 0:
              vectors[docid] = vectors[docid]/np.linalg.norm(vectors[docid])
        return vectors
    


class Posting_list():
    def __init__(self, position):
        self._postings = []
        self._df = 0
        self._position = position

    def __repr__(self):
        return str(self._postings)

    def __iter__(self):
        return iter(self._postings)

    def add_posting(self, docid):
        index = self.find_posting_index(docid)
        if index is not None:
            self._postings[index] = (docid, self._postings[index][1] + 1)
        else:
            self._df += 1
            index = len(self._postings)
            self._postings.append((docid, 1))

        self.keep_postings_sorted(index)
    
    def keep_postings_sorted(self, index):
        while index > 0 and self._postings[index][1] > self._postings[index-1][1]:
            self._postings[index], self._postings[index-1] = self._postings[index-1], self._postings[index]
            index -= 1

    def find_posting_index(self, docid):
        for index, posting in enumerate(self._postings):
            if posting[0] == docid:
                return index
        return None

    def position(self):
        return self._position
    
    def get_post(self, docid):
        index = self.find_posting_index(docid)
        return self._postings[index]
    

class Index():
    def __init__(self, corpus):
        self._terms = OrderedDict()
        self.make_index(corpus)
    
    def __repr__(self):
        return str(self._terms)
    
    def __getitem__(self, term):
        try:
            return self._terms[term]
        except KeyError:
            return None

    def __contains__(self, term):
        try:
            self._terms[term]
            return True
        except KeyError:
            return False
        
    def __len__(self):
        return len(self._terms)
    

    def df(self, term):
        return self._terms[term]._df
    
    def idf(self, term, N):
        return math.log10(N/self.df(term))
    
    def tf(self, term, docid):
        _, tf = self._terms[term].get_post(docid)
        return tf
    
    def tf_idf(self, term, docid, N):
        return self.tf(term, docid)*self.idf(term, N)
        
    def make_index(self, corpus):
        position = 0
        for docid, doc in tqdm(enumerate(corpus), total=len(corpus)):
            for term in doc:
                try:
                    self._terms[term].add_posting(docid)
                except KeyError:
                    self._terms[term] = Posting_list(position)
                    position += 1
                    self._terms[term].add_posting(docid)
    

 