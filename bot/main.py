from asyncio import sleep
import os
import json
import discord
from datetime import datetime
from discord.abc import GuildChannel
from discord.client import Client
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
    _generalChannel: GuildChannel = None
    _generalVoiceChannel: GuildChannel = None

    async def on_ready(self):
        print(f'{self.user} is connected')
        for guild in self.guilds:
            if guild.name == serverName:
                print(f'...to {guild.name}(id: {guild.id})')

                for channel in guild.channels:
                    if channel.name == 'general' or channel.name == 'общее':
                        self._generalChannel = channel
                    elif channel.name == 'Daily':
                        self._generalVoiceChannel = channel
                break

        self._members = guild.members
        membersStr = '\n - '.join([member.name for member in self._members])
        print(f'Guild Members:\n - {membersStr}')

        self.loop.create_task(timed_events(self))

    async def on_member_join(self, member):
        print(f'{member.name} joined')
        self._members.append(member)

    async def on_member_remove(self, member):
        print(f'{member.name} removed')
        self._members.remove(member)

    async def on_message(self, message):
        if message.author == self.user:
            return

        msg_content: str = message.content
        if not msg_content.startswith('!'):
            return

        command: str = msg_content.removeprefix('!')
        data: str = 'Available commands:\n!daily\n!week\n!today\n!add\n!remove'
        if command == 'daily':
            data = await self._generalVoiceChannel.create_invite(reason='Please come to voice channel!', max_age='300')
            for member in self._members:
                if member.status == discord.Status.online or member.status == discord.Status.idle:
                    cnl = await member.create_dm()
                    await cnl.send(data)
            return
        elif command == 'week':
            data = meetings
            if len(data) == 0:
                data = 'No meetings today.'
        elif command == 'today':
            data = meetings[get_day_name(datetime.utcnow().weekday())]
            if len(data) == 0:
                data = 'No meetings today.'
        elif command.startswith('remove'):
            data = 'remove command usage:\n!remove [day] - removes all scheduled events for this day of the week'
            params: str = command.removeprefix('remove').lstrip()
            day = params.strip().lower()
            if day in meetings:
                meetings[day].clear()
                data = f'{day} events cleared!'
        elif command.startswith('add'):
            data = 'add command usage:\n!add [day] [time] [optional comment]\nexample: !schedule monday 13:30 Daily lunch meeting'
            params: str = command.removeprefix('add').lstrip()
            schedule_list = params.split()
            comment = ''
            length = len(schedule_list)
            if length > 2:
                comment = ' '.join(schedule_list[2:])
            if length > 1:
                timeList = schedule_list[1].split(':')
                if len(timeList) == 2:
                    day = schedule_list[0].lower()
                    try:
                        hour: int = int(timeList[0])
                        minute: int = int(timeList[1])
                    except ValueError as ve:
                        hour = -1
                        minute = -1

                    if day in meetings and hour in range(0, 23) and minute in range(0, 59):
                        data = f'Scheduled {day}: {hour}:{minute} - {comment}'
                        newEvent = {
                            'hour': hour,
                            'minute': minute,
                            'comment': comment
                        }
                        meetings[day].append(newEvent)
                else:
                    data = 'Incorrect time format. Please use hh:mm'

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


async def process_work_day(botClient: CustomClient, dayName: str, currTime: datetime):
    events = [evnt for evnt in meetings[dayName] if evnt['hour'] == currTime.hour and
              evnt['minute'] == currTime.minute and currTime.second <= 10]
    if len(events) > 0:
        print(f'Event started {currTime}')
        comment = 'no comments'
        if 'comment' in events[0]:
            comment = events[0]['comment']
        await botClient.SendToGeneral(text=f'@everyone Daily meeting started! ({comment})')
        await sleep(1)


def main():
    try:
        myIntents = discord.Intents.default()
        myIntents.members = True
        myIntents.presences = True

        client = CustomClient(intents=myIntents)
        client.run(botToken)
    except Exception as e:
        print(str(e))


if __name__ == '__main__':
    main()
