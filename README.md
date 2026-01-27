# PersistentReminder
A persistent Discord reminder bot that pings you at regular intervals for tasks. It won't stop notifying you until you mark the task as complete using the `!done` command.

## 🛠️ Setup and How to Use

To get this bot running in your own Discord server, follow these steps:

### 1. Create Your Bot
1.  Go to the [Discord Developer Portal](https://discord.com/developers/applications).
2.  Click **New Application** and give it a name (e.g., "Persistent Reminder").
3.  Navigate to the **Bot** tab on the left sidebar.
4.  Click **Reset Token** to generate your unique Bot Token. **Copy this—you will need it in a moment.**
5.  Scroll down to **Privileged Gateway Intents** and toggle **Message Content Intent** to **ON**.

### 2. Configure Environment Variables
This project uses a `.env` file to keep your sensitive keys safe and out of your GitHub history.
1.  In the root directory of this project, create a file named `.env`.
2.  Open the file and add your token in the following format:
    ```text
    DISCORD_TOKEN=your_token_here_without_quotes
    ```
3.  Ensure your `.gitignore` file includes `.env` so you don't accidentally push your key to the internet.

### 3. Run the Bot
1.  Install the required libraries: 
    `pip install discord.py python-dotenv`
2.  Start the bot: 
    `python main.py`

### 4. Commands
* `!remind [minutes] [task]`: Sets a recurring reminder that pings you every X minutes.
* `!done`: Stops the current reminder once you've finished the task.

---