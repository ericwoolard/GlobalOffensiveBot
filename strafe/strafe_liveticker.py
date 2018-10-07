# System imports
from datetime import datetime
import logging
import os
import sys
import time
# Our imports
import Reddit
import Strafe
import Translations
from file_manager import read, save_json, save
import timeago

logging.basicConfig(format='%(asctime)s %(levelname)-8s %(message)s',
                    filename='{}/logging.log'.format(os.path.dirname(os.path.abspath(sys.argv[0]))),
                    level=logging.INFO,
                    datefmt='%Y-%m-%d %H:%M:%S')
strafe = Strafe.Strafe()
r = Reddit.Reddit()
translator = Translations.Translations()


def get_tournament():
    # Get current tournaments with default parameters.
    try:
        tournaments = strafe.get(first=False)
        if tournaments:
            tournament = strafe.get_top_active_tournament(tournaments)
            if tournament:
                get_live_matches(tournament)
            else:
                logging.info('Tournaments were found, but none active. Removing ticker...')
                """r.delete_widget()"""
        else:
            logging.info('No tournaments found from strafe.get()')
    except:
        logging.exception('{} - Error in get_tournaments!'.format(datetime.now().strftime('%Y-%m-%d %H:%M:%S')))


def get_live_matches(tournament, params=None):
    # Find the current live match if there is one
    if params is None:
        params = {
            'status': 'live',
            'sort': 'start_date'
        }
    tournament_id = tournament['id']
    live_matches = []
    matches_endpoint = '{}/{}/matches'.format(strafe.api_tournaments, tournament_id)
    try:
        # This response returns general data for the live match,
        # but does not include the scoreboard.
        live_matches = strafe.get(url=matches_endpoint, params=params, query_type='matches', first=False)
        if live_matches:
            # If more than one live match is found, take the first
            # TODO - Allow showing more than one live match
            # Save the live match data in an instance variable for easy reference
            strafe.live_matches = live_matches
            save_json('app-cache/live_matches.json', strafe.live_matches)
        else:
            logging.info('No live matches found from strafe.get()')
    except:
        logging.exception('{} - Error in get_live_matches!'.format(datetime.now().strftime('%Y-%m-%d %H:%M:%S')))

    if strafe.live_matches:
        num_live = len(strafe.live_matches)
        count = 0
        live_stats = []

        for match in strafe.live_matches:
            if count == num_live:
                break
            if 'id' in match:
                # If we found a live match, request the detailed match
                # stats such as score, map etc. and store separately.
                try:
                    live_stats.append(strafe.get_live_stats(strafe.live_matches[count]['id']))
                except:
                    logging.exception('{} - Error in get_live_stats!'.format(datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
                count += 1

        if live_stats:
            try:
                for stats in live_stats:
                    if len(stats) > 1:
                        # If the current live match is a BO2 or greater, live_stats will
                        # return a list of live_stats for each map of the series. This
                        # enumerates the list and grabs the index where 'status' == 'live'
                        live_index = next((index for (index, d) in enumerate(stats) if d['status'] == 'live'), None)
                        if live_index is not None:
                            strafe.live_match_stats.append(stats[live_index])  # Save the live stats data in an instance variable for easy reference
                        else:
                            # If Strafe marks the most recent live match as finished before the next
                            # map begins, keep displaying the most recent map stats until it begins.
                            count = 0
                            for index in stats:
                                if index['status'] == 'upcoming':
                                    break
                                count += 1
                            if count > 0:
                                strafe.live_match_stats.append(stats[count - 1])
                    else:
                        strafe.live_match_stats.append(stats[0])
                save_json('app-cache/live_match_stats.json', strafe.live_match_stats)  # Save a cached copy
            except:
                logging.exception('{} - Error getting live stats!'.format(datetime.now().strftime('%Y-%m-%d %H:%M:%S')))

    get_past_matches(tournament_id)


def get_past_matches(tournament_id, params=None):
    # Get matches that have recently finished, in desc order
    if params is None:
        params = {
            'status': 'finished',
            'sort': 'start_date'
        }
    matches_endpoint = '{}/{}/matches'.format(strafe.api_tournaments, tournament_id)
    try:
        past_matches = strafe.get(url=matches_endpoint, params=params, query_type='matches', all_pages=True, first=False)

        # Since we can only sort by start_date, reverse the resulting list
        # to give us a new list in descending order by start_date
        past_matches = list(reversed(past_matches))[:strafe.num_past_matches]

        if past_matches:
            # Remove any matches from the list if they
            # are more than 2 weeks old
            count = 0
            new_past_matches = past_matches.copy()
            for match in past_matches:
                start_date = time.mktime(datetime.strptime(match['start_date'].split('T')[0], "%Y-%m-%d").timetuple()) - ((60 * 60) * 6)
                if (time.time() - start_date) > (((60 * 60) * 24) * 14):
                    del new_past_matches[count]
                else:
                    count += 1
            past_matches = new_past_matches

        if past_matches:
            strafe.past_matches = past_matches  # Save the past matches data in an instance variable for easy reference
            save_json('app-cache/past_matches.json', past_matches)
        else:
            logging.info('No past matches found from strafe.get()')
    except:
        logging.exception('{} - Error in get_past_matches!'.format(datetime.now().strftime('%Y-%m-%d %H:%M:%S')))

    build_markdown()


def build_markdown():
    # Build the markdown in stages. Live matches first, then past matches
    markdown_template = ''
    if strafe.live_matches and strafe.live_match_stats:
        try:
            markdown_template = read('template/strafe_widget_md_template.txt')
            markdown_template = build_live_match(markdown_template)
            if strafe.past_matches:
                markdown_template = build_past_matches(markdown_template)
        except IOError:
            logging.exception('{} - IOError opening md template!'.format(datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
    elif strafe.past_matches:
        try:
            markdown_template = read('template/strafe_widget_md_nolive_template.txt')
            markdown_template = build_past_matches(markdown_template)
        except IOError:
            logging.exception('{} - IOError opening md template!'.format(datetime.now().strftime('%Y-%m-%d %H:%M:%S')))

    # If the markdown template isn't empty, save a copy
    # to our cache and begin the upload process
    if markdown_template != '' and strafe.past_matches:
        save('app-cache/finished_markdown.txt', markdown_template)
        r.widget_markdown = markdown_template
        upload_widget()


def build_live_match(template):
    live_stats = strafe.live_match_stats
    placeholder = r.live_placeholder
    count = 0
    md = ''
    for match in strafe.live_matches:
        team1 = team_name_formatter(match['home']['team']['name'])
        team2 = team_name_formatter(match['away']['team']['name'])

        # Replace all of our placeholders in the markdown
        # template with the relevant data for live matches
        md += (placeholder.replace('__TEAM1__', '[](#team-{})'.format(team1))
               .replace('__TEAM1SCORE__', '[{}](#score)'.format(live_stats[count]['score']['home']))
               .replace('__TEAM1WINS__', '[](#wins-{})'.format(match['score']['home']))
               .replace('__MAP1__', '[{0} {1}]({2}#map-{0})'.format(live_stats[count]['map']['name'].lower(),
                                                                    match['format']['short'].lower(),
                                                                    match['stream']['url']))
               .replace('__MAP1TYPE__', '[{}](#type)'.format(translator.translate(match['kind'])))
               .replace('__TEAM2SCORE__', '[{}](#score)'.format(live_stats[count]['score']['away']))
               .replace('__TEAM2WINS__', '[](#wins-{})'.format(match['score']['away']))
               .replace('__TEAM2__', '[](#team-{})'.format(team2))
               .replace('__MATCH1VIEWERS__', '[{:,} viewers](#liveviewers)'.format(match['stream']['viewers'])))
        count += 1
        if count < len(strafe.live_matches):
            md += '\n\n> >&nbsp;\n\n'
    template = template.replace('__LIVEMATCHES__', md)
    return template


def build_past_matches(template):
    count = 0
    md = ''
    # Loop through each match in the past matches and
    # insert the data into the markdown template
    for match in strafe.past_matches:
        if count == strafe.num_past_matches:
            break
        count += 1
        md += format_past_matches(match, count)

    template = template.replace('__PASTMATCHES__', md)
    return template


def format_past_matches(match, count):
    # Tuple holding the team number as presented in the markdown template
    # The count must be multiplied by 2, with the result (and the result -1)
    # being the team numbers. If count = 2, then 2 * 2 = 4, team nums become 3, 4.
    # Match 1 = 1, 2. Match 2 = 3, 4. Match 3 = 5, 6 etc.
    team2 = count * 2
    team_nums = (team2 - 1, team2)

    placeholders = r.past_placeholder.format(team_nums[0], count, team_nums[1])
    team1 = team_name_formatter(match['home']['team']['name'])
    team2 = team_name_formatter(match['away']['team']['name'])
    match_date = match['start_date'].split('+')[0].replace('T', ' ')

    md = (placeholders.replace('__PREVTEAM{}__'.format(team_nums[0]), '[](#team-{})'.format(team1))
          .replace('__PREVTEAM{}SCORE__'.format(team_nums[0]), '[{}](#score)'.format(match['score']['home']))
          .replace('__PREVMATCH{}DATE__'.format(count), '[{}](#date)'.format(timeago.format(match_date, datetime.utcnow())))
          .replace('__PREVMATCH{}TYPE__'.format(count), '[{}](#type)'.format(translator.translate(match['kind'])))
          .replace('__PREVTEAM{}SCORE__'.format(team_nums[1]), '[{}](#score)'.format(match['score']['away']))
          .replace('__PREVTEAM{}__'.format(team_nums[1]), '[](#team-{})'.format(team2)))

    if count < strafe.num_past_matches:
        md += '\n\n> >&nbsp;\n\n'
    return md


def team_name_formatter(team):
    team = team.lower()
    if team.startswith('the '):
        team = team.split(' ')[1]
    if team.startswith('team '):
        team = team.split('team ')[1]
    if '.' in team:
        team = team.split('.')[0]
    team = team.split(' ')[0]
    return team


def upload_widget():
    res = r.upload_widget()
    if res.status_code != 200:
        logging.exception('{} - Widget upload responded with HTTP {}'.format(datetime.now().strftime('%Y-%m-%d %H:%M:%S'), res.status_code))
        logging.info(res.text)


def start():
    if strafe.enabled:
        get_tournament()
    else:
        """r.delete_widget()"""
        logging.info('Widget currently disabled. Exiting...')


if __name__ == '__main__':
    start()
