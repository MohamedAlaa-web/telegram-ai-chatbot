import os
import logging
import time
from io import BytesIO
from dotenv import load_dotenv
import PyPDF2
import google.generativeai as genai
from huggingface_hub import InferenceClient
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

# 1. تحميل مفاتيح البيئة
load_dotenv()

# 2. إعداد الـ Logging لمراقبة البوت
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# مفاتيح API
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
HF_API_KEY = os.getenv("HF_API_KEY")

# 3. تهيئة عملاء الذكاء الاصطناعي
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    gemini_model = genai.GenerativeModel("gemini-1.5-flash")
else:
    logger.warning("GEMINI_API_KEY missing!")
    gemini_model = None

if HF_API_KEY:
    hf_client = InferenceClient(model="mistralai/Mistral-7B-Instruct-v0.2", token=HF_API_KEY)
else:
    logger.warning("HF_API_KEY missing!")
    hf_client = None

# ذاكرة المحادثات وسجل المستخدمين
user_conversations = {}

# --- دوال مساعدة (Helper Functions) ---

def add_to_history(user_id, role, content):
    if user_id not in user_conversations:
        user_conversations[user_id] = []
    user_conversations[user_id].append({"role": role, "content": content})
    if len(user_conversations[user_id]) > 10:  # حفظ آخر 10 رسائل فقط
        user_conversations[user_id] = user_conversations[user_id][-10:]

async def call_gemini_text(prompt, user_id):
    if not gemini_model: return None
    try:
        response = gemini_model.generate_content(prompt)
        return response.text
    except Exception as e:
        logger.error(f"Gemini Error: {e}")
        return None

async def call_hf_fallback(prompt):
    if not hf_client: return "⚠️ عذراً، جميع الأنظمة معطلة حالياً."
    try:
        # For simplicity in this final version, we use the generated content directly
        return hf_client.text_generation(prompt, max_new_tokens=500)
    except Exception as e:
        logger.error(f"HF Error: {e}")
        return "❌ فشل النظام الأساسي والبديل."

# --- أوامر البوت (Commands) ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 أهلاً بك في البوت الشامل!\n\n"
        "✅ أدعم النصوص، الصور، ملفات PDF، الصوت، والفيديو.\n"
        "استخدم /help لمعرفة كل الأوامر."
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "🤖 **دليل الاستخدام:**\n\n"
        "💬 **الدردشة**: أرسل أي نص.\n"
        "🖼️ **الصور**: أرسل صورة مع وصف لتحليلها.\n"
        "📄 **الملفات**: أرسل PDF للتلخيص.\n"
        "🎤 **الصوت**: أرسل بصمة صوتية للرد عليها.\n"
        "🎬 **الفيديو**: أرسل فيديو (عادي أو دائري).\n\n"
        "📜 **الأوامر:**\n"
        "/clear - مسح السجل\n"
        "/transcribe_last - نص آخر صوت\n"
        "/transcribe_video - وصف آخر فيديو"
    )
    await update.message.reply_text(help_text, parse_mode="Markdown")

async def clear_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_conversations.pop(user_id, None)
    context.user_data.clear()
    await update.message.reply_text("✅ تم مسح السجل والذاكرة المؤقتة.")

async def transcribe_last(update: Update, context: ContextTypes.DEFAULT_TYPE):
    transcript = context.user_data.get("last_transcript", "⚠️ لا يوجد تسجيل متاح.")
    await update.message.reply_text(f"📝 **النص المستخرج:**\n\n{transcript}", parse_mode="Markdown")

async def transcribe_video_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    content = context.user_data.get("last_video_content", "⚠️ لا يوجد فيديو محلل.")
    await update.message.reply_text(f"📝 **تحليل الفيديو:**\n\n{content}", parse_mode="Markdown")

# --- معالجة الرسائل (Handlers) ---

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id, text = update.effective_user.id, update.message.text
    if not text: return
    await update.message.chat.send_action("typing")
    response = await call_gemini_text(text, user_id) or await call_hf_fallback(text)
    add_to_history(user_id, "user", text)
    add_to_history(user_id, "model", response)
    await update.message.reply_text(response)

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.chat.send_action("typing")
    try:
        photo_file = await update.message.photo[-1].get_file()
        photo_bytes = await photo_file.download_as_bytearray()
        response = gemini_model.generate_content([update.message.caption or "اشرح هذه الصورة", {"mime_type": "image/jpeg", "data": bytes(photo_bytes)}])
        await update.message.reply_text(response.text)
    except Exception as e: await update.message.reply_text(f"❌ خطأ: {e}")

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    doc = update.message.document
    if doc.mime_type != "application/pdf": return await update.message.reply_text("⚠️ أرسل ملف PDF فقط.")
    await update.message.chat.send_action("typing")
    try:
        pdf_file = await doc.get_file()
        pdf_data = await pdf_file.download_as_bytearray()
        reader = PyPDF2.PdfReader(BytesIO(pdf_data))
        text = "".join([p.extract_text() for p in reader.pages[:5]])
        prompt = f"لخص هذا النص في نقاط:\n\n{text[:4000]}"
        response = await call_gemini_text(prompt, update.effective_user.id) or await call_hf_fallback(prompt)
        await update.message.reply_text(f"📄 **ملخص PDF:**\n\n{response}", parse_mode="Markdown")
    except Exception as e: await update.message.reply_text(f"❌ خطأ: {e}")

async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.chat.send_action("typing")
    try:
        voice = await update.message.voice.get_file()
        voice_data = await voice.download_as_bytearray()
        # استخراج النص أولاً
        trans = gemini_model.generate_content(["اكتب النص الحرفي لهذا الصوت فقط بوضوح", {"mime_type": "audio/ogg", "data": bytes(voice_data)}]).text
        context.user_data["last_transcript"] = trans
        # الرد على المحتوى
        resp = await call_gemini_text(f"رد بذكاء على هذا: {trans}", update.effective_user.id) or await call_hf_fallback(trans)
        await update.message.reply_text(resp)
    except Exception as e: await update.message.reply_text(f"❌ خطأ الصوت: {e}")

async def handle_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    video = update.message.video or update.message.video_note
    if not video: return
    status_msg = await update.message.reply_text("🎬 جاري تحليل الفيديو (قد يستغرق لحظات)...")
    path = f"temp_{int(time.time())}.mp4"
    try:
        file = await video.get_file()
        await file.download_to_drive(path)
        g_file = genai.upload_file(path=path)
        while g_file.state.name == "PROCESSING": time.sleep(2); g_file = genai.get_file(g_file.name)
        res = gemini_model.generate_content(["صف ما تراه وتسمعه ورد بذكاء", g_file]).text
        context.user_data["last_video_content"] = res
        await status_msg.edit_text(res)
        genai.delete_file(g_file.name)
    except Exception as e: await status_msg.edit_text(f"❌ خطأ الفيديو: {e}")
    finally:
        if os.path.exists(path): os.remove(path)

# --- تشغيل البوت ---

def main():
    if not TELEGRAM_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN missing!")
        return
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("clear", clear_chat))
    app.add_handler(CommandHandler("transcribe_last", transcribe_last))
    app.add_handler(CommandHandler("transcribe_video", transcribe_video_cmd))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.Document.PDF, handle_document))
    app.add_handler(MessageHandler(filters.VOICE, handle_voice))
    app.add_handler(MessageHandler(filters.VIDEO | filters.VIDEO_NOTE, handle_video))
    logger.info("Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()