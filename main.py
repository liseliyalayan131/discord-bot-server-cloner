import requests
import logging
import os
from colorama import init, Fore

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
| -_||     || _ || -_|| _ || . ||   ||  _|
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
        emojis = requests.get(f"{DISCORD_API_BASE_URL}/guilds/{server_id}/emojis", headers=headers).json()
        return server_info, channels, roles, emojis
    except Exception as e:
        logging.error(f"Error fetching server data: {e}")
        return None, None, None, None

def delete_role(token, target_server_id, role_id):
    headers = get_headers(token)
    try:
        response = requests.delete(f"{DISCORD_API_BASE_URL}/guilds/{target_server_id}/roles/{role_id}", headers=headers)
        response.raise_for_status()
        return response.status_code
    except requests.exceptions.HTTPError as e:
        if response.status_code == 403:
            logging.warning(f"Skipping deletion of role {role_id}: Insufficient permissions.")
        else:
            logging.error(f"Error deleting role {role_id}: {e}")
        return None
    except Exception as e:
        logging.error(f"Error deleting role {role_id}: {e}")
        return None

def delete_channel(token, target_server_id, channel_id):
    headers = get_headers(token)
    try:
        response = requests.delete(f"{DISCORD_API_BASE_URL}/channels/{channel_id}", headers=headers)
        response.raise_for_status()
        return response.status_code
    except requests.exceptions.HTTPError as e:
        if response.status_code == 403:
            logging.warning(f"Skipping deletion of channel {channel_id}: Insufficient permissions.")
        else:
            logging.error(f"Error deleting channel {channel_id}: {e}")
        return None
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
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        logging.error(f"Error creating role {role_data['name']}: {e}")
        return None
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
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        logging.error(f"Error creating channel {channel_data['name']}: {e}")
        return None
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
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        logging.error(f"Error updating server info: {e}")
        return None
    except Exception as e:
        logging.error(f"Error updating server info: {e}")
        return None

def create_emoji(token, target_server_id, emoji_data):
    headers = get_headers(token)
    data = {
        "name": emoji_data["name"],
        "image": emoji_data.get("image", None)
    }
    try:
        response = requests.post(f"{DISCORD_API_BASE_URL}/guilds/{target_server_id}/emojis", headers=headers, json=data)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        logging.error(f"Error creating emoji {emoji_data['name']}: {e}")
        return None
    except Exception as e:
        logging.error(f"Error creating emoji {emoji_data['name']}: {e}")
        return None

def delete_emoji(token, target_server_id, emoji_id):
    headers = get_headers(token)
    try:
        response = requests.delete(f"{DISCORD_API_BASE_URL}/guilds/{target_server_id}/emojis/{emoji_id}", headers=headers)
        response.raise_for_status()
        return response.status_code
    except requests.exceptions.HTTPError as e:
        if response.status_code == 403:
            logging.warning(f"Skipping deletion of emoji {emoji_id}: Insufficient permissions.")
        else:
            logging.error(f"Error deleting emoji {emoji_id}: {e}")
        return None
    except Exception as e:
        logging.error(f"Error deleting emoji {emoji_id}: {e}")
        return None

def send_dm(token, user_id, message):
    headers = get_headers(token)
    create_dm_url = f"{DISCORD_API_BASE_URL}/users/@me/channels"
    create_dm_data = {"recipient_id": user_id}

    try:
        dm_channel = requests.post(create_dm_url, headers=headers, json=create_dm_data)
        dm_channel.raise_for_status()

        channel_id = dm_channel.json()["id"]
        send_message_url = f"{DISCORD_API_BASE_URL}/channels/{channel_id}/messages"
        embed_data = {
            "embeds": [
                {
                    "title": "Server Cloning Completed!",
                    "description": message,
                    "color": 0x00ff00,  
                    "footer": {
                        "text": "#codebyemreconf"
                    }
                }
            ]
        }
        response = requests.post(send_message_url, headers=headers, json=embed_data)
        response.raise_for_status()

        logging.info(Fore.GREEN + "DM notification sent successfully!")
    except requests.exceptions.HTTPError as e:
        logging.error(f"Error sending DM: {e}")
    except Exception as e:
        logging.error(f"An unexpected error occurred while sending DM: {e}")

