"""
Discord Server Cloner Bot
A tool to clone Discord server configurations including channels, roles, and emojis.
"""

import requests
import logging
import os
import time
from typing import Optional, Dict, List, Any, Tuple
from colorama import init, Fore

init(autoreset=True)

# Constants
DISCORD_API_BASE_URL = "https://discord.com/api/v9"
RATE_LIMIT_DELAY = 0.5  # Delay between API calls in seconds
SUCCESS_COLOR = 0x00ff00
FOOTER_TEXT = "#codebyemreconf"

ASCII_ART = """
                                      ___
 ___  _____  ___  ___  ___  ___  ___ |  _|
| -_||     || _ || -_|| _ || . ||   ||  _|
|___||_|_|_||_|  |___||___||___||_|_||_|
"""


class InfoFilter(logging.Filter):
    """Filter to only show INFO level logs."""

    def filter(self, record: logging.LogRecord) -> bool:
        """
        Filter log records to only show INFO level.

        Args:
            record: The log record to filter

        Returns:
            True if record is INFO level, False otherwise
        """
        return record.levelno == logging.INFO


# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger()
logger.addFilter(InfoFilter())


def get_headers(token: str) -> Dict[str, str]:
    """
    Generate HTTP headers for Discord API requests.

    Args:
        token: Discord bot token

    Returns:
        Dictionary containing authorization and content-type headers
    """
    return {
        "Authorization": f"Bot {token}",
        "Content-Type": "application/json"
    }


def validate_id(value: str, field_name: str) -> bool:
    """
    Validate that a Discord ID is numeric and non-empty.

    Args:
        value: The ID string to validate
        field_name: Name of the field being validated (for error messages)

    Returns:
        True if valid, False otherwise
    """
    if not value or not value.strip():
        logging.error(f"{field_name} cannot be empty.")
        return False

    if not value.isdigit():
        logging.error(f"{field_name} must be numeric.")
        return False

    return True


def make_request(
    method: str,
    url: str,
    headers: Dict[str, str],
    json_data: Optional[Dict[str, Any]] = None,
    operation_name: str = "API request"
) -> Optional[Any]:
    """
    Make an HTTP request to Discord API with error handling and rate limiting.

    Args:
        method: HTTP method (GET, POST, PUT, DELETE, PATCH)
        url: Full URL to request
        headers: Request headers
        json_data: Optional JSON data for request body
        operation_name: Description of operation for logging

    Returns:
        Response JSON for successful requests, status code for DELETE, None on error
    """
    time.sleep(RATE_LIMIT_DELAY)  # Rate limiting
    response = None

    try:
        if method.upper() == "GET":
            response = requests.get(url, headers=headers)
        elif method.upper() == "POST":
            response = requests.post(url, headers=headers, json=json_data)
        elif method.upper() == "PUT":
            response = requests.put(url, headers=headers, json=json_data)
        elif method.upper() == "DELETE":
            response = requests.delete(url, headers=headers)
        elif method.upper() == "PATCH":
            response = requests.patch(url, headers=headers, json=json_data)
        else:
            logging.error(f"Unsupported HTTP method: {method}")
            return None

        response.raise_for_status()

        # Return status code for DELETE, JSON for others
        if method.upper() == "DELETE":
            return response.status_code
        return response.json()

    except requests.exceptions.HTTPError as e:
        if response and response.status_code == 403:
            logging.warning(f"Insufficient permissions for {operation_name}.")
        elif response and response.status_code == 429:
            logging.warning(f"Rate limited during {operation_name}. Consider increasing delay.")
        else:
            logging.error(f"HTTP error during {operation_name}: {e}")
        return None

    except requests.exceptions.RequestException as e:
        logging.error(f"Request error during {operation_name}: {e}")
        return None

    except Exception as e:
        logging.error(f"Unexpected error during {operation_name}: {e}")
        return None


