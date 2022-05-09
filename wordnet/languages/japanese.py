import gzip
import os.path
import sqlite3
import urllib.request
from wordnet.core import SynsetCollectorBase, WordNet, data_dir


class SynsetCollector(SynsetCollectorBase):
    def __init__(self, db_path):
        self.__conn = sqlite3.connect(db_path)
        self.__synsets = {}
        sql = """SELECT synset, lemma
                   FROM sense, word
                  WHERE sense.wordid=word.wordid;"""
        for synset_id, lemma in self.__conn.execute(sql):
            if synset_id not in self.__synsets:
                self.__synsets[synset_id] = {
                    'lemma': set(),
                    'hypernym': None,
                    'hyponym': None,
                }
            self.__synsets[synset_id]['lemma'].add(lemma)

    def all_ids(self):
        return self.__synsets.keys()

    def lemmas(self, synset_id):
        return self.__synsets[synset_id]['lemma']

    def hypernym_ids(self, synset_id):
        self.__set_linked_synsets_if_needs(synset_id)
        return self.__synsets[synset_id]['hypernym']

    def hyponym_ids(self, synset_id):
        self.__set_linked_synsets_if_needs(synset_id)
        return self.__synsets[synset_id]['hyponym']

    def __set_linked_synsets_if_needs(self, synset_id):
        synsets = self.__synsets[synset_id]
        if synsets['hyponym'] is not None and synsets['hyponym'] is not None:
            pass
        sql = f"""SELECT synset2, link
                    FROM synlink
                   WHERE synset1='{synset_id}'
                     AND (link='hype' OR link='hypo' OR link='syns');"""
        synsets['hypernym'] = set()
        synsets['hyponym'] = set()
        for synset2, link in self.__conn.execute(sql):
            if link == 'hype':
                synsets['hypernym'].add(synset2)
            if link == 'hypo':
                synsets['hyponym'].add(synset2)


def setup():
    GZ_PATH = os.path.join(data_dir, 'wnjpn.db.gz')
    DB_PATH = os.path.join(data_dir, 'wnjpn.db')
    URL = 'http://compling.hss.ntu.edu.sg/wnja/data/1.1/wnjpn.db.gz'
    if not os.path.exists(DB_PATH):
        urllib.request.urlretrieve(URL, GZ_PATH)
        with gzip.open(GZ_PATH, 'rb') as gz_f, open(DB_PATH, 'wb') as db_f:
            db_f.write(gz_f.read())
    collector = SynsetCollector(DB_PATH)
    wordnet = WordNet(collector)
    return wordnet
