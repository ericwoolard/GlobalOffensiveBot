# Project imports
import file_manager

cache_path = 'app-cache/'

def read(relative_path):
    global cache_path
    return file_manager.read(cache_path + relative_path)

def readJson(relative_path):
    global cache_path
    return file_manager.readJson(cache_path + relative_path)

def save(relative_path, data):
    global cache_path
    return file_manager.save(cache_path + relative_path, data)

def saveJson(relative_path, data):
    global cache_path
    return file_manager.saveJson(cache_path + relative_path, data)

# Metadata file management
def getMetadata():
    metadata = readJson('metadata.json')
    if not metadata:
        metadata = {
            "workshop_spotlight_cycle": {
                "current_index": 0,
                "last_updated": 0
            },
            "last_webpanel_restart": 0,
            "last_update_completed": 0,
            "demonym_cycle": {
                "current_index": 0,
                "last_updated": 0
            },
            "error_status": {
                "sidebar_length": {
                    "active": False,
                    "chars_over": 0
                },
                "stylesheet_length": {
                    "active": False,
                    "chars_over": 0
                }
            },
            "community_spotlight_cycle": {
                "current_index": 0,
                "last_updated": 0
            },
            "header_cycle": {
                "current_index": 0,
                "last_updated": 0
            },
            "new_header_cycle": {
                "last_updated": 0,
                "creator": "",
                "last_header": ""
            }
        }
        setMetadata(metadata)
    return metadata

# Overwrites the existing metadata with whatever data is given
# It's recommended that you just getMetadata(), alter that object, then
# use this function to re-set the metadata file with your changes
def setMetadata(data):
    saveJson('metadata.json', data)