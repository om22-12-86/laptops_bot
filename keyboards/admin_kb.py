from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

# Reply-клавиатура для админа (2 столбца)
admin_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Создать/Изменить баннер"), KeyboardButton(text="Добавить/Изменить категорию")],
        [KeyboardButton(text="Добавить/Изменить товар")],
        [KeyboardButton(text="Добавить данные для товара"), KeyboardButton(text="Заказы")],
        [KeyboardButton(text="История заказов"), KeyboardButton(text="Наличие товара")],
        [KeyboardButton(text="🔍 Поиск"), KeyboardButton(text="Отмена")]  # Добавили кнопку отмены
    ],
    resize_keyboard=True
)
