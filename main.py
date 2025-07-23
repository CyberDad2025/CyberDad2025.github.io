import openai
import datetime
import os
import random

# Set your OpenAI API key
openai.api_key = os.getenv("OPENAI_API_KEY")

# Define the output folder
POST_DIR = "_posts"

# Define time-based categories
categories_by_hour = {
    9: "Family Tips",
    13: "Cyber Threat Alert",
    20: "Security Tools"
}

# Title prompt themes
prompt_by_category = {
    "Family Tips": "Write a short, helpful cybersecurity tip for families using non-technical language.",
    "Cyber Threat Alert": "Summarize the latest cybersecurity threat or scam targeting families. Use plain English.",
    "Security Tools": "Explain a cybersecurity tool (like VPN, antivirus, 2FA) in a simple way that even grandparents can follow."
}

# Determine the current category
current_hour = datetime.datetime.now().hour
selected_hour = max([h for h in categories_by_hour if h <= current_hour], default=9)
category = categories_by_hour[selected_hour]
prompt = prompt_by_category[category]

# Generate post with OpenAI
response = openai.ChatCompletion.create(
    model="gpt-4",
