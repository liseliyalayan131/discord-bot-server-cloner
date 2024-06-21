import requests
import logging
import os
from colorama import init, Fore, Style

init(autoreset=True)

class InfoFilter(logging.Filter):
    def filter(self, record):
        return record.levelno == logging.INFO

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger()
logger.addFilter(InfoFilter())

DISCORD_API_BASE_URL = "https://discord.com/api/v9"

ASCII_ART = """
                                      ___ 
 ___  _____  ___  ___  ___  ___  ___ |  _|
| -_||     ||  _|| -_||  _|| . ||   ||  _|
|___||_|_|_||_|  |___||___||___||_|_||_|  
"""

def get_headers(token):
    return {
        "Authorization": f"Bot {token}",
        "Content-Type": "application/json"
    }

def get_server_data(token, server_id):
    headers = get_headers(token)
    try:
        server_info = requests.get(f"{DISCORD_API_BASE_URL}/guilds/{server_id}", headers=headers).json()
        channels = requests.get(f"{DISCORD_API_BASE_URL}/guilds/{server_id}/channels", headers=headers).json()
        roles = requests.get(f"{DISCORD_API_BASE_URL}/guilds/{server_id}/roles", headers=headers).json()
        return server_info, channels, roles
    except Exception as e:
        logging.error(f"Error fetching server data: {e}")
        return None, None, None

def delete_role(token, target_server_id, role_id):
    headers = get_headers(token)
    try:
        response = requests.delete(f"{DISCORD_API_BASE_URL}/guilds/{target_server_id}/roles/{role_id}", headers=headers)
        return response.status_code
    except Exception as e:
        logging.error(f"Error deleting role {role_id}: {e}")
        return None

def delete_channel(token, target_server_id, channel_id):
    headers = get_headers(token)
    try:
        response = requests.delete(f"{DISCORD_API_BASE_URL}/channels/{channel_id}", headers=headers)
        return response.status_code
    except Exception as e:
        logging.error(f"Error deleting channel {channel_id}: {e}")
        return None

def create_role(token, target_server_id, role_data):
    headers = get_headers(token)
    data = {
        "name": role_data["name"],
        "permissions": str(role_data["permissions"]),
        "color": role_data["color"],
        "hoist": role_data["hoist"],
        "mentionable": role_data["mentionable"]
    }
    try:
        response = requests.post(f"{DISCORD_API_BASE_URL}/guilds/{target_server_id}/roles", headers=headers, json=data)
        return response.json()
    except Exception as e:
        logging.error(f"Error creating role {role_data['name']}: {e}")
        return None

def create_channel(token, target_server_id, channel_data):
    headers = get_headers(token)
    data = {
        "name": channel_data["name"],
        "type": channel_data["type"],
        "topic": channel_data.get("topic", ""),
        "nsfw": channel_data.get("nsfw", False),
        "parent_id": channel_data.get("parent_id", None),
        "permission_overwrites": channel_data.get("permission_overwrites", [])
    }
    try:
        response = requests.post(f"{DISCORD_API_BASE_URL}/guilds/{target_server_id}/channels", headers=headers, json=data)
        return response.json()
    except Exception as e:
        logging.error(f"Error creating channel {channel_data['name']}: {e}")
        return None

def update_server_info(token, target_server_id, server_info):
    headers = get_headers(token)
    data = {
        "name": server_info["name"],
        "icon": server_info.get("icon", None)
    }
    try:
        response = requests.patch(f"{DISCORD_API_BASE_URL}/guilds/{target_server_id}", headers=headers, json=data)
        return response.json()
    except Exception as e:
        logging.error(f"Error updating server info: {e}")
        return None

def send_dm(token, user_id):
    headers = get_headers(token)
    create_dm_url = f"{DISCORD_API_BASE_URL}/users/@me/channels"
    create_dm_data = {"recipient_id": user_id}

    try:
        dm_channel = requests.post(create_dm_url, headers=headers, json=create_dm_data)

        if dm_channel.status_code == 200:
            channel_id = dm_channel.json()["id"]
            send_message_url = f"{DISCORD_API_BASE_URL}/channels/{channel_id}/messages"
            embed_data = {
                "embeds": [
                    {
                        "title": "Sunucu Klonlama Tamamlandı!",
                        "description": "Sunucu başarıyla kopyalandı. İyi eğlenceler!",
                        "color": 0x00ff00,  
                        "footer": {
                            "text": "#codebyemreconf"
                        }
                    }
                ]
            }
            response = requests.post(send_message_url, headers=headers, json=embed_data)

            if response.status_code == 200:
                logging.info(Fore.GREEN + "DM notification sent successfully!")
            else:
                logging.error(f"Error sending DM: {response.json()}")
        else:
            logging.error(f"Error creating DM channel: {dm_channel.json()}")
    except Exception as e:
        logging.error(f"An unexpected error occurred while sending DM: {e}")

def clone_server(token, source_server_id, target_server_id, user_id):
    os.system("cls" if os.name == "nt" else "clear")
    print(Fore.MAGENTA + ASCII_ART)

    server_info, channels, roles = get_server_data(token, source_server_id)

    if 'message' in server_info or 'message' in channels or 'message' in roles:
        logging.error(Fore.RED + "Error: Unauthorized. Check if the bot has the necessary permissions and the token is correct.")
        return

    _, target_channels, target_roles = get_server_data(token, target_server_id)

    logging.info(Fore.YELLOW + "Deleting roles in the target server...")
    for role in target_roles:
        if role['name'] != '@everyone':
            delete_role(token, target_server_id, role['id'])

    logging.info(Fore.YELLOW + "Deleting channels in the target server...")
    for channel in target_channels:
        delete_channel(token, target_server_id, channel['id'])

    logging.info(Fore.CYAN + "Updating server info...")
    update_server_info(token, target_server_id, server_info)

    logging.info(Fore.CYAN + "Creating roles in the target server...")
    created_roles = {}
    for role in roles:
        created_role = create_role(token, target_server_id, role)
        if created_role:
            created_roles[role['id']] = created_role['id']

    categories = [ch for ch in channels if ch['type'] == 4] 
    normal_channels = [ch for ch in channels if ch['type'] != 4]


    logging.info(Fore.CYAN + "Creating categories in the target server...")
    category_mapping = {}
    for category in categories:
        created_category = create_channel(token, target_server_id, category)
        if created_category:
            category_mapping[category['id']] = created_category['id']

    logging.info(Fore.CYAN + "Creating channels in the target server...")
    for channel in normal_channels:
        if channel['parent_id']:
            channel['parent_id'] = category_mapping.get(channel['parent_id'], None)
        create_channel(token, target_server_id, channel)

    logging.info(Fore.GREEN + "#codebyemreconf")  

if __name__ == "__main__":
    bot_token = input(Fore.BLUE + "Enter your bot token: ")
    source_server_id = input(Fore.BLUE + "Enter the source server ID: ")
    target_server_id = input(Fore.BLUE + "Enter the target server ID: ")
    user_id = input(Fore.BLUE + "Enter your user ID: ")

    clone_server(bot_token, source_server_id, target_server_id, user_id)