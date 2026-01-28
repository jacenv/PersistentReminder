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
        "next_notification": datetime.datetime.now() + datetime.timedelta(minutes=interval_minutes),
        "created_at": datetime.datetime.now(),
        "channel_id": ctx.channel.id
    })
    
    embed = discord.Embed(title="✅ Reminder Set!", color=discord.Color.green())
    embed.add_field(name="Task", value=task, inline=False)
    embed.add_field(name="Interval", value=f"Every {interval_minutes} minutes", inline=False)
    embed.set_footer(text="Type !list to see all reminders")
    
    await ctx.send(embed=embed)

@remind.error
async def remind_error(ctx, error):
    if isinstance(error, (commands.BadArgument, commands.MissingRequiredArgument)):
        embed = discord.Embed(title="❌ Incorrect Usage", color=discord.Color.red())
        embed.description = "To set a reminder, use the format:\n`!remind <minutes> <task>`"
        embed.add_field(name="Example", value="`!remind 5 drink water`\n(Reminds you to drink water every 5 minutes)")
        await ctx.send(embed=embed)

@bot.command(name="list")
async def list_reminders(ctx):
    """Lists all active reminders."""
    user_id = ctx.author.id
    if user_id not in reminders or not reminders[user_id]:
        embed = discord.Embed(title="No Active Reminders", description="You're all clear! 🎉", color=discord.Color.blue())
        await ctx.send(embed=embed)
        return
    
    embed = discord.Embed(title="📝 Your Active Reminders", color=discord.Color.blue())
    description = ""
    now = datetime.datetime.now()
    for i, r in enumerate(reminders[user_id], 1):
        # Calculate time remaining
        target_time = r.get('next_notification')
        if not target_time:
             target_time = r['last_notified'] + datetime.timedelta(minutes=r['interval'])
        
        remaining = (target_time - now).total_seconds()
        
        if remaining <= 0:
            time_str = "**Due now!**"
        else:
            minutes = int(remaining // 60)
            seconds = int(remaining % 60)
            if minutes > 0:
                time_str = f"in {minutes}m {seconds}s"
            else:
                time_str = f"in {seconds}s"

        created_at = r.get('created_at', now).strftime("%I:%M %p")
        description += f"**{i}.** {r['task']} *(Every {r['interval']} mins)*\nSet at: {created_at} • Next ping: {time_str}\n\n"
    
    embed.description = description
    await ctx.send(embed=embed)

@bot.command()
async def snooze(ctx, index: int = None):
    """Snoozes a reminder for 5 minutes (or its original interval if shorter)."""
    user_id = ctx.author.id
    if user_id not in reminders or not reminders[user_id]:
        await ctx.send("You don't have any active reminders!")
        return

    if index is None:
        # If user has only one reminder, default to it
        if len(reminders[user_id]) == 1:
            index = 1
        else:
            await ctx.send("⚠️ Please specify which reminder number to snooze (e.g., `!snooze 1`). Use `!list` to see numbers.")
            return

    if index < 1 or index > len(reminders[user_id]):
        await ctx.send(f"❌ Invalid number. Please verify with `!list`.")
        return

    reminder = reminders[user_id][index - 1]
    
    # Logic: Snooze for 5 minutes, OR the original interval if it's less than 5 minutes
    snooze_duration = min(5, reminder['interval'])
    
    # Update the next notification time
    reminder['next_notification'] = datetime.datetime.now() + datetime.timedelta(minutes=snooze_duration)
    # Reset last_notified so nag_loop logic works correctly with the new target time
    reminder['last_notified'] = datetime.datetime.now()

    embed = discord.Embed(title="💤 Snoozed!", color=discord.Color.blue())
    embed.description = f"I've snoozed **{reminder['task']}** for {snooze_duration} minutes."
    await ctx.send(embed=embed)

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

    embed = discord.Embed(title="✅ Reminder Stopped", color=discord.Color.green())
    embed.description = f"Great job! I've stopped reminding you about:\n**{removed_task['task']}**"
    await ctx.send(embed=embed)

# Create a check that checks to see each minute if YOU have finished the task XD
@tasks.loop(seconds=1) # Checks every second for precision
async def nag_loop():
    now = datetime.datetime.now()
    
    # Iterate over a copy of items since we might modify dictionary (though deleting users inside loop of items is risky, 
    # but here we iterate list(items))
    for user_id, user_reminders in list(reminders.items()):
        for i, reminder in enumerate(user_reminders, 1):
            # Check if it's time to notify based on next_notification
            # If next_notification key doesn't exist (legacy), fallback to interval check logic
            
            target_time = reminder.get('next_notification')
            
            # If we don't have a target time yet (legacy), calculate it
            if not target_time:
                 target_time = reminder['last_notified'] + datetime.timedelta(minutes=reminder['interval'])

            if now >= target_time:
                channel = bot.get_channel(reminder['channel_id'])
                if channel:
                    embed = discord.Embed(title=f"🔔 Reminder #{i}", description=f"Have you finished: **{reminder['task']}**?", color=discord.Color.orange())
                    embed.set_footer(text=f"Type !done {i} to stop or !snooze {i} to snooze")
                    await channel.send(content=f"<@{user_id}>", embed=embed)
                
                # Update last notified time and set next notification time
                reminder['last_notified'] = now
                reminder['next_notification'] = now + datetime.timedelta(minutes=reminder['interval'])

bot.run(TOKEN)
