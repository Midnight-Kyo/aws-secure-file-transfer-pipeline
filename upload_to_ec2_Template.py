import os
import subprocess
import requests

"""
Template: Python Script to Upload Files/Folders from a Local Windows PC to an EC2 instance
using SCP and then remove them from local storage.
-------------------------------------------------
Replace placeholders with your values:
- <LOCAL_WATCH_FOLDER>
- <EC2_USER>
- <EC2_IP>
- <EC2_TARGET_FOLDER>
- <SSH_KEY_PATH>
- <TELEGRAM_BOT_TOKEN>
- <TELEGRAM_CHAT_ID>
"""

# Local folder to watch
WATCH_FOLDER = r"<LOCAL_WATCH_FOLDER>"  # e.g. "C:\\path\\to\\watch_folder"

# EC2 SSH/SCP Configuration
EC2_USER = "<EC2_USER>"                  # e.g. "ubuntu"
EC2_IP = "<EC2_IP_ADDRESS>"             # e.g. "203.0.113.10"
EC2_TARGET_FOLDER = "/home/<YOUR_EC2_USERNAME>/temp_storage"
SSH_KEY = r"<SSH_KEY_PATH>"             # e.g. "C:\\path\\to\\key.pem"

# Telegram Config
TELEGRAM_BOT_TOKEN = "<TELEGRAM_BOT_TOKEN>"
TELEGRAM_CHAT_ID = "<YOUR_CHAT_ID>"

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    requests.post(url, json=payload)

def upload_to_ec2(local_path, remote_path):
    """
    Uses SCP to upload a file or directory to the specified EC2 target path.
    """
    cmd = [
        "scp",
        "-i", SSH_KEY,
        "-r",  # Recursive to handle folders
        local_path,
        f"{EC2_USER}@{EC2_IP}:{remote_path}"
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return (result.returncode == 0, result.stderr)

def process_folder(folder_path):
    """
    Walk through the local folder, upload each file,
    remove the local file if upload succeeds.
    """
    for root, dirs, files in os.walk(folder_path):
        relative_path = os.path.relpath(root, folder_path)

        # Convert Windows-style backslashes to forward slashes
        ec2_path = os.path.join(EC2_TARGET_FOLDER, relative_path).replace("\\", "/")

        # Ensure the folder structure exists on EC2
        subprocess.run([
            "ssh", "-i", SSH_KEY, f"{EC2_USER}@{EC2_IP}",
            f"mkdir -p '{ec2_path}'"
        ])

        for file in files:
            local_file = os.path.join(root, file)
            success, error = upload_to_ec2(local_file, ec2_path + "/")
            if success:
                # Remove the file locally once uploaded
                os.remove(local_file)
                send_telegram_message(f"✅ PC → EC2 Upload Successful: {relative_path}/{file}")
            else:
                send_telegram_message(f"❌ Failed to upload: {relative_path}/{file}\n{error}")

    # Clean up any empty directories on local machine
    for root, dirs, files in os.walk(folder_path, topdown=False):
        for dir in dirs:
            dir_path = os.path.join(root, dir)
            if not os.listdir(dir_path):
                os.rmdir(dir_path)

if __name__ == "__main__":
    if not os.path.exists(WATCH_FOLDER):
        send_telegram_message(f"❌ Error: WATCH_FOLDER '{WATCH_FOLDER}' does not exist.")
        exit()

    if not os.listdir(WATCH_FOLDER):
        send_telegram_message("✅ No files or folders to upload. Everything is clean.")
    else:
        process_folder(WATCH_FOLDER)
        send_telegram_message("🚀 Upload process complete!")
