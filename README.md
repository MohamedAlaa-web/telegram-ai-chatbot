# 🤖 Telegram AI Chatbot

A powerful Telegram chatbot powered by **Google Gemini 1.5 Flash** with an automated fallback to **Hugging Face (Mistral)**.

## ✨ Features

- **💬 Intelligent Chat**: Uses Gemini 1.5 Flash for high-quality responses.
- **🔄 Fallback Logic**: Automatically switches to Hugging Face if Gemini hits rate limits or is unavailable.
- **📸 Vision Support**: Send images to the bot and it will analyze them using Gemini Vision.
- **📄 PDF Support**: Upload PDF documents, and the bot will summarize the content for you.
- **🎤 Voice Support**: Send voice messages, and the bot will transcribe and respond to them.
- **🎬 Video Support**: Send regular videos or circular video notes, and the bot will analyze and respond to them.
- **📜 Chat History**: Maintains context for a more natural conversation experience.
- **🚀 Deploy Ready**: Pre-configured for deployment on **Render**.

## 🛠️ Setup Instructions

### 1. Requirements
- Python 3.10+
- A Telegram Bot Token (from [@BotFather](https://t.me/BotFather))
- A Google AI Studio API Key ([Get it here](https://aistudio.google.com/))
- A Hugging Face API Token ([Get it here](https://huggingface.co/settings/tokens))

### 2. Installation
1. Clone this repository:
   ```bash
   git clone https://github.com/MohamedAlaa-web/telegram-ai-chatbot.git
   cd telegram-ai-chatbot
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Configure environment variables:
   - Rename `.env.example` to `.env`.
   - Fill in your API keys in the `.env` file.

### 3. Run Locally
```bash
python bot.py
```

## 🌐 Deployment (Render)

1. Connect your GitHub repository to Render.
2. The `render.yaml` file will automatically configure the service.
3. Make sure to add your Environment Variables (`TELEGRAM_BOT_TOKEN`, `GEMINI_API_KEY`, `HF_API_KEY`) in the Render dashboard.

## 📜 Commands

- `/start` - Start the bot.
- `/help` - Show the help manual.
- `/clear` - Clear your chat history.
- `/transcribe_last` - Show the transcript of your last voice message.
- `/transcribe_video` - Show the analysis of your last video.
