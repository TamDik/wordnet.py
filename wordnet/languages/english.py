from enum import Enum, auto
import os.path
import tarfile
import urllib.request
from wordnet.core import SynsetCollectorBase, WordNet, data_dir


class Pos(Enum):
    Noun = auto()
    Verb = auto()
    Adj = auto()
    Adv = auto()

    def to_str(self):
        return {
            Pos.Noun: 'noun',
            Pos.Verb: 'verb',
            Pos.Adj: 'adj',
            Pos.Adv: 'adv',
        }[self]

    def to_short(self):
        return {
            Pos.Noun: 'n',
            Pos.Verb: 'v',
            Pos.Adj: 'a',
            Pos.Adv: 'r',
        }[self]


class SynsetCollector(SynsetCollectorBase):
    def __init__(self, db_path):
        self.__dict_path = os.path.join(db_path, 'dict')
        self.__indexes = {}
        self.__datas = {}
        for pos in Pos:
            self.__parse_index_file(pos, self.__indexes)
            self.__parse_data_file(pos, self.__datas)

    def __parse_index_file(self, pos, indexes):
        filename = f'index.{pos.to_str()}'
        with open(os.path.join(self.__dict_path, filename)) as f:
            for line in f:
                if self.__is_extra_line(line):
                    continue
                line_data = self.__parse_index_file_line(line)
                pos = line_data['pos']
                for synset_offset in line_data['synset_offsets']:
                    synset_id = self.__to_synset_id(pos, synset_offset)
                    if synset_id not in indexes:
                        indexes[synset_id] = []
                    indexes[synset_id].append(line_data)

    def __parse_data_file(self, pos, datas):
        filename = f'data.{pos.to_str()}'
        pos_s = pos.to_short()
        with open(os.path.join(self.__dict_path, filename)) as f:
            for line in f:
                if self.__is_extra_line(line):
                    continue
                line_data = self.__parse_data_file_line(line)
                synset_offset = line_data['synset_offset']
                synset_id = self.__to_synset_id(pos_s, synset_offset)
                datas[synset_id] = (line_data)

    def __parse_index_file_line(self, line):
        fields = line.split()
        p_cnt = int(fields[3])
        return {
            'lemma': fields[0].replace('_', ' '),
            'pos': fields[1],
            'synsent_cnt': int(fields[2]),
            'ptr_symbols': fields[4:4+p_cnt],
            'sense_cnt': int(fields[4+p_cnt]),
            'tagsense_cnt': int(fields[5+p_cnt]),
            'synset_offsets': fields[6+p_cnt:],
        }

    def __parse_data_file_line(self, line):
        before_gloss, gloss = line.split(' | ', maxsplit=1)
        fields = before_gloss.split()
        w_cnt = int(fields[3], 16)
        word_and_lex_ids = []
        for i in range(w_cnt):
            word_i = 4 + 2 * i
            word = fields[word_i].replace('_', ' ')
            lex_id = int(fields[word_i + 1], 16)
            word_and_lex_ids.append((word, lex_id))
        p_cnt = int(fields[4 + 2 * w_cnt])
        ptrs = []
        for i in range(p_cnt):
            symbol_i = 5 + 2 * w_cnt + 4 * i
            ptrs.append({
                'ptr_symbol': fields[symbol_i],
                'synset_offset': fields[symbol_i + 1],
                'pos': fields[symbol_i + 2],
                'source': int(fields[symbol_i + 3][:2], 16),
                'target': int(fields[symbol_i + 3][2:], 16),
            })
        frames = []
        frame_fileds = fields[5 + 2 * w_cnt + 4 * p_cnt:]
        if frame_fileds:
            f_cnt = int(frame_fileds[0])
            for i in range(f_cnt):
                num_i = 3 * i + 2
                frames.append({
                    'f_num': int(frame_fileds[num_i]),
                    'w_num': int(frame_fileds[num_i + 1], 16),
                })
        return {
            'gloss': gloss,
            'synset_offset': fields[0],
            'lex_filenum': fields[1],
            'ss_type': fields[2],
            'word_and_lex_ids': word_and_lex_ids,
            'ptrs': ptrs,
            'frames': frames,
        }

    def __is_extra_line(self, line):
        return line.startswith('  ')

    def __to_synset_id(self, pos, synset_offset):
        return f'{synset_offset}-{pos}'

    def all_ids(self):
        return self.__indexes.keys()

    def lemmas(self, synset_id):
        lemmas = set()
        for index in self.__indexes[synset_id]:
            lemmas.add(index['lemma'])
        return lemmas

    def hypernym_ids(self, synset_id):
        synset_ids = set()
        for ptr in self.__datas[synset_id]['ptrs']:
            if ptr['ptr_symbol'] in ['@', '@i']:
                synset_offset = ptr['synset_offset']
                pos = ptr['pos']
                synset_id = self.__to_synset_id(pos, synset_offset)
                synset_ids.add(synset_id)
        return synset_ids

    def hyponym_ids(self, synset_id):
        synset_ids = set()
        for ptr in self.__datas[synset_id]['ptrs']:
            if ptr['ptr_symbol'] in ['~', '~i']:
                synset_offset = ptr['synset_offset']
                pos = ptr['pos']
                synset_id = self.__to_synset_id(pos, synset_offset)
                synset_ids.add(synset_id)
        return synset_ids


def setup():
    GZ_PATH = os.path.join(data_dir, 'WNdb-3.0.tar.gz')
    DB_PATH = os.path.join(data_dir, 'WNdb-3.0')
    URL = 'https://wordnetcode.princeton.edu/3.0/WNdb-3.0.tar.gz'
    if not os.path.exists(DB_PATH):
        urllib.request.urlretrieve(URL, GZ_PATH)
        with tarfile.open(GZ_PATH, 'r') as gz_f:
            gz_f.extractall(DB_PATH)
    collector = SynsetCollector(DB_PATH)
    wordnet = WordNet(collector)
    return wordnet
