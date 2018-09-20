import discord
import time
import io
import json
import os
import sys

client = discord.Client()

def setup():
    client.loop.create_task(get_users())
    client.run('')


async def get_users():

    online = 0
    idle = 0
    offline = 0

    await client.wait_until_ready()
    startTime = time.time()
    while not client.is_closed:
        for server in client.servers:
            for member in server.members:
                if str(member.status) == 'online':
                    online += 1
                elif str(member.status) == 'idle':
                    idle += 1

        await client.close()

    totalUsers = online + idle
    updateJson('app-cache/discordusers.json', totalUsers)


def returnCount(total):
    print('Total is {}'.format(str(total)))
    updateJson('app-cache/discordusers.json', total)
    return str(total)


def updateJson(path, new_id):
    newPath = ensureAbsPath(path)
    with open(newPath, 'r') as f:
        data = json.load(f)  # Load json data into the buffer

    tmp = data['users']
    data['users'] = new_id

    with open(newPath, 'w+') as f:
        f.write(json.dumps(data))  # Write the new user count to the cache


def ensureAbsPath(path):
    botRootDir = os.path.dirname(os.path.abspath(sys.argv[0])) + '/'
    return path if os.path.isabs(path) else botRootDir + path
