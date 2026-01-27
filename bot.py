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

reminders = {}

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')
    nag_loop.start() # Start the background timer

@bot.command()
async def remind(ctx, interval_minutes: int, *, task: str):
    """Sets a reminder. Usage: !remind 60 1 leetcode problem"""
    user_id = ctx.author.id
    
    if user_id not in reminders:
        reminders[user_id] = []
    
    reminders[user_id].append({
        "task": task,
        "interval": interval_minutes,
        "last_notified": datetime.datetime.now(),
        "channel_id": ctx.channel.id
    })
    
    await ctx.send(f"✅ I'll remind you to **'{task}'** every {interval_minutes} minutes.")

@bot.command(name="list")
async def list_reminders(ctx):
    """Lists all active reminders."""
    user_id = ctx.author.id
    if user_id not in reminders or not reminders[user_id]:
        await ctx.send("You don't have any active reminders!")
        return
    
    response = "**Your Active Reminders:**\n"
    for i, r in enumerate(reminders[user_id], 1):
        response += f"{i}. **{r['task']}** (Every {r['interval']} mins)\n"
    
    await ctx.send(response)

@bot.command()
async def done(ctx, index: int = None):
    """Stops a specific reminder. Usage: !done 1"""
    user_id = ctx.author.id
    if user_id not in reminders or not reminders[user_id]:
        await ctx.send("You don't have any active reminders!")
        return

    if index is None:
        await ctx.send("⚠️ Please specify which reminder number to stop (e.g., `!done 1`). Use `!list` to see numbers.")
        return

    if index < 1 or index > len(reminders[user_id]):
        await ctx.send(f"❌ Invalid number. Please verify with `!list`.")
        return

    removed_task = reminders[user_id].pop(index - 1)
    
    # Cleanup if empty
    if not reminders[user_id]:
        del reminders[user_id]

    await ctx.send(f"✅ Stopped reminder: **{removed_task['task']}**")

# Create a check that checks to see each minute if YOU have finished the task XD
@tasks.loop(seconds=60) # Checks every minute
async def nag_loop():
    now = datetime.datetime.now()
    
    # Iterate over a copy of items since we might modify dictionary (though deleting users inside loop of items is risky, 
    # but here we iterate list(items))
    for user_id, user_reminders in list(reminders.items()):
        for reminder in user_reminders:
            # Calculate time difference
            elapsed = (now - reminder['last_notified']).total_seconds() / 60
            
            if elapsed >= reminder['interval']:
                channel = bot.get_channel(reminder['channel_id'])
                if channel:
                    await channel.send(f"🔔 <@{user_id}>, have you finished: **{reminder['task']}**? (Type `!done <number>` to stop)")
                
                # Update last notified time
                reminder['last_notified'] = now

bot.run(TOKEN)
