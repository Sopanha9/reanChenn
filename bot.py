import os
import logging
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler

import re
import random
from ai import analyze_chinese_image, ask_chinese_question
import database
import tts

# Quiz states
WAITING_FOR_ANSWER = 1

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a message when the command /start is issued."""
    welcome_message = (
        "👋 Welcome to the Chinese Teacher Bot!\n\n"
        "Send me a photo containing Chinese text, and I will extract the text, "
        "provide pinyin, an English translation, and a word-by-word breakdown!\n\n"
        "You can also ask me any questions about learning Chinese directly as a text message!"
    )
    await update.message.reply_text(welcome_message)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a message when the command /help is issued."""
    help_text = (
        "🤖 *How to use this bot:*\n\n"
        "1. Take a picture or screenshot of some Chinese text.\n"
        "2. Send the photo to this chat to analyze it.\n"
        "3. Or, simply send a text message with your Chinese language questions!\n\n"
        "Commands:\n"
        "/start - Show welcome message\n"
        "/help - Show this help message\n"
        "/save - Save a word. Format: /save Chinese | Pinyin | Meaning\n"
        "/vocab - List all saved words\n"
        "/update - Edit a word. Format: /update ID | Chinese | Pinyin | Meaning\n"
        "/delete - Delete a word. Format: /delete ID\n"
        "/quiz - Start a flashcard quiz\n"
        "/cancel - Stop the current quiz"
    )
    # Using markdown parsing for bolding
    await update.message.reply_markdown(help_text)

