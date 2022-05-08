import os
import re
from abc import ABCMeta, abstractmethod


def is_win():
    return os.name == 'nt'


if is_win():
    __LOCALAPPDATA = os.environ['LOCALAPPDATA']
    data_dir = os.path.join(__LOCALAPPDATA, 'wordnet.py')
elif os.name == 'posix' and 'XDG_DATA_HOME' in os.environ:
    __XDG_DATA_HOME = os.environ['XDG_DATA_HOME']
    data_dir = os.path.join(__XDG_DATA_HOME, 'wordnet.py')
else:
    data_dir = os.path.expanduser('~/.local/share/wordnet.py')
os.makedirs(data_dir, exist_ok=True)


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
        self.__lemmas = None

    def __eq__(self, other):
        return self.id == other.id

    def __repr__(self):
        return f'Synset {self.id}'

    @property
    def id(self):
        return self.__id

    @property
    def lemma(self):
        if self.__lemmas is None:
            lemmas = self.__wd.retrieve_lemmas(self.id)
            self.__lemmas = self.__to_list_bject(lemmas)
        return self.__lemmas

    @property
    def hypernym(self):
        if self.__hypernyms is None:
            synsets = self.__wd.retrieve_hypernyms(self.id)
            self.__hypernyms = self.__to_list_bject(synsets)
        return self.__hypernyms

    @property
    def hyponym(self):
        if self.__hyponyms is None:
            synsets = self.__wd.retrieve_hyponyms(self.id)
            self.__hyponyms = self.__to_list_bject(synsets)
        return self.__hyponyms

    def __to_list_bject(self, items):
        list_ = []
        for item in items:
            list_.append(item)
        return list_


class WordNet:
    def __init__(self, collector):
        if not isinstance(collector, SynsetCollectorBase):
            mes = 'Invalid collector. It must be a SynsetCollectorBase.'
            raise TypeError(mes)
        self.__synsets = {}
        self.__collector = collector
        for synset_id in self.__collector.all_ids():
            self.__synsets[synset_id] = Synset(self, synset_id)

    def __getitem__(self, key):
        if key not in self.__synsets:
            return None
        return self.__synsets[key]

    def __iter__(self):
        for synset in self.__synsets.values():
            yield synset

    def retrieve_lemmas(self, synset_id):
        return self.__collector.lemmas(synset_id)

    def retrieve_hypernyms(self, synset_id):
        synset_ids = self.__collector.hypernym_ids(synset_id)
        return self.__to_synset_list(synset_ids)

    def retrieve_hyponyms(self, synset_id):
        synset_ids = self.__collector.hyponym_ids(synset_id)
        return self.__to_synset_list(synset_ids)

    def __to_synset_list(self, synset_ids):
        synsets = []
        for synset_id in synset_ids:
            synsets.append(self.__synsets[synset_id])
        return synsets


class SynsetCollectorBase(metaclass=ABCMeta):
    @abstractmethod
    def all_ids(self):
        pass

    @abstractmethod
    def lemmas(self, synset_id):
        pass

    @abstractmethod
    def hypernym_ids(self, synset_id):
        pass

    @abstractmethod
    def hyponym_ids(self, synset_id):
        pass


class SynsetFilter(metaclass=ABCMeta):
    def do_filter(self, word_net, pattern):
        if not isinstance(word_net, WordNet):
            raise TypeError('Invalid word_net. It must be a WordNet.')
        if not isinstance(pattern, str):
            raise TypeError('Invalid pattern. It must be a str.')
        query = self._convert_to_query(pattern)
        result = []
        for synset in word_net:
            if self._match(synset, query):
                result.append(synset)
        return result

    @abstractmethod
    def _convert_to_query(self, pattern):
        pass

    @abstractmethod
    def _match(self, synset, query):
        pass


class ExactMatchFilter(SynsetFilter):
    def _convert_to_query(self, pattern):
        return pattern

    def _match(self, synset, query):
        return query in synset.lemma


class PartialMatchFilter(SynsetFilter):
    def _convert_to_query(self, pattern):
        return pattern

    def _match(self, synset, query):
        for lemma in synset.lemma:
            if query in lemma:
                return True
        return False


class VagueMatchFilter(SynsetFilter):
    def _convert_to_query(self, pattern):
        return re.compile('^' + re.sub(r'\*+', '.*', pattern) + '$')

    def _match(self, synset, query):
        for lemma in synset.lemma:
            if query.match(lemma):
                return True
        return False
