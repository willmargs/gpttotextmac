# Script written by William Margulies that creates a chatbot
# between chatgpt and messages.
# Will only work on Macs that have message integration with a phone.
# I couldn't sleep and my friend was being wacky and I thought setting
# them up with a chatbot over text could be fun. I didn't realize that
# this is complicated and chatgpt doesn't really know how to work mac's internal
# message database (chat.db), so it ended up taking from like 5:45am to 9am plus like two three hours of work.
# I am pretty sick and on 1.5hrs of sleep it's not ideal
# Whoever's reading this wml
# 7am update: chatgpt was able to help w internal db queries. tragic. i was just learning how it worked.
# additionally, keep in mind that this script works on the most recent chat from this person. That
# includes groupchats that you're in with them.
# I went to the midterm. Thought I did great but found out I messed up a little on the last short answer. We'll see how I did
# Thanks for reading the preface. I'm putting some effort into commenting my code for anyone that wants, so take a peek.
import sqlite3
import requests
import subprocess
from dotenv import load_dotenv
import os
import time
# Load the .env file that has environment variables, like credentials and other configs.
# Usually this is used more for credential-type variables, but I use it here for other options
load_dotenv()

db_path = os.getenv("DB_PATH")
phone_number = os.getenv("INTERESTED_PHONE_NUMBER")  # The phone number you're interested in
prevText = ""
n = 5
i = 0
repetitive = False
# Connect to the SQLite database
conn = sqlite3.connect(db_path)
cursor = conn.cursor()
# SQL query to find the n most recent messages from a phone number put into the request parameters
query = """
SELECT message.text, message.date, message.is_from_me
FROM message
JOIN handle ON message.handle_id = handle.ROWID
WHERE handle.id = ?
ORDER BY message.date DESC
LIMIT ?
"""
# Helper function to remove ChatGPT 
def remove_prefix(text: str) -> str:
    prefixes = ["(You):", "You:", "Them:", "(Them):"]
    # Check if the text starts with any of the prefixes
    for prefix in prefixes:
        if text.startswith(prefix):
            # Remove the prefix and potentially the space after it
            return text[len(prefix):].strip()
    
    # Return the original text if no prefix is found
    return text



print("turned on")
while True:
    # The prompt should ask gpt to continue the conversation and provide conversation context
    # e. g. Continue the conversation below. Return only one message to send. Make sure it 
    # relates directly to the conversation being had below. If a message says just 'None', ignore it.
    prompt = os.getenv("PROMPT") + "\n"
    time.sleep(2.5)
    # Execute the query. First parameter is the other person's phone number of the conversation we want and 
    # n is the number of phone numbers we want to be part of the context we send to chatgpt
    cursor.execute(query, (phone_number, n))
    messages = cursor.fetchall()

    if messages:
        # Fetch the most recent message's text
        most_recent_message_text = messages[0][0] 
        # Check if the most recent message text is the same as prevText, which means that there are no new messages
        if prevText == most_recent_message_text:
            repetitive = True
        else:
            # Otherwise, we proceed and set prevText to the new message
            prevText = most_recent_message_text
            repetitive = False
        
        # If the message sequence is repetitive, skip this repetition of the while loop, where we'll run this code and check again
        if repetitive:
            continue

        # Build the context we send to ChatGPT with the conversation history, assigning prefixes to each message saying who sent it
        for message in messages:
            text, date, is_from_me = message
            sender = "Me" if is_from_me else "Them"
            prompt += f"({sender}): {text}\n"
    # Helper function to create gpt4 request
    def query_gpt4(prompt):
        # Set API key and formulate the request we're making to GPT4
        api_key = os.getenv("OPENAI_API_KEY")
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": "gpt-4",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7,
            "max_tokens": 150,
        }
        # complete the request with the request we just created
        response = requests.post("https://api.openai.com/v1/chat/completions", json=payload, headers=headers)
        # if the response status code is 200, then the request is successful.
        if response.status_code == 200:
            # in that case, strip gpt's text response from chatgpt's response
            return response.json()["choices"][0]["message"]["content"]
        else:
            # If there are errors, print it.
            return f"Error: {response.status_code}, {response.text}"
        # Code fires twice as a result of an issue with req being made. Skip this function every other time 
    if i == 0:
        i = 1
        continue
    else:
        i = 0
    # Make the call to gpt4, store the result
    result = query_gpt4(prompt)
    # hHelper method to send the result to the appropriate conversation
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
    # Send the text
    send_imessage(phone_number, remove_prefix(result))
