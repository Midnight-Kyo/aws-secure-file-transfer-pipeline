#!/bin/bash

# Template: Bash Script to upload local EC2 files to S3 and then clean up.
# Replace placeholders with your values.

BUCKET_NAME="<YOUR_S3_BUCKET_NAME>"        # e.g. "my-secure-bucket"
UPLOAD_DIR="/home/<YOUR_EC2_USERNAME>/temp_storage"  # e.g. /home/ubuntu/temp_storage

TELEGRAM_BOT_TOKEN="<TELEGRAM_BOT_TOKEN>"
TELEGRAM_CHAT_ID="<YOUR_CHAT_ID>"

# Function to send a Telegram message
send_telegram_message() {
    curl -s -X POST "https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/sendMessage" \
         -d "chat_id=$TELEGRAM_CHAT_ID" \
         -d "text=$1" > /dev/null
}

send_telegram_message "🚀 EC2: Starting Upload Process to S3..."

# Iterate over files in $UPLOAD_DIR
for file in "$UPLOAD_DIR"/*; do
    if [ -f "$file" ]; then
        filename=$(basename "$file")
        aws s3 cp "$file" "s3://$BUCKET_NAME/$filename"
        if [ $? -eq 0 ]; then
            send_telegram_message "✅ EC2 → S3 Upload Successful: $filename"
            rm -f "$file"
        else
            send_telegram_message "❌ EC2 → S3 Upload Failed: $filename"
        fi
    fi
done

send_telegram_message "🏁 EC2: Upload Process Complete. EC2 Storage Cleared."
