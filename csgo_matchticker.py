# System imports
import datetime
import json
from time import time
# Third-party imports
import requests
# Project imports
import cache
from config import getSettings
import log

def prepareTournyTitle(title):
    return title[:15] + "..." if len(title) > 15 else title

def getMatchTime(startTime):
    # GosuGamers uses this datetime format
    format = "%Y-%m-%dT%H:%M:%S+00:00"
    now = datetime.datetime.utcnow()
    start = datetime.datetime.strptime(startTime, format)
    seconds = int((start - now).total_seconds())
    if seconds < 0:
        return "LIVE"
    # More than a day away...
    elif seconds > 60*60*24:
        if seconds < 60*60*24*10:  # If more than 10 days don't add decimal
            x=float("{0:.1f}".format(float(seconds) / (60*60*24)))
            x2=int(x)
            return str(x2+0.5 if x >= x2+0.5 else x2) + "d"
        else:
            return str(int(seconds / (60*60*24))) + "d"
    # More than an hour away...
    elif seconds > 60*60:
        if seconds < 60*60*10:  # If more than 10 hours don't add decimal
            x=float("{0:.1f}".format(float(seconds) / (60*60)))
            x2=int(x)
            return str(x2+0.5 if x >= x2+0.5 else x2) + "h"
        else:
            return str(int(seconds / (60*60))) + "h"
    # More than a minute away...
    elif seconds > 60:
        return str(int(seconds / 60)) + "m"
    # Less than a minute away...
    else:
        return str(int(seconds)) + "s"

# Uses the Google API to shorten URLs
def getShortUrl(longUrl):
    settings = getSettings()

    if 'api_key' not in settings or 'google' not in settings['api_key']:
        log.error('No Google API key -- cannot shorten URLs')
        return longUrl

    data = json.dumps({'longUrl': longUrl})
    headers = {'Content-Type': 'application/json'}
    endpoint = 'https://www.googleapis.com/urlshortener/v1/url?key=%s' % settings['api_key']['google']
    shortUrl = 'http://example.org/'
    try:
        req = requests.post(endpoint, data=data, headers=headers)
    except Exception as e:
        log.error('Could not shorten URL (%s)\n- %s' % (str(e), longUrl), 1)
        return longUrl
    try:
        shortUrl = req.json()['id']
    except Exception as e:
        log.error('Error parsing Google API JSON: %s' % str(e), 1)
        return longUrl
    return shortUrl

