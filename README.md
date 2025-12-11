# AI-Agent-kanboard-task-analysis-gemini-ai
A complete AI automation workflow for Kanboard. This agent retrieves all tasks from Kanboard, processes them using Google Gemini for intelligent analysis (status insights, risk detection, prioritization, recommendations), and sends well-structured email reports. Built with Python and Google Gemini API.

# 📌 Kanboard AI Agent using Google Gemini
Automated task analysis & email reporting powered by Gemini AI
🚀 Overview

This project is an AI automation agent that connects Kanboard with Google Gemini to provide intelligent insights about your Kanboard tasks.

✔ Fetch all tasks from Kanboard
✔ Analyze them using Google Gemini
✔ Generate AI-powered insights
✔ Send the results through email automatically

Perfect for project managers, teams, and automation workflows.

🧠 Features

🔄 Fetch tasks from Kanboard via API

🤖 AI analysis using Gemini (task status, risk, next actions, summary)

📧 Send email reports containing the AI insights

⚙ Works on cron schedule or manual execution

🧹 Clean, modular Python code

📂 Project Structure
kanboard-gemini-ai-agent/
│
├── main.py               # Main script (fetch tasks → AI analysis → email)
├── kanboard_api.py       # Kanboard API helper functions
├── gemini_agent.py       # Gemini prompt + AI logic
├── email_sender.py       # Email sending module
├── requirements.txt      # Python dependencies
├── .env.example          # Example environment variables
└── README.md             # This documentation

⚙ Requirements

Python 3.9+

Kanboard with API enabled

Google Gemini API key

SMTP email credentials

🔧 Installation
1️⃣ Clone the repo
git clone https://github.com/<your-username>/kanboard-gemini-ai-agent.git
cd kanboard-gemini-ai-agent

2️⃣ Install dependencies
pip install -r requirements.txt

3️⃣ Create .env file
KANBOARD_URL=http://localhost/kanboard/jsonrpc.php
KANBOARD_API_USER=api_user
KANBOARD_API_KEY=xxxxxx
GEMINI_API_KEY=xxxxxx
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USER=example@gmail.com
EMAIL_PASS=xxxxxx
SEND_TO=team@example.com

▶ Run the Agent
python main.py

📨 Example Output (AI Email Summary)
Project: Website Redesign  
Total Tasks: 24  
Completed: 7  
In Progress: 5  
Blocked: 3  

⚠ AI Risk Analysis:
- Task #12 "Database Migration" is overdue by 8 days
- Task #18 has no assignee and is high priority

🧠 Recommended Actions:
- Assign unassigned critical tasks
- Update tasks not modified in the last 10 days
- Review blocked tasks immediately
