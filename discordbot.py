import discord
import requests
import json
import random
import yt_dlp
from discord.ext import commands
import asyncio

def get_meme():
    response = requests.get("https://meme-api.com/gimme")
    json_data = json.loads(response.text)
    return json_data["url"]

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True

bot = commands.Bot(command_prefix="$", intents=intents)
queue = []
is_paused = False
is_playing = False

@bot.event
async def on_ready():
    print(f"Logged on as {bot.user}!")

@bot.command()
async def hello(ctx):
    await ctx.send("How's your day?")

@bot.command()
async def noob(ctx):
    await ctx.send("Git gud")

@bot.command()
async def minecraft(ctx):
    responses = [
        "FLINT AND STEEL", "THIS IS A CRAFTING TABLE", "THE NETHER", "WATER BUCKET RELEASE",
        "AN ENDER PEARL", "I... AM STEVE", "CHICKEN JOCKEY", "AS A CHILD, I YEARNED FOR THE MINES"
    ]
    await ctx.send(random.choice(responses))

@bot.command()
async def meme(ctx):
    await ctx.send(get_meme())

@bot.command()
async def join(ctx):
    if ctx.author.voice:
        channel = ctx.author.voice.channel
        if ctx.guild.voice_client is None:
            try:
                await channel.connect()
                await ctx.send("Joining the voice channel.")
            except Exception as e:
                await ctx.send(f"Failed to join: {e}")
        else:
            await ctx.send("Already in a voice channel.")
    else:
        await ctx.send("You're not in a voice channel.")

@bot.command()
async def leave(ctx):
    if ctx.guild.voice_client:
        await ctx.guild.voice_client.disconnect()
        await ctx.send("Leaving the voice channel.")
    else:
        await ctx.send("I'm not in a voice channel.")

@bot.command()
async def play(ctx, *, search: str):
    global queue, is_paused, is_playing

    if not ctx.author.voice:
        await ctx.send("You are not in a voice channel.")
        return

    channel = ctx.author.voice.channel
    if ctx.voice_client is None:
        await channel.connect()

    ydl_opts = {
        "format": "bestaudio",
        "noplaylist": "True",
        "quiet": True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"ytsearch:{search}", download=False)["entries"][0]
            url = info["url"]
            title = info["title"]

        queue.append((title, url))
        await ctx.send(f"Added to queue: **{title}**")

        if not is_playing:
            await play_next(ctx)

    except Exception as e:
        await ctx.send(f"Error: {e}")

async def play_next(ctx):
    global queue, is_paused, is_playing

    if len(queue) == 0:
        is_playing = False
        await ctx.send("Queue is empty!")
        return

    is_playing = True
    title, url = queue.pop(0)

    def after_playing(error):
        if error:
            print(f"Playback error: {error}")
        fut = asyncio.run_coroutine_threadsafe(play_next(ctx), bot.loop)
        try:
            fut.result()
        except Exception as e:
            print(f"Error in after callback: {e}")

    audio_source = discord.FFmpegPCMAudio(
        url,
        executable="ffmpeg",
        before_options="-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
        options="-vn"
    )

    if ctx.voice_client:
        ctx.voice_client.stop()
        ctx.voice_client.play(audio_source, after=after_playing)
        await ctx.send(f"Now playing: **{title}**")
    else:
        await ctx.send("Not connected to a voice channel.")
        is_playing = False

@bot.command()
async def stop(ctx):
    global queue, is_playing
    if ctx.voice_client:
        ctx.voice_client.stop()
        queue.clear()
        is_playing = False
        await ctx.send("Music stopped and queue cleared.")

@bot.command()
async def pause(ctx):
    global is_paused
    if ctx.voice_client and not is_paused:
        ctx.voice_client.pause()
        is_paused = True
        await ctx.send("Music paused.")

@bot.command()
async def resume(ctx):
    global is_paused
    if ctx.voice_client and is_paused:
        ctx.voice_client.resume()
        is_paused = False
        await ctx.send("Music resumed.")

@bot.command()
async def skip(ctx):
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.stop()
        await ctx.send("Skipped to the next song.")

@bot.command()
async def rps(ctx, user_choice: str):
    choices = ["rock", "paper", "scissors"]
    user_choice = user_choice.lower()

    if user_choice not in choices:
        await ctx.send("Please choose either rock, paper or scissors, for example: $rps rock")
        return

    bot_choice = random.choice(choices)
    result = ""
    if user_choice == bot_choice:
        result = "It's a tie!"
    elif (
        (user_choice == "rock" and bot_choice == "scissors") or
        (user_choice == "scissors" and bot_choice == "paper") or
        (user_choice == "paper" and bot_choice == "rock")
    ):
        result = "You win!"
    else:
        result = "You lose!"

    await ctx.send(f"I chose **{bot_choice}**.\n{result}")

bot.run("")
