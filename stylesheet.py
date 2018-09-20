# System imports
from time import time
from pathlib import Path
import json
import os
import sys
# Third-party imports
from cssmin import cssmin
import praw
import prawcore
# Project imports
import cache
import config
import log


# Returns the edited-as-necessary stylesheet
def build(r):
    settings = config.getSettings()
    # Get the base stylesheet
    if 'disable' in settings['stylesheet'] and settings['stylesheet']['disable']:
        return None
    stylesheet = config.getStylesheet()
    # Grab the "license" text
    header = config.getStylesheetHeader()
    # Handle the demonyms, if specified in the settings to do so
    if settings['stylesheet']['demonyms_enabled']:
        demonyms = getDemonymsCss()
    else:
        demonyms = ''
    # Handle the multiple-headers settings
    if settings['stylesheet']['num_of_headers'] > 1:
        stylesheet = stylesheet.replace('%%header1%%', getHeader())
    # Handle the new header cycle if enabled
    if settings['stylesheet']['new_header_cycle']['enabled']:
        getNextHeader(r)
    # Prepend the demonyms
    stylesheet = demonyms + "\n\n" + stylesheet
    # Handle the minify stylesheet setting without affecting the header
    if settings['stylesheet']['minify']:
        stylesheet = cssmin(stylesheet)
    # Add the header
    stylesheet = header + "\n\n" + stylesheet
    return stylesheet


# Returns a Reddit CSS name for the current header in the header cycle
def getHeader():
    metadata = cache.getMetadata()
    numOfHeaders = config.getSettings()['stylesheet']['num_of_headers']

    if metadata["header_cycle"]["current_index"] > numOfHeaders:
        metadata["header_cycle"]["current_index"] = 0
    if int(time()) - int(metadata["header_cycle"]["last_updated"]) > 60 * 60:
        # Grabs the new index for the active demonym
        metadata["header_cycle"]["current_index"] = (metadata["header_cycle"]["current_index"] + 1) % numOfHeaders
        metadata["header_cycle"]["last_updated"] = int(time())
        # Write the metadata object
    cache.setMetadata(metadata)
    # Returns the Reddit CSS %%variable%%
    return "%%header" + str(metadata["header_cycle"]["current_index"] + 1) + "%%"


# New header rotation method for cycling through many headers. Avoids the need 
# to have all headers pre-uploaded to the subreddit for the cycle to work. 
def getNextHeader(r):
    log.log('> New header cycle is \GREEN ENABLED')
    metadata = cache.getMetadata()
    settings = config.getSettings()
    interval_mins = settings['stylesheet']['new_header_cycle']['interval_mins']

    num_next_header = 0

    if int(time()) - metadata['new_header_cycle']['last_updated'] > (interval_mins * 60) - 120:
        log.log('\t Interval exceeded for current header...grabbing next header')
        last_header_name = metadata['new_header_cycle']['last_header']
        num_next_header = int(last_header_name.split('.')[0]) + 1
        next_header = Path('/var/www/globaloffensivebot/public/images/headers/{}.jpg'.format(str(num_next_header)))

        try:
            header_exists = next_header.resolve()
        except FileNotFoundError:
            num_next_header = 1
            next_header = '/var/www/globaloffensivebot/public/images/headers/{}.jpg'.format(str(num_next_header))

        with open('/var/www/globaloffensivebot/public/images/headers/creators/creators.json', 'r') as f: 
            creators = json.load(f)
        creator = creators[str(num_next_header)]
        
        try:
            r.subreddit(settings['subreddit']).stylesheet.upload('header', str(next_header))
            metadata['new_header_cycle']['last_updated'] = int(time())
            metadata['new_header_cycle']['last_header'] = '{}.jpg'.format(str(num_next_header))
            metadata['new_header_cycle']['creator'] = creator
            cache.setMetadata(metadata)
        except prawcore.TooLarge:
            log.error('\t\tError uploading {}.jpg by {}. Image too large.'.format(str(num_next_header), creator))
        except praw.exceptions.APIException as e:
            print(e)

        log.log('\t\t\GREEN...done! \R Now using header #{} by {}\n'.format(str(num_next_header), creator))
    else:
        current_num = metadata['new_header_cycle']['last_header'].split('.')[0]
        log.log('\t Not time to change the current header yet. Using header #{} by {}. Moving on...\n'.format(current_num, metadata['new_header_cycle']['creator']))

def getDemonymsCss():
    metadata = cache.getMetadata()
    demonyms = config.getDemonyms()
    # if it's been at least 30 minutes since the last update...
    if metadata["demonym_cycle"]["current_index"] > len(demonyms):
        metadata["demonym_cycle"]["current_index"] = 0
    if len(demonyms) == 0:
        demonyms = [{"subscribers":"subscribers","online":"users online"}]
        config.setDemonyms(demonyms)
    if int(time()) - int(metadata["demonym_cycle"]["last_updated"]) > 60 * 30:
        # Grabs the new index for the active demonym
        metadata["demonym_cycle"]["current_index"] = (metadata["demonym_cycle"]["current_index"] + 1) % len(demonyms)
        metadata["demonym_cycle"]["last_updated"] = int(time())
    cache.setMetadata(metadata)

    demonym = demonyms[metadata["demonym_cycle"]["current_index"]]

    usersOnline = demonym["online"].replace("\"", "''")
    subscribers = demonym["subscribers"].replace("\"", "''")

    demonymCss = (".subscribers .number:after, .res-nightmode .subscribers .number:after {\n"
           "\tcontent: \" " + subscribers + "\";\n"
           "}\n"
           ".users-online .number:after, .res-nightmode .users-online .number:after {\n"
           "\tcontent: \" " + usersOnline + "\";\n"
           "}")

    return demonymCss
