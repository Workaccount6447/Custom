import json
import logging
import re
import aiohttp
from aiogram import types, filters
from bot import dp
from config import Config
from models import models
from telegramify_markdown import standardize as telegramify_markdown_standardize
from telegramify_markdown.customize import get_runtime_config

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configure markdown styling
config = get_runtime_config()
config.markdown_symbol.head_level_1 = "📌"
config.markdown_symbol.link = "🔗"
config.cite_expandable = True
config._strict_markdown = True
config.unescape_html = False

user_selected_models = {}
user_chat_ids = set()


def get_model_info(user_message):
    for model in models:
        model_id_command = f"/{model.model_id.split('/')[1].split(':')[0].replace('-', '').replace('.', '').lower()}"
        if user_message == model_id_command:
            return model
    return None


def split_message(text, chunk_size=4000):
    return [text[i:i + chunk_size] for i in range(0, len(text), chunk_size)]


async def send_openrouter_request(message, openrouter_api_key, selected_model, user_message):
    try:
        async with aiohttp.ClientSession() as session:
            response = await session.post(
                url="https://openrouter.ai/api/v1/chat/completions",
                headers={"Authorization": f"Bearer {openrouter_api_key}"},
                json={
                    "model": selected_model.model_id,
                    "messages": [{"role": "user", "content": user_message}],
                    "top_p": 1,
                    "temperature": 0.9,
                    "frequency_penalty": 0,
                    "presence_penalty": 0,
                    "repetition_penalty": 1,
                    "top_k": 0,
                }
            )

            if response.status == 200:
                try:
                    response_json = await response.json()
                    bot_response = response_json.get('choices', [{}])[0].get('message', {}).get('content', '')
                    formatted_response = telegramify_markdown_standardize(bot_response)
                    response_chunks = split_message(formatted_response.strip())
                    for chunk in response_chunks:
                        await message.answer(chunk, parse_mode="MarkdownV2")
                except json.JSONDecodeError:
                    await message.answer("Sorry, I received an invalid JSON response.")
            else:
                logger.error(await response.text())
                await message.answer(f"Error occurred. Status code: {response.status}")
    except Exception as e:
        logger.exception("Unexpected error during OpenRouter request")
        await message.answer(f"An unexpected error occurred: {str(e)}")


def list_available_models():
    return [
        (
            model.model_id.split('/')[1].split(':')[0].replace('-', '').replace('.', '').lower(),
            f"{model.name.split(':')[0]}: {model.name.split(':')[1]}"
        ) for model in models
    ]


@dp.message_handler(filters.Command(commands=["start"], prefixes="!/", ignore_case=False))
async def start(message: types.Message):
    welcome_text = (
        "Hi, I am your AI assistant! 🤖\n"
        "Please select a model from the /models list using /models.\n"
        "To select a model, send its corresponding command (e.g., `/qwq32b`)."
    )
    await message.answer(welcome_text, parse_mode='MarkdownV2')
    if message.chat.id in user_selected_models:
        del user_selected_models[message.chat.id]


@dp.message_handler(filters.Command(commands=["models"], prefixes="!/", ignore_case=False))
async def list_models(message: types.Message):
    available_models = list_available_models()
    model_list = [f"/{model_id} {name}" for model_id, name in available_models]
    await message.answer(
        f"Available models:\n{chr(10).join(model_list)}\n\nTo select a model, send its corresponding command (e.g., `/mistralsmall3124binstruct`).",
        parse_mode='MarkdownV2'
    )


@dp.message_handler(filters.Command(commands=["privacypolicy"], prefixes="!/", ignore_case=False))
async def privacy_policy(message: types.Message):
    await message.answer("🔐 We ensure your privacy.")


@dp.message_handler(filters.Command(commands=["ownerannouncement"], prefixes="!/", ignore_case=False))
async def owner_announcement(message: types.Message):
    if message.from_user.id != Config.OWNER_ID:
        await message.answer("❌ You are not authorized to use this command.")
        return

    announcement = message.text.partition(" ")[2]
    if not announcement:
        await message.answer("⚠️ Please provide an announcement message after the command.")
        return

    for user_id in user_chat_ids:
        try:
            await message.bot.send_message(chat_id=user_id, text=f"📢 Announcement:\n{announcement}")
        except Exception as e:
            logger.warning(f"Failed to send to {user_id}: {e}")

    await message.answer("✅ Announcement sent to all users.")


@dp.message_handler()
async def respond_to_message(message: types.Message):
    chat_id = message.chat.id
    user_chat_ids.add(chat_id)

    user_message = message.text
    if user_message.lower() == 'exit':
        await message.answer("Goodbye! Feel free to start a new chat anytime.")
        if chat_id in user_selected_models:
            del user_selected_models[chat_id]
        return

    cleaned_user_message = re.sub(r'[\s.:,]', '', user_message).lower()
    selected_model = get_model_info(cleaned_user_message)
    if selected_model:
        user_selected_models[chat_id] = selected_model
        await message.answer(f"You selected: {selected_model.name}\n{selected_model.description}")
    elif chat_id in user_selected_models:
        await send_openrouter_request(
            message=message,
            openrouter_api_key=Config.OPENROUTER_API_KEY,
            selected_model=user_selected_models[chat_id],
            user_message=user_message
        )
    else:
        await message.answer("I'm not sure how to respond to that. Use /models to select a model.")
