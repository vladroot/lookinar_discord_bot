from asyncio import sleep
import os
import json
import discord
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

        self.loop.create_task(timed_events(self))

    async def on_member_join(self, member):
        print(f'{member.name} joined')
        self._members.append(member)

    async def on_message(self, message):
        if message.author == self.user:
            return

        msg_content: str = message.content
        if not msg_content.startswith('!'):
            return

        command: str = msg_content.removeprefix('!')
        data: str = ''
        if command == 'week':
            data = meetings
            if len(data) == 0:
                data = 'No meetings today.'
        elif command == 'today':
            data = meetings[get_day_name(datetime.utcnow().weekday())]
            if len(data) == 0:
                data = 'No meetings today.'
        elif command.startswith('schedule'):
            to_add: str = command.removeprefix('schedule').lstrip()
            print(str)
        else:
            data = 'I don\'t know this trick :('
        await message.channel.send(data)

    async def SendToGeneral(self, text: str):
        await self._generalChannel.send(text)


async def timed_events(botClient: CustomClient):
    while True:
        currentTime = datetime.utcnow()
        dayName = get_day_name(currentTime.weekday())
        if dayName in meetings:
            await process_work_day(botClient, dayName, currentTime)
            await sleep(10)
        else:
            await sleep(600)


async def process_work_day(botClient: CustomClient, dayName: str, currTime: datetime):
    events = [evnt for evnt in meetings[dayName] if evnt['hour'] == currTime.hour and
              evnt['minute'] == currTime.minute and currTime.second <= 10]
    if len(events) > 0:
        print(f'Event started {currTime}')
        await botClient.SendToGeneral(content=f'@everyone Daily meeting started!')
        sleep(1)


try:
    myIntents = discord.Intents.default()
    myIntents.members = True
    myIntents.presences = True

    client = CustomClient(intents=myIntents)
    client.run(botToken)
except Exception as e:
    print(str(e))
