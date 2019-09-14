# System imports
from time import time
# Third-party imports
import cron
import praw
# Our imports
import cache
import community_metrics
import config
import csgo_matchmaking
import csgo_matchticker
import file_manager
import livestream_feed
import log
import notices
import stylesheet
import upcoming_events
# Fix SSL issues by using pyOpenSSL
import urllib3.contrib.pyopenssl
urllib3.contrib.pyopenssl.inject_into_urllib3()

settings = config.getSettings()
oAuthInfo = config.getOAuthInfo()

# Ensure the crontab frequencies exist and are in line with the settings
# Commented out for now because I don't want this enabled on my dev setup
# if settings['dev_mode'] == False:
#   cron.updateFrequency()

# Initialize our main PRAW Reddit object for authentication
r = praw.Reddit(client_id=oAuthInfo['GlobalOffensiveBot']['client_id'],
                client_secret=oAuthInfo['GlobalOffensiveBot']['client_secret'],
                username=oAuthInfo['GlobalOffensiveBot']['username'],
                password=oAuthInfo['GlobalOffensiveBot']['password'],
                user_agent=oAuthInfo['GlobalOffensiveBot']['user_agent'])

####################
#   SIDEBAR PHASE
####################

# Get the sidebar template
sidebar = config.getSidebarTemplate()

# Default values for the different sections of the sidebar
communityMetricsMd = ''
strafe_md = ''
livestreams = {'markdown': '', 'spritesheet_path': None}
upcomingEventsMd = ''
matchesMd = ''
noticesMd = ''
mm = {'status': '', 'url': ''}

strafe_settings = file_manager.readJson('strafe/settings.json')
if not strafe_settings['enabled']:
    sidebar = sidebar.replace('\n__LIVESCORETICKER__\n', '')
else:
    # Wait 10 seconds to make sure the strafe ticker has had
    # enough time to build the match list so we can grab the
    # latest version of the markdown.
    time.sleep(10)

# Get the different components of the sidebar, but only if there is something
# in the sidebar markdown for them to replace!
if '__DISCORDCOUNT__' in sidebar and settings['sidebar']['social']['discord_enabled']:
    discord_count = community_metrics.getDiscordUsersMarkdown()
if '__COMMUNITY_METRICS__' in sidebar:
    # if not settings['sidebar']['social']['ts_enabled'] and not settings['sidebar']['social']['irc_enabled']:
        # communityMetricsMd = ''
    # else:
        # 
    communityMetricsMd = community_metrics.buildMarkdown()
if '__LIVESCORETICKER__' in sidebar:
    strafe_md = file_manager.read('strafe/app-cache/finished_markdown.txt')
if '__LIVESTREAMS__' in sidebar:
    # Returns spritesheet path and markdown
    livestreams = livestream_feed.build()
if '__MATCHTICKER__' in sidebar:
    matchesMd = csgo_matchticker.buildMarkdown()
if '__UPCOMING_EVENTS__' in sidebar:
    upcomingEventsMd = upcoming_events.buildMarkdown()
if '__NOTICES__' in sidebar:
    noticesMd = notices.runAutoposterAndBuildMarkdown(r)
if '__MM_STATUS__' in sidebar or '__MM_STATUS_URL__' in sidebar:
    # Returns status string and url suffix
    mm = csgo_matchmaking.getStatus()

# Replace the placeholders with the retrieved values, or defaults if they
# were not retrieved
sidebar = (sidebar.replace('__COMMUNITY_METRICS__', communityMetricsMd)
                  .replace('__LIVESCORETICKER__', '[*Live Score Ticker*](#heading)\n\n{}'.format(strafe_md))
                  .replace('__LIVESTREAMS__', livestreams['markdown'])
                  .replace('__MATCHTICKER__', matchesMd)
                  .replace('__UPCOMING_EVENTS__', upcomingEventsMd)
                  .replace('__NOTICES__', noticesMd)
                  .replace('__MM_STATUS__', mm['status'])
                  .replace('__MM_STATUS_URL__', mm['url']))

#######################
#   STYLESHEET PHASE
#######################

# Prepares things like the demonyms, multiple headers, etc.
stylesheet = stylesheet.build(r)

# If using the new header cycle, go back and update the sidebar with the
# banner creator for the current header
if settings['stylesheet']['new_header_cycle']['enabled']:
    metadata = cache.getMetadata()
    creator = metadata['new_header_cycle']['creator']
    banner_by = '* [Banner by /u/{}](https://reddit.com/u/{})'.format(creator, creator)
    sidebar = sidebar.replace('__BANNER_CREATOR__', banner_by)
else:
    sidebar = sidebar.replace('__BANNER_CREATOR__', '')

######################
#   UPLOADING PHASE
######################

# Upload the new spritesheet if one was generated
if livestreams['spritesheet_path'] != None:
    startTime = time()
    log.log('> Uploading livestreams spritesheet...')
    try:
        r.subreddit(settings['subreddit']).stylesheet.upload(
            settings['sidebar']['livestreams']['spritesheet_name'],
            livestreams['spritesheet_path'])
    except praw.exceptions.APIException as e:
        print(e)
    log.log('\t\GREEN...done! \BLUE(%s s)\n' % str(round(time() - startTime, 3)))

# Get the PRAW subreddit object
subreddit = r.subreddit(settings['subreddit'])

# Upload the new sidebar markdown if it's any different
if cache.read('sidebar_markdown.txt') != sidebar:
    startTime = time()
    log.log('> Uploading sidebar markdown...')
    subreddit.mod.update(description=sidebar)
    cache.save('sidebar_markdown.txt', sidebar)
    log.log('\t\GREEN...done! \BLUE(%s s)\n' % str(round(time() - startTime, 3)))
else:
    log.log('Not uploading sidebar -- it hasn\'t changed!')

# Upload the new stylesheet
# (ALWAYS! Any image changes rely on this being uploaded)
if stylesheet != None:
    startTime = time()
    log.log('> Uploading stylesheet...')
    subreddit.stylesheet.update(stylesheet=stylesheet)
    cache.save('stylesheet.txt', stylesheet)
    log.log('\t\GREEN...done! \BLUE(%s s) \n\n' % str(round(time() - startTime, 3)))

# Update the metadata with the latest update time for the webpanel to know
# whether or not the bot is still running
metadata = cache.getMetadata()
metadata['last_update_completed'] = int(time())
cache.setMetadata(metadata)

####################
#   LOGGING PHASE
####################

# Signal that we're done so the log manager can take the HTML version of the
# log and send it to Mongo for webpanel usage
log.finish()
