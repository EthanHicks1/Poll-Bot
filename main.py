import asyncio
from collections import Counter
import json
import logging
import aiohttp
import discord
from discord.ext import commands
import strawpoll
import config
import requests

#logging
logging.basicConfig(level=logging.INFO)


bot = commands.AutoShardedBot(command_prefix='+')

#Removes default help command
bot.remove_command("help")

async def send_stats():
    tokens = (
        ('https://discordbots.org/api/bots/%s/stats', config.orgtoken),
        ('https://bots.discord.pw/api/bots/%s/stats', config.pwtoken),
    )
    payload = {'server_count': len(bot.guilds)}
    for url, token in tokens:
        headers = {'Authorization': token}
        await bot.http_session.post(url % bot.user.id, json=payload, headers=headers)

#Log in
@bot.event
async def on_ready():
    await bot.change_presence(game=discord.Game(name='+help', type=0))
    bot.http_session = aiohttp.ClientSession()
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('--------')
    bot.app = await bot.application_info()
    owner = bot.app.owner
    while True:
        guilds = 'guilds: ' + str(len(bot.guilds))
        users = 'users: ' + str(len(list(bot.get_all_members())))
        uniques = 'unique users: ' + str(len(discord.utils._unique(bot.get_all_members())))
        await owner.send(guilds)
        await owner.send(users)
        await owner.send(uniques)
        await owner.send('type +!more for deeper analytics')
        await send_stats()
        print(owner)
        await asyncio.sleep(86400)

@bot.event
async def on_guild_join(guild):
    print("New guild!")
    await send_stats()
    print("Stats updated.")

@bot.event
async def on_guild_remove(guild):
    print("Guild left :(")
    await send_stats()
    print("Stats updated.")

@bot.command(name='!upvoters')
async def upvoters(ctx):
    channel = bot.get_channel(396182828422922241)
    print(ctx.message.channel.id)
    await channel.send("worked")
    headers = {'Authorization': config.orgtoken}
    async with bot.http_session.get('https://discordbots.org/api/bots/%s/votes' % bot.user.id, headers=headers) as resp:
        upvoters = await resp.json()
    upvoter_names = [upvoter['username'] for upvoter in upvoters]
    await channel.send('upvoters: ' + ', '.join(upvoter_names))

#Sends analytics to a channel in the Poll Bot server
@bot.command(name='!stats', pass_context=True)
async def srvrs(ctx):
    chnl = bot.get_channel(396183943910522880)
    srvr = bot.get_guild(300487910619217921)
    bot.app = await bot.application_info()
    guilds = 'guilds: ' + str(len(bot.guilds))
    users = 'users: ' + str(len(list(bot.get_all_members())))
    uniques = 'unique users: ' + str(len(discord.utils._unique(bot.get_all_members())))
    await chnl.send(guilds)
    await chnl.send(users)
    await chnl.send(uniques)
    await chnl.send("server members: " + str(srvr.member_count))
    await chnl.send('type +!mas for deeper analytics')

#Help Command
@bot.command(name='help', pass_context=True)
async def hlp(ctx):
    emb1 = discord.Embed(description="**Reaction Poll**\nCreate a reaction poll by typing '+poll *your message*’. Poll Bot will automatically add the reactions 👍, 👎, and 🤷.\n\n**Strawpoll**\nCreate a strawpoll by typing '+strawpoll {title} [Option1] [Option2] [Option 3]', with up to 30 options.\n\n**Other Commands**\n+updates, +invite, +donate\n\n**Still Have Questions?**\nJoin our official discord server: <https://discord.gg/FhT6nUn>" + "\n" + "Ask us on twitter: <https://twitter.com/DiscordPollBot>", colour=0x83bae3)
    await ctx.author.send(embed=emb1)
    await ctx.message.channel.send('Check your DMs!')

#To pay for hosting
@bot.command(name='donate', pass_context=True)
async def hlp(ctx):
    emb1 = discord.Embed(title='Support', description="We currently don't need donations, but it would be nice if you could upvote Poll Bot here: https://discordbots.org/bot/298673420181438465/vote (and get the upvoter role on the Poll Bot discord server: https://discord.gg/FhT6nUn)", color=0x83bae3)
    await ctx.message.channel.send(embed=emb1)

#Invite link (if people want to add Poll Bot to their own server)
@bot.command(name='invite', pass_context=True)
async def info(ctx):
    emb1 = discord.Embed(description='Invite Poll Bot to your server: <https://discordapp.com/oauth2/authorize?client_id=298673420181438465&scope=bot&permissions=0>', colour=0x83bae3)
    await ctx.message.channel.send(embed=emb1)

#Where the latest updates get put
@bot.command(name='updates', pass_context=True)
async def updts(ctx):
    emb1 = discord.Embed(description="**Please join the Poll Bot server and see #announcements to see the latest updates! <https://discord.gg/FhT6nUn>**\n\n_**Don't forget you can use all of Poll Bot's features within direct messages. Just open a direct message with Poll Bot and use it like you would normally.**_")

    await ctx.message.channel.send(embed=emb1)

#Reaction Poll
@bot.command(name="poll", pass_context=True)
async def poll(ctx):
    await ctx.message.add_reaction('👍')
    await ctx.message.add_reaction('👎')
    await ctx.message.add_reaction('🤷')

#Reaction Poll with 2 options
@bot.command(name="poll2", pass_context=True)
async def poll(ctx):
    await ctx.message.add_reaction('👍')
    await ctx.message.add_reaction('👎')

@bot.command(name="retrying", pass_context=True)


#Strawpoll
@bot.event
async def on_message(message):
    command_name = bot.command_prefix + 'strawpoll'
    messageContent = message.content
    if message.content.startswith(command_name):
        pollURL = await createStrawpoll(messageContent)
        await message.channel.send(pollURL)
    else:
        await bot.process_commands(message)

async def createStrawpoll(message):
    #gets the title of the poll
    first = message.find("{") + 1
    second = message.find("}")
    title = message[first:second]

    #gets the # of options and assigns them to an array
    newMessage = message[second:]
    loopTime = 0

    option = []
    for options in message:
        #get from } [option 1]
        #if newThis == -1:
        stillOptions = newMessage.find("[")
        if stillOptions != -1:
            if loopTime == 0:
                first = newMessage.find("[") + 1

                second = newMessage.find("]")
                second1 = second + 1
                option.append(newMessage[first:second])

                loopTime+=1
            else:
                newMessage = newMessage[second1:]
                first = newMessage.find("[") + 1
                second = newMessage.find("]")
                second1 = second + 1
                option.append(newMessage[first:second])
                loopTime+=1
    strawpollAPI = strawpoll.API()
    try:
        r = requests.post('https://www.strawpoll.me/api/v2/polls', json = {"title": title, "options": option[:(len(option)-1)], "multi": "true"}, headers={"Content Type": "application/json"})
        json = r.json()
        return "https://strawpoll.me/" + str(json["id"])


    except strawpoll.errors.HTTPException:
        return "Please make sure you are using the format '+strawpoll {title} [Option1] [Option2] [Option 3]'"

    except KeyError:
        return "Please make sure you are using the format '+strawpoll {title} [Option1] [Option2] [Option 3]'"


if __name__ == '__main__':
    bot.run(config.discordToken)
