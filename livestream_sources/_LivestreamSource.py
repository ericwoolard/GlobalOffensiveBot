# System imports
import re
from time import time
# Third-party imports
import requests
# Project imports
import cache
from config import getSettings
import log

# Base LivestreamSource class, defines base functionality for the
# code that fetches API data from each livestream source
class LivestreamSource(object):
    def __init__(self):
        # Variables to override in derived classes
        self.name = 'DefaultSourceName'
        self.api_url = 'http://api.example.com/'
        self.streams_field = 'streams'
        self.request_headers = {}

    # Escapes markdown, strips whitespace, and truncates long titles
    def prepareTitle(self, title):
        prepared = ''
        markdown_chars = ['[',']','(',')','`','>','#','*','^']
        if '\n' in title:
            if '\n ' in title:
                title = title.replace('\n', '')
            else:
                title = title.replace('\n', ' ')

        for char in title:
            if char in markdown_chars:
                prepared += '\\' + char
            else:
                prepared += char

        prepared = prepared.replace('    ', '').strip()
        return prepared if len(prepared) < 42 else prepared[:42] + '...'

    # Core of the class: retrieves the API information, gets it converted, and returns it
    def get(self):
        log.log('\tGetting %s streams...' % self.name)
        startTime = time()
        settings = getSettings()

        # Just use the cached copy in dev mode
        if settings['dev_mode'] == True:
            log.log('\t\t...done getting %s streams! (cached data)' % self.name)
            cachedCopy = cache.readJson('%s.json' % self.name)
            return cachedCopy['data'] if cachedCopy != False else []

        req = self.makeApiCall(self.api_url)
        if req == False:
            return self.useCachedCopy()

        streams = req[self.streams_field]

        ret = []

        # Make sure we only have valid live streams, then add them to the
        # list of stream objects we're returning
        for stream in streams:
            streamObj = self.convertStream(stream)
            if streamObj != None:
                ret.append(streamObj)

        elapsedTime = '\BLUE(%s s)' % str(round(time() - startTime, 3))
        log.log('\t\t\GREEN...done! %s' % (elapsedTime))

        cache.saveJson("%s.json" % self.name, {'time': time(), 'data': ret})

        return ret

    # Make a request to the given URL, return JSON if possible. False on error.
    def makeApiCall(self, endpoint):
        try:
            apiResponse = requests.get(endpoint, timeout=7, headers=self.request_headers)
        except requests.exceptions.RequestException as e:
            log.error('API call for Livestream source "%s" failed \n"%s"' \
                % (self.name, str(e)), 2)
            return False
        try:
            apiResponse = apiResponse.json()
        except ValueError as e:
            log.error('JSON parsing for %s API failed\n\t"%s"' \
                % (self.name, str(e)), 2)
            return False
        return apiResponse

    # Wrap up using a cached copy of the response, use in case of error
    def useCachedCopy(self):
        # Grab a cached copy of the data if it exists
        cachedCopy = cache.readJson("%s.json" % self.name)
        # If it's been less than ten minutes since the last cache...
        if cachedCopy and time() - cachedCopy['time'] < 10 * 60:
            log.log('\t\t    (Using a cached copy for the moment)')
            # Return the cached copy's data
            return cachedCopy['data']
        else:
            log.error('Cache for %s is too old to use.' % self.name, 2)
            return ''

    # Function to override
    def convertStream(self, stream):
        return {
            'streamer': 'Default Streamer',
            'title': self.prepareTitle('Default Title'),
            'url': 'https://google.com/',
            'viewers_raw': 0,
            'viewers': '0',
            'thumbnail': 'https://www.google.com/images/srpr/logo11w.png',
            'language': 'EN'
        }

    # Convert any user-entered string of text into one of the games below.
    # NOTE: This is no longer used with new Helix Twitch API, use game IDs instead.
    def convertGames(self, games):
        # Regular expression definitions
        csgo = re.compile(r"c(s[: ]{0,2}?g(o|lobal offensive)|ounter[- ]?strike[: ]{0,2}?g(o|lobal offensive))", re.IGNORECASE)

        result = {
            'Twitch': []
        }

        # Maps the regex for each game to each service's name/ID for that game
        for game in games:
            if csgo.match(game) != None:
                result['Twitch'].append('Counter-Strike: Global Offensive')
                result['Hitbox'].append('427')
                result['Azubu'].append('csgo')
                result['MLG'].append('13')
            else:
                log.warning('No predefined game found for "%s", assuming unknown Twitch game.', 2)
                result['Twitch'].append(game)

        return result