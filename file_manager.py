# System imports
import errno
import io
import json
import os
import sys
# Project imports
import log

##############################
#      BASIC OPERATIONS
##############################

# Saves string of text to a file
def save(path, data_str, mode='w'):
    path = ensureAbsPath(path)
    try:
        with io.open(path, mode, encoding='utf-8') as f:
            f.write(str(data_str))
    except IOError:
        # This block of code will run if the path points to a file in a
        # non-existant directory.  To fix this, create the necessary
        # director(y/ies) and call this function again to create the file.
        directory = os.path.dirname(path)
        if not os.path.isdir(directory):
            try:
                os.makedirs(directory)
            except OSError as oserr:
                pass
        if os.path.isdir(directory):
            return save(path, data_str, mode)
        else:
            log.error('Could not write to ' + path)
            return False
    else:
        return True

# Reads text from a file as a string and returns it
def read(path):
    path = ensureAbsPath(path)
    try:
        fileContents = ''
        with open(path, encoding='utf-8') as f:
            fileContents = f.read()
        return fileContents
    except IOError:
        log.error('Could not find or open file: ' + path)
        return False

# Deletes the file at the specified path. Cryptic, I know.
def delete(path):
    path = ensureAbsPath(path)
    try:
        os.remove(path)
    except OSError:
        log.error('Could not remove file: ' + path)
        return False
    else:
        return True

# If any relative paths are given, make them relative to the bot's working dir
def ensureAbsPath(path):
    botRootDir = os.path.dirname(os.path.abspath(sys.argv[0])) + '/'
    return path if os.path.isabs(path) else botRootDir + path

##############################
#         JSON FILES
##############################

# Converts object to JSON, then saves it to a file
def saveJson(path, data):
    return save(
        path,
        json.dumps(
            data,
            ensure_ascii=False,
            indent=4,
            separators=(',', ': ')
        )
    )

# Reads text from a file, converts it to JSON, and returns it
def readJson(path):
    f = read(path)
    if f:
        try:
            return json.loads(f)
        except ValueError:
            log.error('Could not parse JSON file: ' + path)
            return False
    else:
        return False

##############################
#      MISC HELPER FUNCS
##############################

# Appends data to a file rather than overwriting it -- useful for logging
def append(path, data):
    return save(path, data + '\n', 'a')

# Grabs the file contents and returns them, then deletes the file
# This is primarily used for the temporary logging mechanism
def readAndDelete(path):
    fileContents = read(path)
    delete(path)
    return fileContents
