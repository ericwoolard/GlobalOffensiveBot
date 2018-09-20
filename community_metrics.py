# System imports
import json
import requests
from time import time
# Third-party imports
import ts3
import discord
# Project imports
import cache
from config import getSettings
import log
import discord_metrics

# Get the number of connected clients
def buildMarkdown():
    log.log('\n> Retrieving community metrics...')
    startTime = time()

    settings = getSettings()

    if settings['dev_mode'] == True:
        log.log('\t... done! (using a cached copy)')
        return cache.read('community_metrics.txt')

    teamspeakMd = getTeamspeakUsersMarkdown(settings)
    ircMd = getIrcUsersMarkdown(settings)
    disMd = getDiscordUsersMarkdown(settings)

    markdown = teamspeakMd + '\n' + ircMd + '\n' + disMd
    # markdown = teamspeakMd + '\n' + ircMd + '\n' + ' '
    cache.save('community_metrics.txt', markdown)

    elapsedTime = '\BLUE(%s s)' % str(round(time() - startTime, 3))
    log.log('\GREENDone retrieving community metrics. %s \n' % elapsedTime)

    return markdown

# Use the TeamSpeak ServerQuery API to check how many users there are on the
# specified TS3 server
def getTeamspeakUsersMarkdown(settings):
    log.log('\tGetting number of TeamSpeak users...')
    startTime = time()

    if 'teamspeak' not in settings['sidebar']:
        log.error('No TeamSpeak ServerQuery info -- cannot build TS3 metric.')
        return ''

    ipMissing = 'ip' not in settings['sidebar']['teamspeak']
    usernameMissing = 'username' not in settings['sidebar']['teamspeak']
    passwordMissing = 'password' not in settings['sidebar']['teamspeak']

    if ipMissing or usernameMissing or passwordMissing:
        log.error('Missing TeamSpeak information -- cannot build TS3 metric.')
        return ''

    try:
        with ts3.query.TS3Connection(settings['sidebar']['teamspeak']['ip']) as ts3conn:
            ts3conn.login(
                client_login_name=settings['sidebar']['teamspeak']['username'],
                client_login_password=settings['sidebar']['teamspeak']['password']
            )
            ts3conn.use(sid=1)
            numOfUsers = len(ts3conn.clientlist()) - 1
    except (OSError, Exception) as e:
        elapsedTime = '\BLUE(%s s)' % str(round(time() - startTime, 3))
        log.error('Error! {}'.format(e))
        return '1. [](http://www.teamspeak.com/invite/{}#ts3) N/A'.format(settings['sidebar']['teamspeak']['ip'])

    elapsedTime = '\BLUE(%s s)' % str(round(time() - startTime, 3))
    log.log('\t\t\GREEN...done! %s' % elapsedTime)
    return '1. [](http://www.teamspeak.com/invite/%s#ts3) %d users' % \
           (settings['sidebar']['teamspeak']['ip'], numOfUsers)

# Queries IRC user count API for the number of people on our IRC network
def getIrcUsersMarkdown(settings):
    log.log('\tGetting number of IRC users...')
    startTime = time()

    if 'api_key' not in settings or 'irc_counter' not in settings['api_key']:
        log.error('No IRC counter API key -- cannot build IRC counting metric')
        return '1. [](http://reddit.com/r/%s/w/irc#irc) N/A'

    # Get the API response
    try:
        apiResponseObj = requests.get('http:url/{}'.format(settings['api_key']['irc_counter']))
    except Exception as e:
        log.error('Could not retrieve IRC users.\nError message: %s' % str(e), 2)
        return '1. [](http://reddit.com/r/%s/w/irc#irc) N/A'

    # Convert the response from JSON to a usable object
    try:
        apiResponse = apiResponseObj.json()
    except ValueError:
        log.error('Could not convert IRC API JSON response to an object', 2)
        return '1. [](http://reddit.com/r/%s/w/irc#irc) N/A'

    elapsedTime = '\BLUE(%s s)' % str(round(time() - startTime, 3))
    log.log('\t\t\GREEN...done! %s' % elapsedTime)

    numOfUsers = 0

    # If the data we want exists, return it.  Otherwise, return -1.
    if 'data' in apiResponse:
        if len(apiResponse['data']) > 0:
            if 'clientsconnected' in apiResponse['data']:
                numOfUsers = apiResponse['data']['clientsconnected']
    if numOfUsers <= 0:
        return '1. [](http://reddit.com/r/%s/w/irc#irc) Error!'
    else:
        return '1. [](http://reddit.com/r/%s/w/irc#irc) %d users ' % \
               (settings['subreddit'], numOfUsers)


def getDiscordUsersMarkdown(settings):
    log.log('\tGetting number of Discord users...')
    startTime = time()
    
    try:
        totalOnline = discord_metrics.setup()
        cacheFile = cache.readJson('discordusers.json')
        cacheCount = cacheFile['users']

        elapsedTime = '\BLUE(%s s)' % str(round(time() - startTime, 3))
        log.log('\t\t\GREEN...done! %s' % elapsedTime)
        return '1. [](http://discord.gg/globaloffensive#discord) {} users'.format(str(cacheCount))
    except Exception as ex:
        elapsedTime = '\BLUE(%s s)' % str(round(time() - startTime, 3))
        log.error('\t\t{}'.format(ex))
        return '1. [](http://discord.gg/globaloffensive#discord)'
