import sqlite3
import re
from abc import ABCMeta, abstractmethod


class Synset:
    def __init__(self, wd, id_):
        if not isinstance(wd, WordNet):
            raise TypeError('Invalid wd. It must be a WordNet.')
        if not isinstance(id_, str):
            raise TypeError('Invalid id_. It must be a str.')
        self.__wd = wd
        self.__id = id_
        self.__hypernyms = None
        self.__hyponyms = None
        self.__lemmas = []

    def __eq__(self, other):
        return self.id == other.id

    def __repr__(self):
        return f'Synset {self.id}'

    def add_lemma(self, lemma):
        if not isinstance(lemma, str):
            raise TypeError('Invalid lemma. It must be a str.')
        self.__lemmas.append(lemma)

    @property
    def id(self):
        return self.__id

    @property
    def lemma(self):
        return self.__lemmas

    @property
    def hypernym(self):
        if self.__hypernyms is None:
            self.__set_linked_synsets()
        return self.__hypernyms

    @property
    def hyponym(self):
        if self.__hyponyms is None:
            self.__set_linked_synsets()
        return self.__hyponyms

    def __set_linked_synsets(self):
        detail = self.__wd.retrieve_linked_synsets(self.id)
        self.__hypernyms, self.__hyponyms = detail


class WordNet:
    def __init__(self, word_net_db_path):
        self.__conn = sqlite3.connect(word_net_db_path)
        self.__search_result = {'search': {}, 'search_one': {}}
        self.__synsets = {}
        sql = "SELECT synset, lemma FROM sense, word WHERE sense.wordid=word.wordid;"
        for synset, lemma in self.__conn.execute(sql):
            if synset not in self.__synsets:
                self.__synsets[synset] = Synset(self, synset)
            self.__synsets[synset].add_lemma(lemma)

    def __getitem__(self, key):
        if key not in self.__synsets:
            return None
        return self.__synsets[key]

    def __iter__(self):
        for synset in self.__synsets.values():
            yield synset

    def retrieve_linked_synsets(self, synset_id):
        if not isinstance(synset_id, str):
            raise TypeError('Invalid synset_id. It must be a str.')
        sql = f"""SELECT synset2, link FROM synlink
                   WHERE synset1='{synset_id}'
                       AND (link='hype' OR link='hypo' OR link='syns');"""
        hypernyms = []
        hyponyms = []
        for synset2, link in self.__conn.execute(sql):
            if link == 'hype':
                hypernyms.append(self.__synsets[synset2])
            if link == 'hypo':
                hyponyms.append(self.__synsets[synset2])
        return hypernyms, hyponyms

    def search(self, query):
        if not isinstance(query, str):
            raise TypeError('Invalid query. It must be a str.')
        if query in self.__search_result['search']:
            return self.__search_result['search'][query]
        searcher = self.__dispatch_searcher(query)
        result = searcher.search(query)
        self.__search_result['search'][query] = result
        return result

    def search_one(self, query):
        if not isinstance(query, str):
            raise TypeError('Invalid query. It must be a str.')
        if query in self.__search_result['search_one']:
            return self.__search_result['search_one'][query]
        searcher = self.__dispatch_searcher(query)
        result = searcher.search_one(query)
        self.__search_result['search_one'][query] = result
        return result

    def __dispatch_searcher(self, query):
        if self.__has_wildcard(query):
            searcher = SynsetVagueSearcher(self)
        else:
            searcher = SynsetPerfectSearcher(self)
        return searcher

    def __has_wildcard(self, query):
        return '*' in query


class SynsetSearcher(metaclass=ABCMeta):
    def __init__(self, word_net):
        if not isinstance(word_net, WordNet):
            raise TypeError('Invalid word_net. It must be a WordNet.')
        self.__word_net = word_net

    def search(self, pattern):
        if not isinstance(pattern, str):
            raise TypeError('Invalid pattern. It must be a str.')
        query = self._convert_to_query(pattern)
        result = []
        for synset in self.__word_net:
            if self._match(synset, query):
                result.append(synset)
        return result

    def search_one(self, pattern):
        if not isinstance(pattern, str):
            raise TypeError('Invalid pattern. It must be a str.')
        query = self._convert_to_query(pattern)
        for synset in self.__word_net:
            if self._match(synset, query):
                return synset
        return None

    @abstractmethod
    def _convert_to_query(self, pattern):
        pass

    @abstractmethod
    def _match(self, synset, query):
        pass


class SynsetPerfectSearcher(SynsetSearcher):
    def _convert_to_query(self, pattern):
        return pattern

    def _match(self, synset, query):
        return query in synset.lemma


class SynsetVagueSearcher(SynsetSearcher):
    def _convert_to_query(self, pattern):
        return re.compile('^' + re.sub(r'\*+', '.*', pattern) + '$')

    def _match(self, synset, query):
        for lemma in synset.lemma:
            if query.match(lemma):
                return True
        return False


def main():
    db_path = input('sqlite3 database path > ')
    wn = WordNet(db_path)
    print()
    print('----- access -----')
    synset = wn['02581957-n']
    print('ID   :', synset.id)
    print('Lemma:', ', '.join(synset.lemma))
    print('Hype :', ', '.join(map(str, synset.hypernym)))
    print('Hypo :', ', '.join(map(str, synset.hyponym)))
    print()

    print('----- search -----')
    query1 = 'dolphin'
    print(f'query: {query1}')
    print(f'search(query)    : {wn.search(query1)}')
    print(f'search_one(query): {wn.search_one(query1)}')
    print()

    query2 = 'dolph*'
    print(f'query: {query2}')
    print(f'search(query)    : {wn.search(query2)}')
    print(f'search_one(query): {wn.search_one(query2)}')

if __name__ == "__main__":
    main()
