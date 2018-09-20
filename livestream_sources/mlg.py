# System imports
from time import time
# Third-party imports
import requests
# Project imports
import cache
import config
from ._LivestreamSource import LivestreamSource
import log

class MLG(LivestreamSource):
    def __init__(self):
        settings = config.getSettings()
        game_ids = self.convertGames(settings['sidebar']['livestreams']['games'])['MLG']

        # The list of games. If there are none, just use CS:GO because CS:GO is awesome.
        game_id = ','.join(game_ids) if len(game_ids) > 0 else '13'

        self.name = 'MLG'
        self.streams_api = ''
        self.channels_api = '' % game_id
        self.request_headers = {}

    # Gets list of live streams from MLG
    # ---
    # The basic flow is
    #	1) Get all CS:GO-tagged channels on MLG
    #	2) Get a list of all streams and their number of viewers
    #	3) Assign the number of viewers (from step 2) to the channel object (from step 1)
    #	4) Return the completed channel object
    #
    # The oddity with this flow is due to how MLG separates "channels" and "streams"
    # with channels being a list of properties that must be manually changed
    # and streams being an indicator for whether or not the channel is live and
    # how many viewers it has.  I've requested they change this to make it more
    # intuitive, but no such luck as of yet.
    def get(self):
        log.log('\tGetting %s streams...' % self.name)
        startTime = time()
        settings = config.getSettings()

        if settings['dev_mode'] == True:
            log.log('\t\t...done getting %s streams! (cached data)' % self.name)
            cachedCopy = cache.readJson('%s.json' % self.name)
            return cachedCopy['data'] if cachedCopy != False else []

        # Get all CS:GO streams (CS:GO's MLG game ID is 13)
        mlgCsgoStreams = self.makeApiCall(self.channels_api)
        if mlgCsgoStreams == False:
            return self.useCachedCopy()

        streams = {}

        # Convert streams to usable, more uniform format
        for stream in mlgCsgoStreams:
            streams[stream['stream_name']] = self.convertStream(stream)

        # Get viewer info on all CS:GO channels
        streamInfo = self.makeApiCall(self.streams_api)
        if streamInfo == False:
            return self.useCachedCopy()

        liveStreams = []

        for stream in streamInfo:
            if stream['stream_name'] in streams:
                if 'viewers' in stream:
                    streams[stream['stream_name']]['viewers'] = '{:,}'.format(stream['viewers'])
                    streams[stream['stream_name']]['viewers_raw'] = stream['viewers']
                    liveStreams.append(streams[stream['stream_name']])

        elapsedTime = '\BLUE(%s s)' % str(round(time() - startTime, 3))
        log.log('\t\t\GREEN...done! %s' % (elapsedTime))

        cache.saveJson("%s.json" % self.name, {'time': time(), 'data': liveStreams})

        return liveStreams

    # Makes an API call to the given endpoint, returns False on any failure
    def makeApiCall(self, endpoint):
        apiResponse = super(MLG, self).makeApiCall(endpoint)
        if apiResponse == False:
            return False
        if apiResponse['status_code'] != 200:
            log.error('MLG status code NOT okay! (%s)' % str(apiResponse['status_code']))
            return False
        return apiResponse['data']['items']

    def convertStream(self, stream):
        return {
            'streamer': stream['name'],
            'title': self.prepareTitle(stream['subtitle']),
            'url': stream['url'],
            'thumbnail': stream['image_16_9_small'], # 208 x 117 is always the size, I believe
            'language': 'en'
        }