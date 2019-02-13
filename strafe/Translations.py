class Translations(object):
    def __init__(self):
        self._types = {
            'Quarterfinals': 'QFinals',
            'Grand Final': 'Finals',
            'Opening Matches': 'Opener',
            'Elimination Match': 'Elimination',
            'Winners\' Match': 'Winners',
            'Decider Match': 'Decider',
            'Round 2 Low': 'Rd. 2 Low',
            'Round 2 High': 'Rd. 2 High',
            'Round 3 Low': 'Rd. 3 Low',
            'Round 3 Mid': 'Rd. 3 Mid',
            'Round 3 High': 'Rd. 3 High',
            'Round 4 Low': 'Rd. 4 Low',
            'Round 4 Mid': 'Rd. 4 Mid',
            'Round 4 High': 'Rd. 4 High'
        }

    @property
    def types(self):
        return self._types

    def translate(self, kind):
        if kind in self._types:
            return self._types[kind]
        return kind