def get_server_data(
    token: str,
    server_id: str
) -> Tuple[Optional[Dict], Optional[List], Optional[List], Optional[List]]:
    """
    Fetch all data from a Discord server.

    Args:
        token: Discord bot token
        server_id: ID of the server to fetch data from

    Returns:
        Tuple of (server_info, channels, roles, emojis) or (None, None, None, None) on error
    """
    headers = get_headers(token)

    server_info = make_request(
        "GET",
        f"{DISCORD_API_BASE_URL}/guilds/{server_id}",
        headers,
        operation_name=f"fetching server {server_id} info"
    )

    channels = make_request(
        "GET",
        f"{DISCORD_API_BASE_URL}/guilds/{server_id}/channels",
        headers,
        operation_name=f"fetching server {server_id} channels"
    )

    roles = make_request(
        "GET",
        f"{DISCORD_API_BASE_URL}/guilds/{server_id}/roles",
        headers,
        operation_name=f"fetching server {server_id} roles"
    )

    emojis = make_request(
        "GET",
        f"{DISCORD_API_BASE_URL}/guilds/{server_id}/emojis",
        headers,
        operation_name=f"fetching server {server_id} emojis"
    )

    # Check if any request returned an error message
    if any(data and isinstance(data, dict) and 'message' in data
           for data in [server_info, channels, roles]):
        logging.error("Error: Unauthorized or invalid server ID. Check bot permissions and server ID.")
        return None, None, None, None

    return server_info, channels, roles, emojis


def delete_role(token: str, target_server_id: str, role_id: str) -> bool:
    """
    Delete a role from a server.

    Args:
        token: Discord bot token
        target_server_id: ID of the server containing the role
        role_id: ID of the role to delete

    Returns:
        True if successful, False otherwise
    """
    headers = get_headers(token)
    result = make_request(
        "DELETE",
        f"{DISCORD_API_BASE_URL}/guilds/{target_server_id}/roles/{role_id}",
        headers,
        operation_name=f"deleting role {role_id}"
    )
    return result is not None


def delete_channel(token: str, target_server_id: str, channel_id: str) -> bool:
    """
    Delete a channel from a server.

    Args:
        token: Discord bot token
        target_server_id: ID of the server containing the channel
        channel_id: ID of the channel to delete

    Returns:
        True if successful, False otherwise
    """
    headers = get_headers(token)
    result = make_request(
        "DELETE",
        f"{DISCORD_API_BASE_URL}/channels/{channel_id}",
        headers,
        operation_name=f"deleting channel {channel_id}"
    )
    return result is not None


