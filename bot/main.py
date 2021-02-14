import os
import json
import discord
from time import sleep
from datetime import datetime
from discord.abc import GuildChannel
from discord.client import Client
from discord.guild import Guild
from dotenv import load_dotenv

load_dotenv()
botToken = os.getenv('DISCORD_TOKEN')
serverName = os.getenv('DISCORD_SERVER')
with open('meetings.json') as meetings_file:
    meetings = json.load(meetings_file)


def get_day_name(id: int):
    if id == 0:
        return 'monday'
    elif id == 1:
        return 'tuesday'
    elif id == 2:
        return 'wednesday'
    elif id == 3:
        return 'thursday'
    elif id == 4:
        return 'friday'
    elif id == 5:
        return 'saturday'
    elif id == 6:
        return 'sunday'
    return None


class CustomClient(Client):
    _members = []
    _server: Guild = None
    _generalChannel: GuildChannel = None

    async def on_ready(self):
        print(f'{self.user} is connected')
        for guild in self.guilds:
            if guild.name == serverName:
                self._server = guild
                print(f'...to {guild.name}(id: {guild.id})')

                for channel in self._server.channels:
                    if channel.name == 'general':
                        self._generalChannel = channel

                break

        self._members = self._server.members
        members = '\n - '.join([member.name for member in self._members])
        print(f'Guild Members:\n - {members}')

        await self._timed_events()

    async def on_member_join(self, member):
        print(f'{member.name} joined')
        self._members.append(member)

    async def _timed_events(self):
        while True:
            currentTime = datetime.utcnow()
            dayName = get_day_name(currentTime.weekday())
            if dayName in meetings:
                await self._process_work_day(dayName, currentTime)
                sleep(10)
            else:
                sleep(600)

    async def _process_work_day(self, dayName: str, currTime: datetime):
        events = [evnt for evnt in meetings[dayName] if evnt['hour'] == currTime.hour and
                  evnt['minute'] == currTime.minute and currTime.second <= 10]
        if len(events) > 0:
            print(f'Event started {currTime}')
            await self._send_tripple_message_to_general('Daily meeting started!')

    async def _send_tripple_message_to_general(self, message: str):
        await self._generalChannel.send(content=f'@everyone {message}')
        sleep(.5)
        await self._generalChannel.send(content=f'@everyone {message}')
        sleep(.5)
        await self._generalChannel.send(content=f'@everyone {message}')


try:
    myIntents = discord.Intents.default()
    myIntents.members = True
    myIntents.presences = False

    client = CustomClient(intents=myIntents)
    client.run(botToken)
except Exception as e:
    print(str(e))
