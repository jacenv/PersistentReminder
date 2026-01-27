import discord
from discord.ext import commands, tasks
import datetime
import os
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

# Setup intents to read messages and members in the server
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# Create a hashmap to store reminders that i give it
reminders = {}

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')
    nag_loop.start() # Start the background timer

@bot.command()
async def remind(ctx, interval_minutes: int, *, task: str):
    """Sets a reminder. Usage: !remind 60 1 leetcode problem"""
    user_id = ctx.author.id
    
    reminders[user_id] = {
        "task": task,
        "interval": interval_minutes,
        "last_notified": datetime.datetime.now(),
        "channel_id": ctx.channel.id
    }
    
    await ctx.send(f"✅ I'll remind you to **'{task}'** every {interval_minutes} minutes until you type `!done`.")

@bot.command()
async def done(ctx):
    """Stops the reminder."""
    if ctx.author.id in reminders:
        task_name = reminders[ctx.author.id]['task']
        del reminders[ctx.author.id]
        await ctx.send(f"Great job! I've stopped the reminders for: **{task_name}**")
    else:
        await ctx.send("You don't have any active reminders!")

# Create a check that checks to see each minute if YOU have finished the task XD
@tasks.loop(seconds=60) # Checks every minute
async def nag_loop():
    now = datetime.datetime.now()
    
    for user_id, data in list(reminders.items()):
        # Calculate time difference
        elapsed = (now - data['last_notified']).total_seconds() / 60
        
        if elapsed >= data['interval']:
            channel = bot.get_channel(data['channel_id'])
            if channel:
                await channel.send(f"🔔 <@{user_id}>, have you finished: **{data['task']}**? (Type `!done` to stop)")
                # Update last notified time
                reminders[user_id]['last_notified'] = now

bot.run(TOKEN)
