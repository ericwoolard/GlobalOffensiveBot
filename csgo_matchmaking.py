# System imports
from time import time
# Third-party imports
import requests
# Project imports
import cache
from config import getSettings
import log

def getStatus():
    log.log('Getting CS:GO Matchmaking status...')
    startTime = time()

    settings = getSettings()

    if settings['dev_mode'] == True:
        log.log('\t... done! (using a cached copy)')
        return cache.readJson('matchmaking.json')

    if 'api_key' not in settings or 'steam' not in settings['api_key']:
        log.error('No Steam API key -- cannot retrieve CS:GO server status.')
        return {'status': 'UNKNOWN', 'url': 'down'}

    offline = {'status': 'OFFLINE', 'url': 'down'}
    online = {'status': 'ONLINE', 'url': 'up'}

    try:
        api_url = 'https://api.steampowered.com/ICSGOServers_730/GetGameServersStatus/v1/?key=%s'
        req = requests.get(api_url % settings['api_key']['steam'])
    except Exception as e:
        elapsedTime = '\BLUE(%s s)' % str(round(time() - startTime, 3))
        log.error('Could not retrieve CS:GO GC status. (%s) %s' % (str(e), elapsedTime), 1)
        return offline

    status = req.json()['result']['matchmaking']['scheduler']

    elapsedTime = '\BLUE(%s s)' % str(round(time() - startTime, 3))
    log.log('\t...done! %s' % elapsedTime)

    if status == 'offline':
        cache.saveJson('matchmaking.json', offline)
        return offline
    elif status == 'normal':
        cache.saveJson('matchmaking.json', online)
        return online
    else:
        return {'status': 'UNKNOWN (%s)' % status, 'url': 'down'}
