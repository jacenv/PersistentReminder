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
    for i, r in enumerate(reminders[user_id], 1):
        created_at = r.get('created_at', datetime.datetime.now()).strftime("%I:%M %p")
        description += f"**{i}.** {r['task']} *(Every {r['interval']} mins)*\nSet at: {created_at}\n\n"
    
    embed.description = description
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
                    embed = discord.Embed(title="🔔 Reminder!", description=f"Have you finished: **{reminder['task']}**?", color=discord.Color.orange())
                    embed.set_footer(text="Type !done <number> to stop")
                    await channel.send(content=f"<@{user_id}>", embed=embed)
                
                # Update last notified time
                reminder['last_notified'] = now

bot.run(TOKEN)
