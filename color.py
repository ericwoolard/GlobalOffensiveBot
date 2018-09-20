# List of ASCII escape colors
# Reference: http://ascii-table.com/ansi-escape-sequences.php

# Colors
BLACK		= '\033[30m'
RED			= '\033[31m'
GREEN		= '\033[32m'
YELLOW		= '\033[33m'
BLUE		= '\033[34m'
MAGENTA		= '\033[35m'
CYAN		= '\033[36m'
# Attributes
RESET 		= '\033[0m'
BOLD 		= '\033[1m'
UNDERLINE 	= '\033[4m'
BLINK 		= '\033[5m'

def color(s, color):
    return color + s + RESET

def black(s):
    return BLACK + s + RESET

def red(s):
    return RED + s + RESET

def green(s):
    return GREEN + s + RESET

def yellow(s):
    return YELLOW + s + RESET

def blue(s):
    return BLUE + s + RESET

def magenta(s):
    return MAGENTA + s + RESET

def cyan(s):
    return CYAN + s + RESET

# Replaces escape color aliases with actual escape codes
def colorize(string):
    string = string.replace('\BLACK', BLACK) \
                   .replace('\RED', RED) \
                   .replace('\GREEN', GREEN) \
                   .replace('\YELLOW', YELLOW) \
                   .replace('\BLUE', BLUE) \
                   .replace('\MAGENTA', MAGENTA) \
                   .replace('\CYAN', CYAN) \
                   .replace('\R', RESET)
    return string + RESET

# Returns a colorized string specifically for use in websites.
def colorizeHtml(string):
    template = '<span style="color:#%s">'
    string = string.replace('\BLACK', template % '2f3436') \
                   .replace('\RED', template % 'cc0000') \
                   .replace('\GREEN', template % '489a06') \
                   .replace('\YELLOW', template % 'c4a000') \
                   .replace('\BLUE', template % '3465a4') \
                   .replace('\MAGENTA', template % '75507b') \
                   .replace('\CYAN', template % '06989a') \
                   .replace('\R', '</span>')
    return string + (string.count('<span') - string.count('</span>')) * '</span>'