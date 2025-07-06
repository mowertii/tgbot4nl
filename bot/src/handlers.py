# bot/src/handlers.py
from aiogram import Router, types

router = Router()

@router.message(lambda message: message.text and message.text.lower() == '/start')
async def welcome_handler(message: types.Message):
    await message.reply("Добро пожаловать на канал о здоровом питании и правильных привычках.")

@router.message()
async def faq_handler(message: types.Message):
    text = message.text.lower()
    if "как подписаться" in text:
        await message.reply("Чтобы подписаться на канал, нажмите кнопку «Подписаться» вверху экрана.")
    elif "где найти рецепты" in text:
        await message.reply("Рецепты вы найдёте в закреплённых сообщениях нашего канала.")
    else:
        # здесь в будущем будет интеграция с LM
        await message.reply("Спасибо за вопрос! В скором времени я смогу на него ответить.")

