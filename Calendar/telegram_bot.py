import os
import requests
from flask import Flask, request, jsonify

# Get your bot token from an environment variable (safer)
# In your terminal, run: export BOT_TOKEN="123456:ABC..."
TOKEN = os.environ.get("BOT_TOKEN")
TELEGRAM_URL = f"https://api.telegram.org/bot{TOKEN}"

app = Flask(__name__)

def send_message(chat_id, text):
    """Sends a reply message to the specified chat_id."""
    url = f"{TELEGRAM_URL}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text
    }
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status() # Will raise an exception for 4xx/5xx errors
        print(f"Reply sent: {response.json()}")
    except requests.exceptions.RequestException as e:
        print(f"Error sending reply: {e}")

@app.route("/webhook", methods=["POST"])
def webhook_handler():
    """This is the main function that receives and handles the webhook."""
    if request.is_json:
        data = request.get_json()
        
        # You can uncomment this to see the full data structure
        # print("Full update received:", data)
        
        # Check if the update contains a 'message' and 'text'
        if "message" in data and "text" in data["message"]:
            chat_id = data["message"]["chat"]["id"]
            text = data["message"]["text"]
            
            print(f"Received from {chat_id}: {text}", flush=True)
            
            # --- YOUR PYTHON PROJECT LOGIC GOES HERE ---
            # For this example, we'll just echo the message
            reply_text = f"You sent: {text}"
            send_message(chat_id, reply_text)
            # ---------------------------------------------
            
    # Always return a 200 OK to Telegram
    # This tells Telegram "I got the update, don't send it again."
    return jsonify(success=True), 200

if __name__ == "__main__":
    # This part is only for local testing, NOT for production
    app.run(host="0.0.0.0", port=5000)