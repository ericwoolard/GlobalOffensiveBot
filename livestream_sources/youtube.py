import config
import log
from time import time
from apiclient import discovery
from apiclient import errors
from oauth2client.tools import argparser
from pprint import pprint


settings = config.getSettings()

DEVELOPER_KEY = settings['api_key']['youtube']
YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"
SEARCH_PART = "snippet"
VIDEOS_PART = "liveStreamingDetails"
base_url = 'https://gaming.youtube.com/watch?v='
ret = []

def youtube_search():
    log.log('\tGetting YouTube Gaming streams...')
    startTime = time()
    
    youtube = discovery.build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION, developerKey=DEVELOPER_KEY)
    
    for channel in settings['sidebar']['livestreams']['youtube_channels'].values():
        try:
            # Call search.list to retrieve results matching the specified query term
            search_response = youtube.search().list(
                channelId=channel,
                part=SEARCH_PART,
                eventType="live",
                type="video"
            ).execute()

            live_streams = {}

            # Get the videoId of the livestream and send it with a request to videos.list to
            # retrieve viewer count. After retrieving the number of concurrent viewers, add
            # the info we need to the live_streams dictionary
            for search_result in search_response.get("items", []):
                if search_result["id"]["kind"] == "youtube#video":
                    metadata = youtube.videos().list(
                        part=VIDEOS_PART,
                        id=search_result['id']['videoId']
                    ).execute()
                    concurrent_viewers = metadata.get('items', [])

                    live_streams = {
                        'streamer': search_result['snippet']['channelTitle'],
                        'title': search_result['snippet']['title'],
                        'url': base_url + search_result['id']['videoId'],
                        'thumbnail': search_result['snippet']['thumbnails']['medium']['url'],
                        'viewers_raw': int(concurrent_viewers[0]['liveStreamingDetails']['concurrentViewers']),
                        'viewers': '{:,}'.format(int(concurrent_viewers[0]['liveStreamingDetails']['concurrentViewers']))}

                    ret.append(live_streams)

        except errors.HttpError as e:
            log.error("An HTTP error %d occurred:\n%s" % (e.resp.status, e.content))
        
    elapsedTime = '\BLUE(%s s)' % str(round(time() - startTime, 3))
    log.log('\t\t\GREEN...done! %s' % (elapsedTime))
    
    return ret
