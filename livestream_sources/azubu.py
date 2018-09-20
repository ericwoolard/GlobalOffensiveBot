import config
from ._LivestreamSource import LivestreamSource

class Azubu(LivestreamSource):
    def __init__(self):
        settings = config.getSettings()
        game_ids = self.convertGames(settings['sidebar']['livestreams']['games'])['Azubu']

        # Just use the first game, if there are none, just use CS:GO because CS:GO is awesome.
        # TODO: Implement multiple game searching on Azubu
        game_id = game_ids[0] if len(game_ids) > 0 else 'csgo'

        limit = str(settings['sidebar']['livestreams']['max_shown'] * 2)

        self.name = 'Azubu'
        self.api_url = 'http://api.azubu.tv/public/channel/live/list/game/' \
            + game_id + '?limit=' + limit
        self.streams_field = 'data'
        self.request_headers = {}

    def convertStream(self, stream):
        return {
            'streamer': stream['user']['display_name'],
            'title': self.prepareTitle(stream['user']['alt_name']),
            'url': stream['url_channel'],
            'viewers_raw': int(stream['view_count']),
            'viewers': '{:,}'.format(int(stream['view_count'])),
            'thumbnail': stream['url_thumbnail'],
            'language': "en"
        }