import config
from ._LivestreamSource import LivestreamSource

class Twitch(LivestreamSource):
    def __init__(self):
        self.settings = config.getSettings()

        parameters = ''
        request_headers = {}
        game_id = 0
        max_shown = str(self.settings['sidebar']['livestreams']['max_shown'] * 2)

        if 'api_key' in self.settings and 'twitch' in self.settings['api_key']:
            request_headers = {'Client-ID': self.settings['api_key']['twitch']}

        # If the sidebar.livestreams.twitch_include_only field is set in
        # settings, then we only grab those channels from Twitch.
        if 'twitch_include_only' in self.settings['sidebar']['livestreams']:
            channels = self.settings['sidebar']['livestreams']['twitch_include_only']
            if channels != []:
                parameters.append('channel=' + ','.join(channels))

        if 'game_ids' in self.settings['sidebar']['livestreams']:
            if 'CSGO' in self.settings['sidebar']['livestreams']['game_ids']:
                game_id = self.settings['sidebar']['livestreams']['game_ids']['CSGO']
                # Turn parameters list into a stringified URL parameter chain
                parameters = '?game_id={}&first={}'.format(game_id, max_shown)

        # Variables to be used in the rest of the object, mainly inherited funcs
        self.name = 'Twitch'
        self.api_url = 'https://api.twitch.tv/helix/streams/' + parameters
        self.streams_field = 'data'
        self.request_headers = request_headers

    def convertStream(self, stream):
        return {
            'streamer': stream['user_name'],
            'title': self.prepareTitle(stream['title']),
            'url': 'https://twitch.tv/{}'.format(stream['user_name']),
            'viewers_raw': int(stream['viewer_count']),
            'viewers': '{:,}'.format(int(stream['viewer_count'])),
            'thumbnail': self.checkCustomThumbs(stream, stream['user_name']),
            'language': stream['language']
        }

    def checkCustomThumbs(self, stream, user):
        if user in self.settings['sidebar']['livestreams']['custom_thumbs']:
            thumb_link = self.settings['sidebar']['livestreams']['custom_thumbs'][user]
            return thumb_link

        return stream['thumbnail_url'].replace('{width}', '45').replace('{height}', '30')
