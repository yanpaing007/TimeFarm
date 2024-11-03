import json
import requests
import re
from bot.utils import logger

baseUrl = "https://tg-bot-tap.laborx.io/api"

api_endpoints = [
    r"https://tg-bot-tap.laborx.io/api",
    r"/v1/auth/validate-init/v2",
    r"/v1/me/onboarding/complete",
    r"/v1/farming/info",
    r"/v1/me/level/upgrade",
    r"/v1/balance/referral/claim",
    r"/v1/balance",
    r"/v1/farming/start",
    r"/v1/farming/finish",
    r"/v1/referral/link",
    r"/v1/tasks/.*",
    r"/v1/tasks",
    r"v1/tasks/submissions",
    r"v1/tasks/.*/claims",
]

def get_main_js_format(base_url):
    try:
        response = requests.get(base_url)
        response.raise_for_status()
        content = response.text
        
        matches = re.findall(r'src="((?:https?:)?//.*?/index.*?\.js|/.*?/index.*?\.js)"', content)
        if matches:
            return sorted(set(matches), key=len, reverse=True)
        else:
            return None
    except requests.RequestException as e:
        logger.error(f"Error fetching the base URL: {e}")
        return None

def get_base_api(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        content = response.text
        
        # Check if each API endpoint pattern matches any part of the JS content
        missing_endpoints = [pattern for pattern in api_endpoints if not re.search(pattern, content)]
        
        if not missing_endpoints:
            return True
        else:
            logger.error("<red>Missing endpoints:</red>", missing_endpoints)
            return False
    except requests.RequestException as e:
        logger.error(f"Error fetching the JS file: {e}")
        return None

def check_base_url():
    base_url = "https://img-tap-miniapp.chrono.tech/"
    main_js_formats = get_main_js_format(base_url)

    if main_js_formats:
        for format in main_js_formats:
            result = get_base_api(format)
            if result:
                return True

        return False
    else:
        logger.error("Could not find any main.js format. Dumping page content for inspection:")
        try:
            response = requests.get(base_url)
            logger.error(response.text[:1000])  
        except requests.RequestException as e:
            logger.error(f"Error fetching the base URL for content dump: {e}")
        return False

def get_version_info():
    try:
        response = requests.get("https://raw.githubusercontent.com/yanpaing007/TimeFarm/main/bot/config/answer.json")
        response.raise_for_status()
        data = response.json()
        version = data.get('version', None)
        message = data.get('message', None)
        return version, message
    except requests.RequestException as e:
        logger.error(f"Error fetching the version info: {e}")
        return None, None
    
def get_local_version_info():
    try:
        with open('bot/config/answer.json', 'r') as local_file:
            data = json.load(local_file)
            version = data.get('version', None)
            return version

    except FileNotFoundError:
            logger.error(f"Local file answer.json not found.")
    except json.JSONDecodeError as json_err:
            logger.error(f"Error parsing JSON from local file: {json_err}")

    return None