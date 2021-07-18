# wordnet.py

Wordnet.py provides an interface to use WordNet for Python3.

```python
db_path = '/path/to/sqlite3-database-path'
wn = WordNet(db_path)

# access
synset = wn['02581957-n']
synset.id
synset.lemma
synset.hypernym
synset.hyponym

# search
query1 = 'dolphin'
wn.search(query1)
wn.search_one(query1)

query2 = 'dolph*'
wn.search(query2)
wn.search_one(query2)
```
