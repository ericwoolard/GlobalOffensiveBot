# System imports
from time import time
from datetime import datetime
import random
# Third-party imports
import praw
import prawcore
# Project imports
import config
import log

frequency = {
    'once':		0,
    'daily':	60 * 60 * 24,
    'weekly':	60 * 60 * 24 * 7,
    'biweekly':	60 * 60 * 24 * 7 * 2,
    'monthly':	60 * 60 * 24 * 7 * 4
}

# Used for formatting the date to be used for an post title (4th of February, 2nd of January, etc)
def formatTitleDate(title):
    now = datetime.datetime.now()
    month = now.strftime('%B')
    day = datetime.datetime.today().day
    year = datetime.datetime.today().year
    output = " (" + day + suffix + " of " + month + ", " + year + ")"

    if 4 <= day <= 20 or 24 <= day <= 30:
        suffix = "th"
    else:
        suffix = ["st", "nd", "rd"][day % 10 - 1]

    return output

# Returns whether or not the notice is live
def isNoticeLive(notice):
    # Preconditions
    if notice['hide_notice'] == True:
        return False
    if notice['permanent_notice'] == True:
        return True

    return isItemLive(
        notice['frequency'],
        notice['created'],
        notice['notice_start_time'],
        notice['notice_duration'] * 60 * 60
    )

# Returns whether or not the post is live
def isPostLive(notice):
    # Preconditions
    if notice['disable_posting'] == True or 'autopost' not in notice['type']:
        return False

    return isItemLive(
        notice['frequency'],
        notice['created'],
        notice['post_time'],
        notice['sticky_duration'] * 60 * 60
    )

# Returns whether or not the given item is "live" with the given criteria
def isItemLive(itemFrequency, created, triplet, duration):
    if itemFrequency == 'daily':
        timeSinceCreated = int(time()) - getStartOfDay(created)
    else:
        timeSinceCreated = int(time()) - getStartOfWeek(created)

    postTime = getTimeFromTriplet(triplet, itemFrequency)
    timeSincePostTime = timeSinceCreated

    if itemFrequency != 'once':
        timeSincePostTime = timeSinceCreated % frequency[itemFrequency]
    if postTime > 0:
        timeSincePostTime -= postTime

    if timeSincePostTime < 0 or timeSinceCreated < 0:
        return False

    return timeSincePostTime < duration and timeSincePostTime != 0

# Returns the post time relative to the beginning of the posting cycle
def getTimeFromTriplet(triplet, itemFrequency):
    postTime = triplet[0] * 60 * 60 * 24 + \
               triplet[1] * 60 * 60 + \
               triplet[2] * 60
    if itemFrequency == 'daily':
        # Remove the day element of the postTime
        postTime = postTime - triplet[0] * 60 * 60 * 24
    elif itemFrequency == 'biweekly':
        postTime += 60 * 60 * 24 * 7
    elif itemFrequency == 'monthly':
        postTime += 60 * 60 * 24 * 7 * 3
    return postTime

# Returns the UTC timestamp of the beginning of the week for the given time
def getStartOfWeek(time):
    weekData = datetime.utcfromtimestamp(time)
    day = weekData.weekday() * 60 * 60 * 24
    hour = weekData.hour * 60 * 60
    minute = weekData.minute * 60
    second = weekData.second
    return time - day - hour - minute - second

# Returns the UTC timestamp of the beginning of the day for the given time
def getStartOfDay(time):
    weekData = datetime.utcfromtimestamp(time)
    hour = weekData.hour * 60 * 60
    minute = weekData.minute * 60
    second = weekData.second
    return time - hour - minute - second

# Creates a post!
def createPostFromNotice(r, settings, notice):
    oAuthInfo = config.getOAuthInfo()
    account_switched = False

    # If the poster_account is csgocomnights, switch over to that account
    if notice['poster_account'] != settings['primary_bot']:
        pa = notice['poster_account']
        r = praw.Reddit(client_id=oAuthInfo[pa]['client_id'],
                        client_secret=oAuthInfo[pa]['client_secret'],
                        username=oAuthInfo[pa]['username'],
                        password=oAuthInfo[pa]['password'],
                        user_agent=oAuthInfo[pa]['user_agent'])
        account_switched = True

    log.log('\t\t\YELLOWSENDING POST: %s' % formatTitle(notice['thread_title']))
    post = None
    subreddit = settings['subreddit']
    if notice['self_post'] == True:
        post = r.subreddit(subreddit).submit(
            title=formatTitle(notice['thread_title']),
            selftext=notice['body'],
            send_replies=False
        )
    else:
        post = r.subreddit(subreddit).submit(
            title=formatTitle(notice['thread_title']),
            url=notice['thread_link'],
            send_replies=False
        )
    
    # If we switched accounts, make sure we switch back to the primary bot
    if account_switched:
        r = praw.Reddit(client_id=oAuthInfo['GlobalOffensiveBot']['client_id'],
                        client_secret=oAuthInfo['GlobalOffensiveBot']['client_secret'],
                        username=oAuthInfo['GlobalOffensiveBot']['username'],
                        password=oAuthInfo['GlobalOffensiveBot']['password'],
                        user_agent=oAuthInfo['GlobalOffensiveBot']['user_agent'])
    return post

# Functions to help with stickying/unstickying when necessary
def isPostStickied(r, post_id):
    try:
        post = r.submission(id=post_id)
    except prawcore.exceptions.NotFound:
        log.error('Could not find post: %s' % post_id, 2)
        return False
    else:
        return post.stickied