async def save_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Save a flashcard to the database."""
    if not context.args:
        await update.message.reply_text("ℹ️ Usage: /save Chinese | Pinyin | Meaning\nExample: /save 你好 | nǐ hǎo | hello")
        return

    text = " ".join(context.args)
    parts = text.split("|")

    if len(parts) != 3:
        await update.message.reply_text("❌ Invalid format! Please use: Chinese | Pinyin | Meaning")
        return

    chinese = parts[0].strip()
    pinyin = parts[1].strip()
    meaning = parts[2].strip()

    try:
        database.save_word(chinese, pinyin, meaning)
        await update.message.reply_text(f"✅ Saved correctly!\n\n🇨🇳 {chinese}\n🗣 {pinyin}\n🇬🇧 {meaning}")
    except Exception as e:
        logger.error(f"Error saving word: {e}")
        await update.message.reply_text("❌ Failed to save the word.")

async def vocab_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """List all saved flashcards."""
    try:
        words = database.get_all_words()

        if not words:
            await update.message.reply_text("You haven't saved any words yet! Use /save to add some.")
            return

        message = "📚 *Your Vocabulary:*\n\n"
        for word in words:
            message += f"ID: {word['id']} | *{word['chinese_word']}* ({word['pinyin']}) - {word['english_meaning']}\n"

        await update.message.reply_markdown(message)
    except Exception as e:
        logger.error(f"Error getting vocab: {e}")
        await update.message.reply_text("❌ Failed to get vocabulary list.")

async def update_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Update an existing flashcard in the database."""
    if not context.args:
        await update.message.reply_text(
            "ℹ️ Usage: /update ID | Chinese | Pinyin | Meaning\n"
            "Example: /update 3 | 你好 | nǐ hǎo | hello\n\n"
            "Use /vocab to see your words and their IDs."
        )
        return

    text = " ".join(context.args)
    parts = text.split("|")

    if len(parts) != 4:
        await update.message.reply_text("❌ Invalid format! Please use: /update ID | Chinese | Pinyin | Meaning")
        return

    try:
        card_id = int(parts[0].strip())
    except ValueError:
        await update.message.reply_text("❌ Invalid ID! The first value must be a number.")
        return

    chinese = parts[1].strip()
    pinyin = parts[2].strip()
    meaning = parts[3].strip()

    if not chinese or not pinyin or not meaning:
        await update.message.reply_text("❌ All fields (Chinese, Pinyin, Meaning) must be non-empty.")
        return

    try:
        old_word = database.get_word_by_id(card_id)
        if not old_word:
            await update.message.reply_text(f"❌ No word found with ID {card_id}. Use /vocab to see your words.")
            return

        success = database.update_word(card_id, chinese, pinyin, meaning)
        if success:
            await update.message.reply_text(
                f"✅ Word updated!\n\n"
                f"*Before:*\n🇨🇳 {old_word['chinese_word']} ({old_word['pinyin']}) - {old_word['english_meaning']}\n\n"
                f"*After:*\n🇨🇳 {chinese} ({pinyin}) - {meaning}",
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_text(f"❌ Failed to update word with ID {card_id}.")
    except Exception as e:
        logger.error(f"Error updating word: {e}")
        await update.message.reply_text("❌ Failed to update the word.")

async def delete_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Delete a flashcard from the database."""
    if not context.args:
        await update.message.reply_text(
            "ℹ️ Usage: /delete ID\n"
            "Example: /delete 3\n\n"
            "Use /vocab to see your words and their IDs."
        )
        return

    try:
        card_id = int(context.args[0].strip())
    except ValueError:
        await update.message.reply_text("❌ Invalid ID! Please provide a valid number.")
        return

    try:
        word = database.get_word_by_id(card_id)
        if not word:
            await update.message.reply_text(f"❌ No word found with ID {card_id}. Use /vocab to see your words.")
            return

        success = database.delete_word(card_id)
        if success:
            await update.message.reply_text(
                f"🗑 Word deleted!\n\n"
                f"🇨🇳 {word['chinese_word']} ({word['pinyin']}) - {word['english_meaning']}"
            )
        else:
            await update.message.reply_text(f"❌ Failed to delete word with ID {card_id}.")
    except Exception as e:
        logger.error(f"Error deleting word: {e}")
        await update.message.reply_text("❌ Failed to delete the word.")

async def quiz_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start the quiz."""
    words = database.get_all_words()
    if not words:
        await update.message.reply_text("You haven't saved any words yet! Use /save to add some before starting a quiz.")
        return ConversationHandler.END

    # Pick a random word
    word = random.choice(words)
    context.user_data['quiz_word'] = word

    await update.message.reply_text(
        f"🎯 *Quiz Time!*\n\nWhat is the English meaning of:\n🇨🇳 *{word['chinese_word']}*\n\nType your answer, or /cancel to stop.",
        parse_mode='Markdown'
    )
    return WAITING_FOR_ANSWER

async def quiz_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Check the user's answer for the quiz."""
    user_answer = update.message.text.lower().strip()
    word = context.user_data.get('quiz_word')

    if not word:
        await update.message.reply_text("Oops, something went wrong. Let's cancel the quiz.", reply_to_message_id=update.message.message_id)
        return ConversationHandler.END

    correct_meaning = word['english_meaning'].lower().strip()

    # Simple check for now, can be improved later
    if user_answer in correct_meaning or correct_meaning in user_answer:
        await update.message.reply_text(f"✅ *Correct!*\n\n🇨🇳 {word['chinese_word']}\n🗣 {word['pinyin']}\n🇬🇧 {word['english_meaning']}", parse_mode='Markdown')
    else:
        await update.message.reply_text(f"❌ *Wrong!*\n\nThe correct answer was:\n🇨🇳 {word['chinese_word']}\n🗣 {word['pinyin']}\n🇬🇧 {word['english_meaning']}", parse_mode='Markdown')

    # Clear user data and end conversation
    context.user_data.pop('quiz_word', None)
    return ConversationHandler.END

async def quiz_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel the quiz."""
    context.user_data.pop('quiz_word', None)
    await update.message.reply_text("Quiz cancelled. Send /quiz when you're ready to try again!")
    return ConversationHandler.END

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle incoming photos and analyze them using Gemini."""
    processing_message = await update.message.reply_text("⏳ Analyzing image, please wait...")

    try:
        # Get the highest resolution photo (the last one in the list)
        photo_file = await update.message.photo[-1].get_file()

        # Download the photo as a bytearray
        image_bytes = await photo_file.download_as_bytearray()

        # Analyze the image bytes
        result = analyze_chinese_image(bytes(image_bytes))

        # Edit the processing message with the result
        await processing_message.edit_text(result)

        # Extract the original Chinese text using regex
        # We need to find the text between "🇨🇳 *Original Text*\n" and the next "\n\n"
        chinese_match = re.search(r"🇨🇳 \*Original Text\*\n(.*?)(?=\n\n|$)", result, re.DOTALL)

        if chinese_match:
            chinese_text = chinese_match.group(1).strip()
            # Remove any markdown artifacts if present
            chinese_text = chinese_text.replace('*', '').replace('_', '')

            if chinese_text:
                # Generate audio
                audio_path = tts.speak_chinese(chinese_text)
                if audio_path and os.path.exists(audio_path):
                    # Send the audio
                    with open(audio_path, 'rb') as audio_file:
                        await context.bot.send_voice(chat_id=update.effective_chat.id, voice=audio_file)

                    # Clean up the temp file
                    os.remove(audio_path)
            else:
                 logger.warning("Could not parse Chinese text for TTS.")

    except Exception as e:
        logger.error(f"Error processing photo: {e}")
        error_msg = f"❌ Sorry, an error occurred while processing your image: {str(e)}"
        await processing_message.edit_text(error_msg)

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle text messages by asking Gemini."""
    user_question = update.message.text
    if not user_question:
         return

    processing_message = await update.message.reply_text("🤔 Thinking...")

    try:
        # Ask the question
        result = ask_chinese_question(user_question)

        # Reply with the result
        await processing_message.edit_text(result)

    except Exception as e:
        logger.error(f"Error processing question: {e}")
        error_msg = f"❌ Sorry, an error occurred while answering your question: {str(e)}"
        await processing_message.edit_text(error_msg)

def main():
    """Start the bot."""
    token = os.getenv("TELEGRAM_TOKEN")
    if not token:
        logger.error("TELEGRAM_TOKEN not found in .env file! Please set it and restart.")
        return

    # Initialize the database
    database.init_db()

    application = ApplicationBuilder().token(token).build()

    # Quiz ConversationHandler
    quiz_handler = ConversationHandler(
        entry_points=[CommandHandler("quiz", quiz_start)],
        states={
            WAITING_FOR_ANSWER: [MessageHandler(filters.TEXT & ~(filters.COMMAND), quiz_answer)]
        },
        fallbacks=[CommandHandler("cancel", quiz_cancel)]
    )
    application.add_handler(quiz_handler)

    # Commands
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("save", save_command))
    application.add_handler(CommandHandler("vocab", vocab_command))
    application.add_handler(CommandHandler("update", update_command))
    application.add_handler(CommandHandler("delete", delete_command))

    # Photo handler
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))

    # Text handler
    application.add_handler(MessageHandler(filters.TEXT & ~(filters.COMMAND), handle_text))

    print("ChinesePhobia Bot is running...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
