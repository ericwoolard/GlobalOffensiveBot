# System imports
from datetime import datetime
import logging
import os
import sys
from time import time
# Third-party imports
from pymongo import MongoClient
# Project imports
import color
import config
import file_manager


# Prints the log message to console and saves it in two locations:
#   - The temporary HTML log file for this bot update iteration
#   - The temporary log file for this bot update iteration
def log(msg, indent=0):
    msg = indentString(msg, indent)
    file_manager.append('app-cache/log-html.txt', color.colorizeHtml(msg))
    # The rest of the files will take normal ASCII colors
    msg = color.colorize(msg)
    print(msg)  # This should be the only print statement in the entire bot

# TODO: For error and warning, strip any tabs before outputting to the log
# Prints the message in red text prepended by "ERROR: " and sends it to the log
def error(msg, indent=0):
    log(indentString(color.red('ERROR: ' + msg), indent))

# Prints the message in yellow text prepended by "WARNING: " and sends it to the log
def warning(msg, indent=0):
    log(indentString(color.yellow('WARNING: ' + msg), indent))

# Returns an indented string
def indentString(string, indent):
    return "\t" * indent + string.replace('\n', '\n' + indent * '\t')

# This is called when the current iteration is finished, indicating we need to
# take the HTML version of the log and send it to Mongo
def finish():
    settings = config.getSettings()

    if 'db' not in settings or 'mongo' not in settings['db']:
        return

    # Send the HTML version of the log to Mongo for webpanel access
    logContentsHtml = file_manager.readAndDelete('app-cache/log-html.txt')
    # Establish database connection
    client = MongoClient(
        settings['db']['mongo']['host'],
        settings['db']['mongo']['port']
    )
    db = client[settings['db']['mongo']['database']]
    db.authenticate(
        settings['db']['mongo']['username'],
        settings['db']['mongo']['password'],
        mechanism='SCRAM-SHA-1'
    )
    # Insert the log as a document, including a timestamp
    db['botlog'].insert_one({
        "body": logContentsHtml,
        "time_finished": str(int(time()))
    })