def create_role(
    token: str,
    target_server_id: str,
    role_data: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """
    Create a new role in a server.

    Args:
        token: Discord bot token
        target_server_id: ID of the server to create the role in
        role_data: Dictionary containing role configuration

    Returns:
        Created role data if successful, None otherwise
    """
    headers = get_headers(token)
    data = {
        "name": role_data.get("name", "new role"),
        "permissions": str(role_data.get("permissions", "0")),
        "color": role_data.get("color", 0),
        "hoist": role_data.get("hoist", False),
        "mentionable": role_data.get("mentionable", False)
    }

    return make_request(
        "POST",
        f"{DISCORD_API_BASE_URL}/guilds/{target_server_id}/roles",
        headers,
        json_data=data,
        operation_name=f"creating role {role_data.get('name', 'unknown')}"
    )


def create_channel(
    token: str,
    target_server_id: str,
    channel_data: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """
    Create a new channel in a server.

    Args:
        token: Discord bot token
        target_server_id: ID of the server to create the channel in
        channel_data: Dictionary containing channel configuration

    Returns:
        Created channel data if successful, None otherwise
    """
    headers = get_headers(token)
    data = {
        "name": channel_data.get("name", "new-channel"),
        "type": channel_data.get("type", 0),
        "topic": channel_data.get("topic", ""),
        "nsfw": channel_data.get("nsfw", False),
        "parent_id": channel_data.get("parent_id"),
        "permission_overwrites": channel_data.get("permission_overwrites", [])
    }

    return make_request(
        "POST",
        f"{DISCORD_API_BASE_URL}/guilds/{target_server_id}/channels",
        headers,
        json_data=data,
        operation_name=f"creating channel {channel_data.get('name', 'unknown')}"
    )


def update_server_info(
    token: str,
    target_server_id: str,
    server_info: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """
    Update server name and icon.

    Args:
        token: Discord bot token
        target_server_id: ID of the server to update
        server_info: Dictionary containing server configuration

    Returns:
        Updated server data if successful, None otherwise
    """
    headers = get_headers(token)
    data = {
        "name": server_info.get("name", "Cloned Server"),
        "icon": server_info.get("icon")
    }

    return make_request(
        "PATCH",
        f"{DISCORD_API_BASE_URL}/guilds/{target_server_id}",
        headers,
        json_data=data,
        operation_name="updating server info"
    )


def create_emoji(
    token: str,
    target_server_id: str,
    emoji_data: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """
    Create a new emoji in a server.

    Args:
        token: Discord bot token
        target_server_id: ID of the server to create the emoji in
        emoji_data: Dictionary containing emoji configuration

    Returns:
        Created emoji data if successful, None otherwise
    """
    headers = get_headers(token)
    data = {
        "name": emoji_data.get("name", "emoji"),
        "image": emoji_data.get("image")
    }

    return make_request(
        "POST",
        f"{DISCORD_API_BASE_URL}/guilds/{target_server_id}/emojis",
        headers,
        json_data=data,
        operation_name=f"creating emoji {emoji_data.get('name', 'unknown')}"
    )


def delete_emoji(token: str, target_server_id: str, emoji_id: str) -> bool:
    """
    Delete an emoji from a server.

    Args:
        token: Discord bot token
        target_server_id: ID of the server containing the emoji
        emoji_id: ID of the emoji to delete

    Returns:
        True if successful, False otherwise
    """
    headers = get_headers(token)
    result = make_request(
        "DELETE",
        f"{DISCORD_API_BASE_URL}/guilds/{target_server_id}/emojis/{emoji_id}",
        headers,
        operation_name=f"deleting emoji {emoji_id}"
    )
    return result is not None


def send_dm(token: str, user_id: str, message: str) -> bool:
    """
    Send a DM notification to a user.

    Args:
        token: Discord bot token
        user_id: ID of the user to send DM to
        message: Message content

    Returns:
        True if successful, False otherwise
    """
    headers = get_headers(token)
    create_dm_data = {"recipient_id": user_id}

    # Create DM channel
    dm_channel = make_request(
        "POST",
        f"{DISCORD_API_BASE_URL}/users/@me/channels",
        headers,
        json_data=create_dm_data,
        operation_name="creating DM channel"
    )

    if not dm_channel:
        return False

    # Send message
    embed_data = {
        "embeds": [
            {
                "title": "Server Cloning Completed!",
                "description": message,
                "color": SUCCESS_COLOR,
                "footer": {
                    "text": FOOTER_TEXT
                }
            }
        ]
    }

    result = make_request(
        "POST",
        f"{DISCORD_API_BASE_URL}/channels/{dm_channel['id']}/messages",
        headers,
        json_data=embed_data,
        operation_name="sending DM notification"
    )

    if result:
        logging.info(Fore.GREEN + "DM notification sent successfully!")
        return True
    return False


def update_channel_permissions(
    token: str,
    channel_id: str,
    overwrite_data: Dict[str, Any]
) -> bool:
    """
    Update permission overwrites for a channel.

    Args:
        token: Discord bot token
        channel_id: ID of the channel to update
        overwrite_data: Permission overwrite data

    Returns:
        True if successful, False otherwise
    """
    headers = get_headers(token)
    result = make_request(
        "PUT",
        f"{DISCORD_API_BASE_URL}/channels/{channel_id}/permissions/{overwrite_data['id']}",
        headers,
        json_data=overwrite_data,
        operation_name=f"updating permissions for channel {channel_id}"
    )
    return result is not None


def list_and_delete_emojis(token: str, server_id: str) -> None:
    """
    List all emojis in a server and optionally delete one.

    Args:
        token: Discord bot token
        server_id: ID of the server
    """
    headers = get_headers(token)
    emojis = make_request(
        "GET",
        f"{DISCORD_API_BASE_URL}/guilds/{server_id}/emojis",
        headers,
        operation_name="listing emojis"
    )

    if not emojis:
        logging.info(Fore.YELLOW + "No emojis found.")
        return

    logging.info(Fore.YELLOW + "List of Emojis:")
    for emoji in emojis:
        logging.info(f"{emoji.get('name', 'unknown')} ({emoji.get('id', 'unknown')})")

    emoji_to_delete = input(Fore.BLUE + "Enter the ID of the emoji to delete (leave blank to skip): ").strip()

    if emoji_to_delete:
        if delete_emoji(token, server_id, emoji_to_delete):
            logging.info(Fore.GREEN + f"Emoji {emoji_to_delete} deleted successfully.")
        else:
            logging.error(Fore.RED + f"Failed to delete emoji {emoji_to_delete}.")
    else:
        logging.info(Fore.BLUE + "No emoji deleted.")


def clone_server(
    token: str,
    source_server_id: str,
    target_server_id: str,
    user_id: str
) -> bool:
    """
    Clone a Discord server from source to target.

    Args:
        token: Discord bot token
        source_server_id: ID of the server to clone from
        target_server_id: ID of the server to clone to
        user_id: ID of the user to notify upon completion

    Returns:
        True if successful, False otherwise
    """
    # Clear screen and show ASCII art
    os.system("cls" if os.name == "nt" else "clear")
    print(Fore.MAGENTA + ASCII_ART)

    # Fetch source server data
    logging.info(Fore.CYAN + "Fetching source server data...")
    server_info, channels, roles, emojis = get_server_data(token, source_server_id)

    if not all([server_info, channels, roles]):
        logging.error(Fore.RED + "Failed to fetch source server data. Aborting.")
        return False

    # Fetch target server data
    logging.info(Fore.CYAN + "Fetching target server data...")
    _, target_channels, target_roles, _ = get_server_data(token, target_server_id)

    if not all([target_channels, target_roles]):
        logging.error(Fore.RED + "Failed to fetch target server data. Aborting.")
        return False

    # Delete existing roles in target server
    logging.info(Fore.YELLOW + "Deleting roles in the target server...")
    for role in target_roles:
        if role.get('name') != '@everyone':
            delete_role(token, target_server_id, role['id'])

    # Delete existing channels in target server
    logging.info(Fore.YELLOW + "Deleting channels in the target server...")
    for channel in target_channels:
        delete_channel(token, target_server_id, channel['id'])

    # Update server info (name and icon)
    logging.info(Fore.CYAN + "Updating server info...")
    update_server_info(token, target_server_id, server_info)

    # Create roles and track mapping
    logging.info(Fore.CYAN + "Creating roles in the target server...")
    created_roles = {}
    for role in roles:
        created_role = create_role(token, target_server_id, role)
        if created_role:
            created_roles[role['id']] = created_role['id']

    # Create emojis
    logging.info(Fore.CYAN + "Creating emojis in the target server...")
    for emoji in emojis or []:
        create_emoji(token, target_server_id, emoji)

    # Separate categories and normal channels
    categories = [ch for ch in channels if ch.get('type') == 4]
    normal_channels = [ch for ch in channels if ch.get('type') != 4]

    # Create categories first
    logging.info(Fore.CYAN + "Creating categories in the target server...")
    category_mapping = {}
    for category in categories:
        created_category = create_channel(token, target_server_id, category)
        if created_category:
            category_mapping[category['id']] = created_category['id']

    # Create normal channels
    logging.info(Fore.CYAN + "Creating channels in the target server...")
    headers = get_headers(token)
    for channel in normal_channels:
        # Update parent_id to match new category
        if channel.get('parent_id'):
            channel['parent_id'] = category_mapping.get(channel['parent_id'])

        created_channel = create_channel(token, target_server_id, channel)

        # Update permission overwrites
        if created_channel and channel.get("permission_overwrites"):
            for overwrite in channel["permission_overwrites"]:
                overwrite_data = {
                    "id": created_roles.get(overwrite["id"], overwrite["id"]),
                    "type": overwrite.get("type", 0),
                    "allow": overwrite.get("allow", "0"),
                    "deny": overwrite.get("deny", "0")
                }
                update_channel_permissions(token, created_channel['id'], overwrite_data)

    # Send completion notification
    logging.info(Fore.GREEN + "Server cloning completed!")
    send_dm(token, user_id, "The server has been successfully cloned.")

    return True


def main() -> None:
    """Main entry point for the Discord Server Cloner."""
    print(Fore.MAGENTA + ASCII_ART)
    print(Fore.CYAN + "Discord Server Cloner v2.0\n")

    # Get user inputs
    bot_token = input(Fore.BLUE + "Enter your bot token: ").strip()
    if not bot_token:
        logging.error(Fore.RED + "Bot token cannot be empty.")
        return

    source_server_id = input(Fore.BLUE + "Enter the source server ID: ").strip()
    if not validate_id(source_server_id, "Source server ID"):
        return

    target_server_id = input(Fore.BLUE + "Enter the target server ID: ").strip()
    if not validate_id(target_server_id, "Target server ID"):
        return

    user_id = input(Fore.BLUE + "Enter your user ID: ").strip()
    if not validate_id(user_id, "User ID"):
        return

    # Clone the server
    success = clone_server(bot_token, source_server_id, target_server_id, user_id)

    if not success:
        logging.error(Fore.RED + "Server cloning failed. Please check the logs above.")
        return

    # Optional emoji management
    list_emojis_choice = input(
        Fore.BLUE + "Do you want to list and delete emojis? (yes/no): "
    ).strip().lower()

    if list_emojis_choice == "yes":
        list_and_delete_emojis(bot_token, target_server_id)

    print(Fore.GREEN + "\nThank you for using Discord Server Cloner!")


if __name__ == "__main__":
    main()
