# Server Cloner

This project clones a Discord server (including channels, roles, and server information) from a source server to a target server.

## Requirements

- Python 3.6+
- `requests` library
- `colorama` library

## Installation

1. Clone this repository.
2. Install the required libraries:
    ```bash
    pip install -r requirements.txt
    ```

## Usage

1. Run the script:
    ```bash
    python main.py
    ```
2. Provide your bot token, source server ID, and target server ID when prompted.

## Notes

- Ensure that your bot token has the necessary permissions to access both the source and target servers.
- The script currently clones channels, roles, server name, and server icon. Additional features can be added as needed.