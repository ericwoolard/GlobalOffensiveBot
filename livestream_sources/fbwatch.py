# System imports
import time
# Project imports
import cache
import config
import log
from ._LivestreamSource import LivestreamSource


class FBWatch(LivestreamSource):
    def __init__(self):
        self.settings = config.getSettings()
        request_headers = {}

        # Variables to be used in the rest of the object, mainly inherited funcs
        self.name = 'Facebook Watch'
        self.api_url = ''
        self.streams_field = '[]'
        self.request_headers = request_headers

    # Core of the class: retrieves the API information, gets it converted, and returns it
    def get(self):
        log.log('\tGetting %s streams...' % self.name)
        startTime = time.time()

        req = self.makeApiCall(self.api_url)
        if req == False:
            return self.useCachedCopy()

        streams = req
        ret = []

        # Make sure we only have valid live streams, then add them to the
        # list of stream objects we're returning
        for stream in streams:
            if stream['provider'] == 'facebook' and stream['islive'] == '1':
                if stream['account'] == '1948357485429258-english' and stream['viewers']:
                    streamObj = self.convertStream(stream)
                    if streamObj:
                        ret.append(streamObj)

        elapsedTime = '\BLUE(%s s)' % str(round(time.time() - startTime, 3))
        log.log('\t\t\GREEN...done! %s' % (elapsedTime))

        cache.saveJson("%s.json" % self.name, {'time': time.time(), 'data': ret})

        return ret

    def convertStream(self, stream):
        return {
            'streamer': stream['name'],
            'title': self.prepareTitle(stream['title']),
            'url': self.fixLink(stream['embed_code']),
            'viewers_raw': int(stream['viewers']),
            'viewers': '{:,}'.format(int(stream['viewers'])),
            'thumbnail': 'https://i.imgur.com/OBe46GF.png',
            'language': 'en',
            'provider': 'facebook'
        }

    """
    The 'link_provider' key (that *should* provide a correct Facebook Watch
    link) does not currently return a link with the correct video ID in the
    URL. This takes the correct ID (found in the 'embed_code' link) and builds
    the correct link for the stream. This won't be needed once this is fixed.
    """
    def fixLink(self, embed_code):
        video_id = embed_code.split('videos%2F')[1].split('%2F')[0]
        url = 'https://www.facebook.com/ESLProLeagueCSGO/videos/{}'.format(video_id)
        return url
