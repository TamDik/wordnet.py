# wordnet.py

Wordnet.py provides an interface to use WordNet for Python3.

## Example

```python
from wordnet.languages.japanese import setup
from wordnet.core import ExactMatchFilter, VagueMatchFilter

wn = setup()

# access
synset = wn['02581957-n']
synset.id
synset.lemma
synset.hypernym
synset.hyponym

# search
ExactMatchFilter().do_filter(wn, 'dolphin')

VagueMatchFilter().do_filter(wn, 'dolph*')
```
