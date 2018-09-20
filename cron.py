# System includes
import os
import sys
# Third-party includes
from crontab import CronTab
# Project includes
from config import getSettings

def getJob(cron, name):
    jobHunt = cron.find_command(name)
    try:
        job = jobHunt.next()
    except StopIteration:
        job = None
    return job

# Reads the bot settings and ensures there is a cron job
# for the sidebar bot and it is set to the correct
# frequency. If it's already set and correct, this does nothing.
def updateFrequency():
    cron = CronTab(user=True)
    writeCron = False
    settings = getSettings()

    sidebarJob = getJob(cron, 'sidebar/main.py')
    # If the job exists, make sure the existing crontab matches
    # what the settings say it should be
    if sidebarJob:
        if sidebarJob.minute != '*/' + str(settings['sidebar']['update_interval_mins']):
            sidebarJob.minute.every(settings['sidebar']['update_interval_mins'])
            writeCron = True
    # If the job doesn't exist, create it with the settings given
    else:
        # This crontab entry will run the bot and redirect stderr and stdout to
        # an individual file for just this iteration as well as to the full
        # appended output log that can be `tail -f`'d
        base_path = os.path.dirname(os.path.abspath(sys.argv[0]))
        sidebarJob = cron.new(command='python ' + base_path \
            + '/main.py 2>&1 | tee ' + base_path \
            + '/logs/iterations/`date -u +\%s`.txt >> ' \
            + base_path + '/logs/output.txt',
            comment='GOB Sidebar module')
        sidebarJob.minute.every(settings['sidebar']['update_interval_mins'])
        writeCron = True

    # If changes were made, write them to the crontab
    if writeCron:
        cron.write()
