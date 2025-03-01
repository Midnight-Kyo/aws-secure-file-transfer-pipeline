import os
import requests
import subprocess

"""
Template: Telegram File Watcher for EC2 -> S3
--------------------------------------------
Replace the placeholders with your own values:
- <TELEGRAM_BOT_TOKEN>
- <YOUR_CHAT_ID>
- <YOUR_EC2_STORAGE_FOLDER>
- <YOUR_S3_BUCKET_NAME>

Usage:
- Monitors Telegram updates for new files or photos.
- Downloads them to the EC2 instance folder, then uploads to S3.
- Sends success/failure messages back to Telegram.
"""

# Configuration
TELEGRAM_BOT_TOKEN = "<TELEGRAM_BOT_TOKEN>"  # e.g. "1234567:ABC-..."
TELEGRAM_CHAT_ID = "<YOUR_CHAT_ID>"         # e.g. "987654321"
EC2_STORAGE_FOLDER = "/home/<YOUR_EC2_USERNAME>/temp_storage"  # Replace <YOUR_EC2_USERNAME>
S3_BUCKET = "<YOUR_S3_BUCKET_NAME>"         # e.g. "my-secure-file-bucket"

# Sends a text message to a Telegram user or group
def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    requests.post(url, json=payload)

# Downloads file from Telegram, returns the local file path
def download_file_from_telegram(file_id, file_name):
    # Step 1: Get File Path from Telegram API
    file_info_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getFile?file_id={file_id}"
    file_info = requests.get(file_info_url).json()

    if 'result' not in file_info:
        raise ValueError(f"Failed to fetch file info from Telegram API: {file_info}")

    file_path = file_info['result']['file_path']

    # Step 2: Download the actual file
    download_url = f"https://api.telegram.org/file/bot{TELEGRAM_BOT_TOKEN}/{file_path}"
    response = requests.get(download_url)

    local_path = os.path.join(EC2_STORAGE_FOLDER, file_name)
    with open(local_path, 'wb') as f:
        f.write(response.content)

    return local_path

# Uploads file to S3, removes local file if successful
def upload_file_to_s3(local_path, s3_path):
    cmd = ["aws", "s3", "cp", local_path, f"s3://{S3_BUCKET}/{s3_path}"]
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode == 0:
        send_telegram_message(f"✅ EC2 → S3 Upload Successful: {s3_path}")
        os.remove(local_path)  # Clean up file after upload
    else:
        send_telegram_message(f"❌ EC2 → S3 Upload Failed: {s3_path}\n{result.stderr}")

# Retrieves any new messages from Telegram, processes files if present
def process_new_messages():
    updates_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates"
    response = requests.get(updates_url).json()

    if 'result' not in response:
        print("No new messages found (no 'result' field).")
        return

    # Extract all messages
    messages = [update['message'] for update in response['result'] if 'message' in update]

    # Process each message
    for message in messages:
        # If it has a document (file)
        if 'document' in message:
            file_id = message['document']['file_id']
            file_name = message['document']['file_name']
            local_path = download_file_from_telegram(file_id, file_name)
            upload_file_to_s3(local_path, f"uploads/{file_name}")

        # If it has a photo
        elif 'photo' in message:
            file_id = message['photo'][-1]['file_id']  # The highest-quality photo is the last
            file_name = f"photo_{file_id}.jpg"
            local_path = download_file_from_telegram(file_id, file_name)
            upload_file_to_s3(local_path, f"uploads/{file_name}")

        else:
            # Could be text, sticker, or other non-file messages
            print(f"Skipping non-file message: {message.get('text', 'No text')}")

    # Optional: clear Telegram updates so they aren’t processed again
    if response['result']:
        offset = max(update['update_id'] for update in response['result']) + 1
        requests.get(f"{updates_url}?offset={offset}")

# Main runner
if __name__ == "__main__":
    # Create the storage folder if it doesn’t exist
    if not os.path.exists(EC2_STORAGE_FOLDER):
        os.makedirs(EC2_STORAGE_FOLDER)

    process_new_messages()
