class Translations(object):
    def __init__(self):
        self._types = {
            'Quarterfinals': 'QFinals',
            'Grand Final': 'Finals'
        }

    @property
    def types(self):
        return self._types

    def translate(self, kind):
        if kind in self._types:
            return self._types[kind]
        return kind
