from __future__ import print_function
import httplib2
import os

from apiclient import discovery
import oauth2client
from oauth2client import client
from oauth2client import tools

import datetime

from config import getSettings, getConfigPath
import log

try:
    import argparse
    flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
except ImportError:
    flags = None

# If modifying these scopes, delete your previously saved credentials
# at ~/.credentials/calendar-python-quickstart.json
SCOPES = 'https://www.googleapis.com/auth/calendar.readonly'

def buildMarkdown():
    log.log("> Building calendar...")
    settings = getSettings()
    events = getEvents(settings['sidebar']['calendar'])

    if len(events) == 0:
        return ''

    markdown = '[*Upcoming Events*](#heading)\n\n. | .\n---|---\n'
    for event in events:
        date = datetime.datetime.strptime(event['start']['date'], '%Y-%m-%d')
        link = event['htmlLink']
        markdown += date.strftime('%b **%-d**') + ' | ' + '[{}]'.format(event['summary']) + '({})'.format(link) + '\n'
    
    markdown += '\n**[See all](http://goo.gl/q9iOZb#button#slim)**'

    return markdown


def getCredentials(userAgent):
    credential_path = os.path.join(getConfigPath(), 'calendar_creds.json')

    store = oauth2client.file.Storage(credential_path)
    credentials = store.get()
    if not credentials or credentials.invalid:
        flow = client.flow_from_clientsecrets(os.path.join(getConfigPath(), 'calendar_client_secret.json'), SCOPES)
        flow.user_agent = userAgent
        if flags:
            credentials = tools.run_flow(flow, store, flags)
        else:  # Needed only for compatibility with Python 2.6
            credentials = tools.run(flow, store)
        print('Storing credentials to ' + credential_path)
    return credentials

def getEvents(calSettings):
    credentials = getCredentials(calSettings['app_name'])
    http = credentials.authorize(httplib2.Http())
    service = discovery.build('calendar', 'v3', http=http)

    now = datetime.datetime.utcnow().isoformat() + 'Z'  # 'Z' indicates UTC time
    print('\tGetting upcoming %s events...' % str(calSettings['num_of_events']))
    eventsResult = service.events().list(
        calendarId=calSettings['id'], timeMin=now, maxResults=calSettings['num_of_events'], singleEvents=True,
        orderBy='startTime').execute()
    events = eventsResult.get('items', [])

    if not events:
        log.log('\tNo upcoming events found.')
    else:
        log.log('\t\GREENFound ' + str(len(events)) + ' events! \n')

    return events

if __name__ == '__main__':
    buildMarkdown()