def stickyPost(r, post_id):
    try:
        post = r.submission(id=post_id)
    except prawcore.exceptions.NotFound:
        log.error('Could not find post: %s' % post_id, 2)
    else:
        log.log('\t\t\YELLOWStickying %s...' % post_id)
        try:
            post.mod.sticky()
        except prawcore.exceptions.Forbidden:
            log.error('Bot does not have permission to sticky the post')

def unstickyPost(r, post_id):
    try:
        post = r.submission(id=post_id)
    except prawcore.exceptions.NotFound:
        log.error('Could not find post: %s' % post_id, 2)
    else:
        log.log('\t\t\YELLOWUnstickying %s...' % post_id)
        try:
            post.mod.sticky(state=False)
        except prawcore.exceptions.Forbidden:
            log.error('Bot does not have permission to unsticky the post')

# Main function of the module -- runs the autoposter to see if anything needs
# to be posted or put up as a notice, then builds the necessary markdown and
# returns it.
def runAutoposterAndBuildMarkdown(r):
    notices = config.getNotices()
    settings = config.getSettings()

    noticesToBuild = []
    potentialStickies = []

    # Extra \n just to add some whitespace
    log.log('> Running the auto-poster and building notices...')
    startTime = time()

    for notice in notices:
        if notice['notice_title'] != 'Default Notice Title':
            log.log("\t\MAGENTAFor \"%s\"" % notice['notice_title'])
        else:
            log.log("\t\MAGENTAFor \"%s\"" % notice['thread_title'])

        live = '\GREENlive'
        notLive = '\REDnot live'

        postIsLive = isPostLive(notice)
        log.log('\t\tThe post is ' + (live if postIsLive else notLive) + '.')
        noticeIsLive = isNoticeLive(notice)
        log.log('\t\tThe notice is ' + (live if noticeIsLive else notLive) + '.')

        if noticeIsLive:
            noticesToBuild.append(notice)

        # Determine eligibility for being posted
        # --- Subtracting 60 sec from the last_posted time is to account for the fact that no
        # --- notices/threads are ever posted at *exactly* the scheduled time, because it takes a few
        # --- seconds to post at the least. Therefore, without shaving off 60 seconds (which is a very
        # --- generous 'buffer' for how long it may take to post any given recurring notice/thread),
        # --- the 'last_posted' time will increase by a few seconds each week, making a scheduled item
        # --- not go up until the next 5 min update interval, and continues increasing until 'Reset Timing'
        # --- is issued from the webpanel. This is really just a bandaid for now and should be rewritten.
        timeSinceLastPosted = (int(time()) - notice['last_posted']) - 60

        eligibleForPosting = timeSinceLastPosted > frequency[notice['frequency']]
        if notice['frequency'] == 'once' and notice['last_posted'] != 0:
            eligibleForPosting = False

        # Determine if it should be posted, and get its ID
        if eligibleForPosting and postIsLive:
            post = createPostFromNotice(r, settings, notice)
            notice['last_posted'] = int(time())
            notice['last_posted_id'] = post.id
            post_id = post.id
        else:
            post_id = notice['last_posted_id']

        # Handle stickies later when we can ensure we're on the primary bot acct
        if post_id != None and post_id != "":
            potentialStickies.append({
                'postIsLive': postIsLive,
                'id': post_id
            })

        log.log('')

    # Handle whether or not the posts should be stickied
    for potential in potentialStickies:
        stickied = isPostStickied(r, potential['id'])
        if stickied == False and potential['postIsLive']:
            stickyPost(r, potential['id'])
        elif stickied and potential['postIsLive'] == False:
            unstickyPost(r, potential['id'])

    # Write changes of the notices to the notices file
    config.saveNotices(notices)

    noticesMd = ''
    # Shuffle the notices if necessary
    if len(noticesToBuild) > 3:
        random.shuffle(noticesToBuild)
        noticesToBuild = noticesToBuild[:3]
    # Build the notices markdown string
    template = "1. [__TITLE__](__LINK__#__CATEGORY__)\n"
    for notice in noticesToBuild:
        if notice['type'] == 'autopost+notice':
            noticesMd += (template.replace('__TITLE__', formatTitle(notice['notice_title']))
                .replace('__LINK__', "http://redd.it/" + notice['last_posted_id'])
                .replace('__CATEGORY__', notice['category']))
        else:
            noticesMd += (template.replace('__TITLE__', formatTitle(notice['notice_title']))
                .replace('__LINK__', notice['notice_link'])
                .replace('__CATEGORY__', notice['category']))
    elapsedTime = '\BLUE(%s s)' % str(round(time() - startTime, 3))
    log.log('\GREENDone running the auto-poster and building notices! %s \n' % elapsedTime)

    # Return the markdown
    return noticesMd

# Replaces "variables" in the title string to actual values, allowing for more
# dynamic titles.
def formatTitle(title):
    now = datetime.now()
    # Month
    title = title.replace("%%month%%", now.strftime("%B"))
    # Day of month
    day = now.strftime("%d").lstrip('0')
    title = title.replace("%%day%%", day)
    # Ordinal Number in day of month
    day_on = getOrdinalNumber(day)
    title = title.replace("%%day_on%%", day_on)
    # Year
    title = title.replace("%%year%%", now.strftime("%Y"))
    return title

# Converts a number to its ordinal number,
# e.g. "32" would yield "32nd", "31" would yield "31st" etc.
suffixes = {1: 'st', 2: 'nd', 3: 'rd'}
def getOrdinalNumber(num):
    num = int(float(num))
    suffix = ''
    if 10 <= num % 100 <= 20:
        suffix = 'th'
    else:
        suffix = suffixes.get(num % 10, 'th')
    return str(num) + suffix
