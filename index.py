# Script written by will margulies that creates a chatbot
# between chatgpt and the messages in your computer.
# Will only work on Macs that have message integration with a phone.
# I couldn't sleep and someone was being wacky and I thought setting
# them up with a chatbot over text could be fun. I didn't realize that
# this is complicated and chatgpt doesn't really know how to work mac's internal
# database, so it ended up taking from like 5:45am to probably like 8am.
# I have an econ final at 9:30am and I've gotten like an hour and a half of sleep.
# because I'm pretty damn sick. It's chill tho.
# Whoever's reading this wml
# 7am update: chatgpt was able to help w internal db queries. tragic. i was just learning how it worked.
# additionally, keep in mind that this script works on the most recent chat from this person. That
# includes groupchats that you're in with them.
# I went to the midterm. Thought I did great but found out I messed up a little on the last short answer. We'll see
import sqlite3
import requests
import subprocess
from dotenv import load_dotenv
import os
import time
load_dotenv()

# Replace these with the actual values
db_path = os.getenv("DB_PATH")
phone_number = os.getenv("INTERESTED_PHONE_NUMBER")  # The phone number you're interested in
prevText = ""
n = 5
i = 0
# change prompt to specifics about the conversation:
# Connect to the SQLite database
conn = sqlite3.connect(db_path)
cursor = conn.cursor()
# SQL query to find the n most recent messages from a specific phone number
query = """
SELECT message.text, message.date, message.is_from_me
FROM message
JOIN handle ON message.handle_id = handle.ROWID
WHERE handle.id = ?
ORDER BY message.date DESC
LIMIT ?
"""
while True:
    prompt = os.getenv("PROMPT") + "\n"
    time.sleep(2.5)
    # Execute the query
    cursor.execute(query, (phone_number, n))
    messages = cursor.fetchall()

    # Check if there are any messages
    if messages:
        # Fetch the most recent message's text
        most_recent_message_text = messages[0][0]  # Get the text of the most recent message

        # Check if the most recent message text is the same as prevText
        if prevText == most_recent_message_text:
            repetitive = True
            print("exited")
        else:
            # If they are different, update prevText and reset the repetitive flag
            prevText = most_recent_message_text
            repetitive = False
        
        # If the message sequence is repetitive, skip sending a new message
        if repetitive:
            continue

        # Build the prompt with the conversation history
        for message in messages:
            text, date, is_from_me = message
            sender = "Me" if is_from_me else "Them"
            prompt += f"({sender}): {text}\n"
    print(prompt)
    # The rest of your code for generating and sending the message follows here

    dummy = True
    if repetitive:
        continue
    # Close the connection
    def query_gpt4(prompt):
        # REPLACE WITH YOUR OWN API KEY
        # if u just want to fool around and want me to get u one lmk
        api_key = os.getenv("OPENAI_API_KEY")
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": "gpt-3.5-turbo",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7,
            "max_tokens": 150,
        }
        response = requests.post("https://api.openai.com/v1/chat/completions", json=payload, headers=headers)
        
        if response.status_code == 200:
            # Extracting the text from the response
            return response.json()["choices"][0]["message"]["content"]
        else:
            # Handle possible errors
            return f"Error: {response.status_code}, {response.text}"

    # Replace YOUR_PROMPT_HERE with your actual prompt
    result = query_gpt4(prompt)
    def send_imessage(phone_number, message_text):
        """
        Sends an iMessage to a given phone number from your Mac.
        
        :param phone_number: The recipient's phone number as a string.
        :param message_text: The message text to send.
        """
        apple_script = f'''
        tell application "Messages"
            send "{message_text}" to buddy "{phone_number}" of (service 1 whose service type is iMessage)
        end tell
        '''
        
        subprocess.run(["osascript", "-e", apple_script], text=True)
    if i == 0:
        i = 1
    else:
        i = 0
        send_imessage(phone_number, result[6:])
