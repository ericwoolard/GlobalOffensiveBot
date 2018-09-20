from config import getAccounts, setAccounts
from time import time
import fileinput

# Returns the new r variable on success, None on failure
def login(r, username):
    accounts = getAccounts()
    if accounts == None:
        accounts = {}
    access_info = None
    if username not in accounts:
        import webbrowser
        # Currently this is all scopes
        # TODO: Narrow this list down to only what we need for the bot
        scope = [
            'creddits',
            'edit',
            'flair',
            'history',
            'identity',
            'modconfig',
            'modcontributors',
            'modflair',
            'modlog',
            'modothers',
            'modposts',
            'modself',
            'modwiki',
            'mysubreddits',
            'privatemessages',
            'read',
            'report',
            'save',
            'submit',
            'subscribe',
            'vote',
            'wikiedit',
            'wikiread'
        ]
        url = r.get_authorize_url('', ' '.join(scope), True)
        webbrowser.open(url)
        access_code = raw_input("Click \"Accept\" and enter the `code` parameter from the URL: ")
        access_info = r.get_access_information(access_code)
    elif accounts[username]['expires'] < time():
        access_info = r.refresh_access_information(accounts[username]['refresh_token'])
    else:
        access_info = r.set_access_credentials(set(accounts[username]['scope'].split()),
            accounts[username]['access_token'],
            accounts[username]['refresh_token'])
        return r
    accounts[username] = {
        'access_token': access_info['access_token'],
        'refresh_token': access_info['refresh_token'],
        'scope': ' '.join(access_info['scope']),
        'expires': int(time()) + 60 * 60
    }
    setAccounts(accounts)
    return r
