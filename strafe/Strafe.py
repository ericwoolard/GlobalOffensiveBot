# System imports
import requests
import requests.auth
import json
import time
from datetime import datetime, timedelta, date
from pprint import pprint
# Our imports
from file_manager import read_json, save_json

config = read_json('settings.json')


class Strafe:
    def __init__(self,
                 min_prize_pool=config['strafe']['min_prize_pool'],
                 enabled=None,
                 allow_online=None,
                 auto_remove=None):
        if enabled is None:
            self.enabled = config['enabled']
        elif isinstance(enabled, bool):
            self.enabled = enabled

        if allow_online is None:
            self.allow_online = config['allow_online']
        elif isinstance(allow_online, bool):
            self.allow_online = allow_online

        if auto_remove is None:
            self.auto_remove = config['auto_remove']
        elif isinstance(auto_remove, bool):
            self.auto_remove = auto_remove

        self._api_key = config['strafe']['api_key']
        self.api_tournaments = ''
        self.api_match = ''
        self.game = 1
        self.min_prize_pool = min_prize_pool
        self.num_past_matches = config['strafe']['num_past_matches']
        self.header = {'Authorization': 'Bearer {}'.format(self._api_key)}
        self._tournament_name = config['tournament_name']
        self.live_matches = []
        self.live_match_stats = []
        self.past_matches = []

    @property
    def tournament_name(self):
        return self._tournament_name

    @tournament_name.setter
    def tournament_name(self, name):
        self._tournament_name = name
        config['tournament_name'] = name
        save_json('settings.json', config)

    def get(self,
            before=None,
            after=None,
            url=None,
            params=None,
            header=None,
            query_type='tournament',
            all_pages=False,
            first=True):
        """
        Get the current tournament with a prize pool equal to or
        greater than self.min_prize_pool

        Parameters
        ----------
        before : date
            Date object formatted to YYYY-MM-DD, the date a tournament must start before
        after : date
            Date object formatted to YYYY-MM-DD, the date a tournament must end after
        url : string
            URL to send the request
        params : dict
            Dictionary of query string parameters
        header : dict
            Dictionary of headers to send with the request
        query_type : string
            Either 'tournament' or 'matches'
        all_pages : bool
            If true, returns all additional pages in the response
        first : bool
            If multiple tournaments matching the minimum prize pool are found, only return the first

        Returns
        -------
        response : list
            JSON formatted list of the response
        """
        if before is None or after is None:
            # Strafe API needs date strings formatted as
            # YYYY-MM-DD in order to query by date
            if not before:
                before = date.today() + timedelta(days=1)  # add 1 extra day to include tournaments that start today
            if not after:
                after = date.today()
        if url is None:
            url = self.api_tournaments
        if params is None:
            # Default params to send with the request. Used for
            # the initial tournaments request, otherwise, override.
            params = {
                'game': self.game,
                'start_before': str(before),
                'end_after': str(after)
            }
        if header is None:
            header = self.header

        # Strafe API paginates responses for matches, so we need to loop
        # through them by requesting each page one by one until we reach
        # an empty page, and build a unified list of each match when done.
        if all_pages and query_type == 'matches':
            last_page = False
            params['page'] = 1
            response = []
            while not last_page:
                page_response = requests.get(url, params=params, headers=header).json()
                if len(page_response) == 0:
                    last_page = True
                else:
                    response += page_response
                    params['page'] += 1
            return response

        response = requests.get(url, params=params, headers=header).json()

        if query_type == 'tournament':
            # Sort the tournaments in desc order by prize pool
            response = [d for d in response if d['prize_pool']['amount'] >= self.min_prize_pool]

        if first and len(response) > 1:
            return response[0]
        return response

    def get_live_stats(self, match_id):
        """
        Get detailed match stats for the current live game

        Parameters
        ----------
        match_id : int
            ID of the live match

        Returns
        -------
        response : list
            JSON formatted list of the response
        """
        endpoint = '{}/{}/games'.format(self.api_match, match_id)
        response = requests.get(url=endpoint, headers=self.header).json()
        return response

    def get_top_active_tournament(self, tournaments):
        """
        Find the active tournament with the highest prize pool

        Strafe API includes extremely broad start/end dates for tournaments,
        which do not always mean the tournament is currently live, so we
        must determine that here.

        If self.auto_remove is false, it will ignore whether or not the
        tournament is on an off day and continue returning past matches until
        reaching the end of the tournament. If set to true and the current
        day doesn't have any matches, it will see it as inactive and will
        remove the widget from the sub until it finds matches again.

        Parameters
        ----------
        tournaments : list
            List of tournaments meeting the start_before and end_after date params

        Returns
        -------
        tournament : list
            A single, currently live tournament with the highest prize pool
        None: None
            If no tournaments meeting the criteria are found
        """
        curr_time = time.time()
        if self.tournament_name != '':
            for tournament in tournaments:
                if tournament['name'] == self.tournament_name:
                    return tournament
            # If the saved tournament name is no longer in the list, clear
            # the name from our instance variable so we can grab the next.
            self.tournament_name = ''

        if self.tournament_name == '':
            count = 0
            for tournament in tournaments:
                for stage in tournament['stages']:
                    if stage['venue']['location'].lower() == 'online' and not self.allow_online:
                        continue

                    # start_date - adjust for server tz diff from UTC
                    # end_date - add 24 hours so we get the end rather than start of day
                    start_date = time.mktime(datetime.strptime(stage['start_date'], "%Y-%m-%d").timetuple()) - ((60 * 60) * 6)
                    end_date = time.mktime(datetime.strptime(stage['end_date'], "%Y-%m-%d").timetuple()) + ((60 * 60) * 24)
                    if start_date < curr_time < end_date:
                        self.tournament_name = tournament['name']
                        return tournaments[count]

                count += 1
            return None
