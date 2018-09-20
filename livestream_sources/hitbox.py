import config
from ._LivestreamSource import LivestreamSource

class Hitbox(LivestreamSource):
    def __init__(self):
        settings = config.getSettings()
        game_ids = self.convertGames(settings['sidebar']['livestreams']['games'])['Hitbox']

        # Just use the first game, if there are none, just use CS:GO because CS:GO is awesome.
        # TODO: Implement multiple game searching on Hitbox
        game_id = game_ids[0] if len(game_ids) > 0 else '427'

        limit = str(settings['sidebar']['livestreams']['max_shown'] * 2)

        self.name = 'Hitbox'
        self.api_url = 'http://api.hitbox.tv/media/?game=' + game_id \
            + '&live=1&limit=' + limit
        self.streams_field = 'livestream'
        self.request_headers = {}

    def convertStream(self, stream):
        return {
            'streamer': stream['media_display_name'],
            'title': self.prepareTitle(stream['media_status']),
            'url': stream['channel']['channel_link'],
            'viewers_raw': int(stream['media_views']),
            'viewers': '{:,}'.format(int(stream['media_views'])),
            'thumbnail': 'http://edge.sf.hitbox.tv/' + stream['media_thumbnail'],
            'language': stream['media_countries'][0] if stream['media_countries'] != None and len(stream['media_countries']) > 0 else 'en'
        }