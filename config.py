# System imports
from time import time
# Third-party imports
import yaml
import praw
# Project imports
import file_manager
import log

r = None
config_root = 'cfg/'        # Root of all configuration files
profile_root = 'profile/'   # Folder with profiles, relative to config_root
profile = None              # Name of target profile/the target profile folder
settings_root = ''          # Full path to profile folder relative to bot root 
last_updated = 0
cached_returns = {}         # Used to, well, cache function returns. Not wildly
                            # used in the configuration files, but a handy
                            # option nonetheless.
                            # TODO: Look into streamlining the caching process
authed_account = ''         # The current authenticated account

# Aliases of the file_manager functions to control the relative path
def read(relative_path):
    global config_path
    return file_manager.read(config_path + relative_path)

def readJson(relative_path):
    global config_path
    return file_manager.readJson(config_path + relative_path)

def save(relative_path, data):
    global config_path
    return file_manager.save(config_path + relative_path, data)

def saveJson(relative_path, data):
    global config_path
    return file_manager.saveJson(config_path + relative_path, data)

def getConfigPath():
    global config_path
    return file_manager.ensureAbsPath(config_path)

# Bot settings
def getSettings():
    global cached_returns
    global last_updated
    global config_root
    global config_path
    global r
    global profile

    # Only allow updating the settings once every couple minutes
    if 'settings' in cached_returns and time() - cached_returns['settings']['updated'] < 60 * 2:
        return cached_returns['settings']['return']

    profile_from_file = getProfile()

    # If the profile has changed since we last loaded up settings,
    # generate a new PRAW object just in case the credentials are out
    # of date
    if profile != profile_from_file:
        # Determine the new profile
        profile = profile_from_file
        # Update the config path to the current profile
        config_path = config_root + profile_root + profile + '/'

    settings = readJson('settings.json')

    # Get the OAuth information
    settings['bot'] = getOAuthInfo()

    if 'settings' not in cached_returns:
        cached_returns['settings'] = {}
    cached_returns['settings']['updated'] = time()
    cached_returns['settings']['return'] = settings

    return settings

# Grabs profile from profile.txt
def getProfile():
    global config_root

    if 'profile' in cached_returns and time() - cached_returns['profile']['updated'] > 60 * 2:
        return cached_returns['profile']['return']

    file_contents = file_manager.read(config_root + 'profile.txt')

    if file_contents == False:
        log.warning('No profile.txt file found, assuming default.')
        file_contents = 'default'
    else:
        file_contents = file_contents.strip()

    cached_returns['profile'] = {
        'updated': time(),
        'return': file_contents
    }

    return file_contents

# Bot account OAuth information // These don't follow the profile,
# keep all bots in the same accounts.json file
def getAccounts():
    global config_root
    return file_manager.readJson(config_root + 'accounts.json')

def setAccounts(newAccounts):
    global config_root
    file_manager.saveJson(config_root + 'accounts.json', newAccounts)

# The Reddit app OAuth info necessary for registering ourselves as legit
def getOAuthInfo():
    return readJson('oauth.json')

# Sidebar template
def getSidebarTemplate():
    settings = getSettings()
    if settings['use_wiki']:
        sidebar_template = getWikiPage(
            settings['primary_bot'],
            settings['subreddit'],
            'sidebar'
        )
        if sidebar_template != None:
            # Save the sidebar template from the wiki to the local file
            save('sidebar.txt', sidebar_template)
            return sidebar_template
    return read('sidebar.txt')

# Stylesheet
def getStylesheet():
    settings = getSettings()
    if settings['use_wiki']:
        stylesheet = getWikiPage(
            settings['primary_bot'],
            settings['subreddit'],
            'stylesheet'
        )
        if stylesheet != None:
            # Save the stylesheet from the wiki to the local file
            save('stylesheet.txt', stylesheet)
            return stylesheet
    return read('stylesheet.txt')

def getStylesheetHeader():
    settings = getSettings()
    if settings['use_wiki']:
        stylesheet_header = getWikiPage(
            settings['primary_bot'],
            settings['subreddit'],
            'stylesheet-header'
        )
        if stylesheet_header != None:
            # Save the stylesheet header from the wiki to the local file
            save('stylesheet_header.txt', stylesheet_header)
            return stylesheet_header
    return read('stylesheet_header.txt')
    

# Templates for various output
def getTemplates():
    settings = getSettings()
    if settings['use_wiki']:
        templates = getWikiPage(
            settings['primary_bot'],
            settings['subreddit'],
            'templates'
        )
        if templates != None:
            templates = parseYaml(templates)
            if templates != None:
                # Commit the wiki templates to the local file
                saveJson('templates.json', templates)
                return templates
    return readJson('templates.json')

# Header notice list
def getNotices():
    return readJson('notices.json')

# Iterates through the notices and updates them based on the unique ID
def setNotices(notices):
    oldNotices = getNotices()
    for oldNotice in oldNotices:
        for notice in notices:
            if oldNotice['unique_notice_id'] == notice['unique_notice_id']:
                oldNotice.update(notice)
    saveJson('notices.json', notices)

# Demonyms
def getDemonyms():
    settings = getSettings()
    if settings['use_wiki']:
        demonyms = getWikiPage(
            settings['primary_bot'],
            settings['subreddit'],
            'demonyms'
        )
        if demonyms != None:
            demonyms = parseYaml(demonyms)
            if demonyms != None:
                return demonyms
    return readJson('demonyms.json')

def setDemonyms(data):
    saveJson('demonyms.json', data)

# Iterates through the notices and updates them based on the unique ID
def saveNotices(notices):
    oldNotices = getNotices()
    for oldNotice in oldNotices:
        for notice in notices:
            if oldNotice['unique_notice_id'] == notice['unique_notice_id']:
                oldNotice.update(notice)
    saveJson('notices.json', notices)

# Converts YAML to a usable object
def parseYaml(text):
    try:
        obj = yaml.load(text)
    except yaml.YAMLError as e:
        log.error('Could not convert YAML to Python\n%s' % str(e))
        return None
    return obj