def list_and_delete_emojis(token, server_id):
    headers = get_headers(token)
    try:
        emojis = requests.get(f"{DISCORD_API_BASE_URL}/guilds/{server_id}/emojis", headers=headers).json()
        if not emojis:
            logging.info(Fore.YELLOW + "No emojis found.")
            return
        
        logging.info(Fore.YELLOW + "List of Emojis:")
        for emoji in emojis:
            logging.info(f"{emoji['name']} ({emoji['id']})")

        emoji_to_delete = input(Fore.BLUE + "Enter the ID of the emoji to delete (leave blank to skip): ")
        if emoji_to_delete:
            delete_emoji(token, server_id, emoji_to_delete)
            logging.info(Fore.GREEN + f"Emoji {emoji_to_delete} deleted successfully.")
        else:
            logging.info(Fore.BLUE + "No emoji deleted.")
    except requests.exceptions.HTTPError as e:
        logging.error(f"Error listing/deleting emojis: {e}")
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")

def clone_server(token, source_server_id, target_server_id, user_id):
    os.system("cls" if os.name == "nt" else "clear")
    print(Fore.MAGENTA + ASCII_ART)

    server_info, channels, roles, emojis = get_server_data(token, source_server_id)

    if 'message' in server_info or 'message' in channels or 'message' in roles:
        logging.error(Fore.RED + "Error: Unauthorized. Check if the bot has the necessary permissions and the token is correct.")
        return

    headers = get_headers(token)

    target_server_info, target_channels, target_roles, _ = get_server_data(token, target_server_id)

    logging.info(Fore.YELLOW + "Deleting roles in the target server...")
    for role in target_roles:
        if role['name'] != '@everyone':
            delete_role(token, target_server_id, role['id'])

    logging.info(Fore.YELLOW + "Deleting channels in the target server...")
    for channel in target_channels:
        delete_channel(token, target_server_id, channel['id'])

    logging.info(Fore.CYAN + "Updating server info...")
    update_server_info(token, target_server_id, server_info)

    created_roles = {}
    for role in roles:
        created_role = create_role(token, target_server_id, role)
        if created_role:
            created_roles[role['id']] = created_role['id']

    logging.info(Fore.CYAN + "Creating emojis in the target server...")
    for emoji in emojis:
        create_emoji(token, target_server_id, emoji)

    categories = [ch for ch in channels if ch['type'] == 4]
    normal_channels = [ch for ch in channels if ch['type'] != 4]

    logging.info(Fore.CYAN + "Creating categories and channels in the target server...")
    category_mapping = {}
    for category in categories:
        created_category = create_channel(token, target_server_id, category)
        if created_category:
            category_mapping[category['id']] = created_category['id']

    for channel in normal_channels:
        if channel['parent_id']:
            channel['parent_id'] = category_mapping.get(channel['parent_id'], None)
        created_channel = create_channel(token, target_server_id, channel)

        if created_channel and "permission_overwrites" in channel:
            for overwrite in channel["permission_overwrites"]:
                overwrite_data = {
                    "id": created_roles.get(overwrite["id"], overwrite["id"]), 
                    "type": overwrite["type"],
                    "allow": overwrite["allow"],
                    "deny": overwrite["deny"]
                }
                requests.put(
                    f"{DISCORD_API_BASE_URL}/channels/{created_channel['id']}/permissions/{overwrite_data['id']}",
                    headers=headers,
                    json=overwrite_data
                )

    logging.info(Fore.GREEN + "Server cloning completed!")
    send_dm(token, user_id, "The server has been successfully cloned.")

if __name__ == "__main__":
    bot_token = input(Fore.BLUE + "Enter your bot token: ")
    source_server_id = input(Fore.BLUE + "Enter the source server ID: ")
    target_server_id = input(Fore.BLUE + "Enter the target server ID: ")
    user_id = input(Fore.BLUE + "Enter your user ID: ")

    clone_server(bot_token, source_server_id, target_server_id, user_id)

    list_and_delete_emojis_choice = input(Fore.BLUE + "Do you want to list and delete emojis? (yes/no): ").lower()
    if list_and_delete_emojis_choice == "yes":
        list_and_delete_emojis(bot_token, target_server_id)
