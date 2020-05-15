import config
import requests
from ._LivestreamSource import LivestreamSource

class Twitch(LivestreamSource):
    def __init__(self):
        self.settings = config.getSettings()
        self.oauth_info = config.getOAuthInfo()
        self.is_token_valid = self.validateToken(self.oauth_info)
        self.token = self.getOauth()

        parameters = ''
        request_headers = {}
        game_id = 0
        max_shown = str(self.settings['sidebar']['livestreams']['max_shown'] * 2)

        if 'twitch' in self.settings and 'client_id' in self.settings['twitch']:
            request_headers = {
                'Authorization': 'Bearer {}'.format(self.token),
                'Client-ID': self.settings['twitch']['client_id']
            }

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
            'url': 'https://twitch.tv/{}'.format(stream['user_name'].replace(' ', '')),
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


    # See if our OAuth token is still valid. If this fails,
    # our token is likely expired and needs to be renewed.
    def validateToken(self, oauth_info):
        access_token = oauth_info['twitch']['access_token']
        if access_token:
            val_url = 'https://id.twitch.tv/oauth2/validate'
            res = requests.get(val_url, headers={'Authorization': 'OAuth {}'.format(access_token)})
            if res.status_code == 200:
                return True
            else:
                return False
        else:
            return False


    # Handle the OAuth code flow for Application type authorization.
    # Store our access token so it may be used until it expires.
    def getOauth(self):
        if not self.is_token_valid:
            request_data = {
                    'client_id': self.settings['twitch']['client_id'],
                    'client_secret': self.settings['twitch']['client_secret'],
                    'grant_type': self.settings['twitch']['grant_type']
                }
            token_url = 'https://id.twitch.tv/oauth2/token'
            res = requests.post(token_url, data=request_data)
            if res.status_code == 200:
                res_data = res.json()
                self.oauth_info['twitch']['access_token'] = res_data['access_token']
                config.setOAuthInfo(self.oauth_info)
                return res_data['access_token']
            else:
                return None
        else:
            return self.oauth_info['twitch']['access_token']