def buildMarkdown():
    log.log('> Beginning to build the matchticker...')
    startTime = time()
    
    settings = getSettings()

    if settings['dev_mode'] == True:
        log.log('\t...done! (using a cached copy)')
        return cache.read('matchticker.txt')

    if 'api_key' not in settings or 'gosugamers' not in settings['api_key']:
        log.error('No GosuGamers API key -- cannot build matchticker.')
        return ''

    # Get the stream information
    try:
        api_url = ''
        req = requests.get(api_url % settings['api_key']['gosugamers'])
    except requests.exceptions.RequestException as e:
        elapsedTime = '\BLUE(%s s)' % str(round(time() - startTime, 3))
        log.error('From GosuGamers API: %s %s' % (str(e), elapsedTime), 1)
        return ''
    if req.status_code == 403 or not req.ok or 'IP Address Not Allowed' in str(req.content):
        elapsedTime = '\BLUE(%s s)' % str(round(time() - startTime, 3))
        log.error('GosuGamers rejected our IP ' + elapsedTime, 1)
        return blankTicker(startTime)
    try:
        upcomingMatches = req.json()['matches']
    except Exception as e:
        elapsedTime = '\BLUE(%s s)' % str(round(time() - startTime, 3))
        log.error('Issue with GosuGamers API JSON: %s %s' % (str(e), elapsedTime), 1)
        return ''

    # Matches to display
    matches = []
    gamesToGrab = 0
    
    if len(upcomingMatches) == 0:
        return blankTicker(startTime)
        
    if len(upcomingMatches) < settings['sidebar']['matchticker']['max_shown']:
        gamesToGrab = len(upcomingMatches)
    else:
        gamesToGrab = settings['sidebar']['matchticker']['max_shown']
    for i in range(0, gamesToGrab):
        matches.append({
            'tourny': prepareTournyTitle(upcomingMatches[i]['tournament']['name']),
            'team1': {'name': str(upcomingMatches[i]['firstOpponent']['shortName']),
                      'cc': str(upcomingMatches[i]['firstOpponent']['country']['countryCode']).lower()},
            'team2': {'name': str(upcomingMatches[i]['secondOpponent']['shortName']),
                      'cc': str(upcomingMatches[i]['secondOpponent']['country']['countryCode']).lower()},
            'time': getMatchTime(upcomingMatches[i]['datetime']),
            'url': upcomingMatches[i]['pageUrl'],
            'is_live': bool(upcomingMatches[i]["isLive"])
        })
    # Build the markdown
    matchtickerMd = ''
    matchMdTemplate = ('>>>\n'
                       '[~~__TOURNY__~~\n'
                       '~~__TIME__~~\n'
                       '~~__TEAM1__~~\n'
                       '~~__TEAM2__~~](__URL__#info)\n'
                       '[ ](#lang-__LANG1__)\n'
                       '[ ](#lang-__LANG2__)\n\n'
                       '>>[](#separator)\n\n')
    matchtickerMd = '[*Match Ticker*](#heading)\n\n'
    i = 0
    for match in matches:
        matchMd = matchMdTemplate
        matchMd = (matchMd.replace('__TOURNY__', match['tourny'])
            .replace('__TIME__', match['time'])
            .replace('__TEAM1__', match['team1']['name'])
            .replace('__TEAM2__', match['team2']['name'])
            .replace('__LANG1__', match['team1']['cc'])
            .replace('__LANG2__', match['team2']['cc'])
            .replace('__URL__', match['url']))
        matchtickerMd += matchMd
        i += 1
    matchtickerMd += '>>**[See all](http://bit.ly/1xGEuiJ#button#slim)**'

    cache.save('matchticker.txt', matchtickerMd)

    characters = '\YELLOW(%d characters)' % len(matchtickerMd)
    elapsedTime = '\BLUE(%s s)' % str(round(time() - startTime, 3))
    log.log('\t\GREEN...done! %s %s \n' % (characters, elapsedTime))

    return matchtickerMd

def blankTicker(startTime):
    matches = []

    matches.append({
        'tourny': '?',
        'team1': {'name': 'No matches retrieved.',
                  'cc': ''},
        'team2': {'name': '',
                  'cc': ''},
        'time': '0',
        'url': 'http://bit.ly/1xGEuiJ#button#slim',
        'is_live': False
    })

    matchtickerMd = ''
    matchMdTemplate = ('>>>\n'
                       '[~~__TOURNY__~~\n'
                       '~~__TIME__~~\n'
                       '~~__TEAM1__~~\n'
                       '~~__TEAM2__~~](__URL__#info)\n'
                       '[ ](#lang-__LANG1__)\n'
                       '[ ](#lang-__LANG2__)\n\n'
                       '>>[](#separator)\n\n')
    matchtickerMd = '[*Match Ticker*](#heading)\n\n'

    i = 0
    for match in matches:
        matchMd = matchMdTemplate
        matchMd = (matchMd.replace('__TOURNY__', match['tourny'])
            .replace('__TIME__', match['time'])
            .replace('__TEAM1__', match['team1']['name'])
            .replace('__TEAM2__', match['team2']['name'])
            .replace('__LANG1__', match['team1']['cc'])
            .replace('__LANG2__', match['team2']['cc'])
            .replace('__URL__', match['url']))
        matchtickerMd += matchMd
        i += 1
    matchtickerMd += '>>**[See all](http://bit.ly/1xGEuiJ#button#slim)**'

    cache.save('matchticker.txt', matchtickerMd)

    elapsedTime = '\BLUE(%s s)' % str(round(time() - startTime, 3))
    log.log('\t...done! (%d characters) %s \n' % (len(matchtickerMd), elapsedTime))

    return matchtickerMd
