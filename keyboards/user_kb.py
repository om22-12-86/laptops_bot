from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# Клавиатура для пользователя с кнопками в 2 столбца
user_menu = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Каталог", callback_data="catalog"), InlineKeyboardButton(text="Корзина", callback_data="cart")],
    [InlineKeyboardButton(text="О нас", callback_data="about"), InlineKeyboardButton(text="Заказы", callback_data="orders")],
    [InlineKeyboardButton(text="Связаться с нами", callback_data="contact"), InlineKeyboardButton(text="Доставка", callback_data="delivery")]
])

# Клавиатура для категорий (Каталог)
def get_categories_keyboard(categories):
    keyboard = []

    # Создаём кнопки категорий в 2 столбца
    row = []
    for category in categories:
        row.append(InlineKeyboardButton(text=category.name, callback_data=f"category_{category.id}"))
        if len(row) == 2:
            keyboard.append(row)
            row = []

    if row:
        keyboard.append(row)

    # Добавляем кнопки "Назад" и "Корзина"
    keyboard.append([
        InlineKeyboardButton(text="⬅️ Назад", callback_data="main_menu"),
        InlineKeyboardButton(text="🛒 Корзина", callback_data="cart")
    ])
    keyboard.append([
        InlineKeyboardButton(text="🔍 Поиск", callback_data="search")
    ])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)

# Клавиатура для подкатегорий
def get_subcategories_keyboard(subcategories):
    keyboard = []

    # Создаём кнопки подкатегорий в 2 столбца
    row = []
    for subcategory in subcategories:
        row.append(InlineKeyboardButton(text=subcategory.name, callback_data=f"subcategory_{subcategory.id}"))
        if len(row) == 2:
            keyboard.append(row)
            row = []

    if row:
        keyboard.append(row)

    # Кнопка "Назад" для возврата к категориям
    keyboard.append([
        InlineKeyboardButton(text="⬅️ Назад", callback_data="catalog")
    ])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_cart_keyboard(cart_items: list, current_index: int = 0):
    buttons = []

    # Кнопки управления количеством
    buttons.append([
        InlineKeyboardButton(text="➖", callback_data=f"decrease_{cart_items[current_index].product_id}"),
        InlineKeyboardButton(text="➕", callback_data=f"increase_{cart_items[current_index].product_id}")
    ])

    # Кнопки навигации
    nav_buttons = []
    if len(cart_items) > 1:
        nav_buttons.append(InlineKeyboardButton(text="⬅️", callback_data=f"prev_cart_item_{current_index}"))
        nav_buttons.append(InlineKeyboardButton(text=f"{current_index + 1}/{len(cart_items)}", callback_data="none"))
        nav_buttons.append(InlineKeyboardButton(text="➡️", callback_data=f"next_cart_item_{current_index}"))
        buttons.append(nav_buttons)

    # Другие кнопки
    buttons.append([
        InlineKeyboardButton(text="🛒 Оформить заказ", callback_data="place_order_user"),
        InlineKeyboardButton(text="⬅️ В меню", callback_data="main_menu")
    ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)




# Клавиатура для пустой корзины
def get_empty_cart_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="main_menu")]
    ])

# Клавиатура для товара
def get_product_keyboard(product_id: int, page: int, total_products: int, subcategory_id: int):
    buttons = [
        [InlineKeyboardButton(text="⬅️ Назад", callback_data=f"back_to_subcategory_{subcategory_id}"),
         InlineKeyboardButton(text="🛒 Корзина", callback_data="cart")],
        [InlineKeyboardButton(text="📷 ФОТО", callback_data=f"product_images_{product_id}"),
         InlineKeyboardButton(text="📊 ТЕХ/ПАР", callback_data=f"product_specs_{product_id}")],
        [InlineKeyboardButton(text="☑️ Добавить в корзину", callback_data=f"buy_product_{product_id}")]
    ]

    # Добавляем кнопки навигации
    navigation_buttons = []
    if page > 0:
        navigation_buttons.append(InlineKeyboardButton(text="⬅️ Предыдущий", callback_data=f"prev_product_{subcategory_id}_{page - 1}"))
    if page < total_products - 1:
        navigation_buttons.append(InlineKeyboardButton(text="➡️ Следующий", callback_data=f"next_product_{subcategory_id}_{page + 1}"))

    if navigation_buttons:
        buttons.append(navigation_buttons)

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_search_results_keyboard(product_id: int, current_index: int, total: int, query: str):
    buttons = [
        [
            InlineKeyboardButton(text="⬅️ Назад", callback_data="catalog"),
            InlineKeyboardButton(text="🛒 Корзина", callback_data="cart")
        ],
        [
            InlineKeyboardButton(text="📷 Фото", callback_data=f"product_images_{product_id}"),
            InlineKeyboardButton(text="📊 Характеристики", callback_data=f"product_specs_{product_id}")
        ],
        [
            InlineKeyboardButton(text="🛍️ В корзину", callback_data=f"buy_product_{product_id}")
        ]
    ]

    # Кнопки навигации
    nav_buttons = []
    if current_index > 0:
        nav_buttons.append(InlineKeyboardButton(
            text="⬅️ Пред.",
            callback_data=f"prev_search_{query}_{current_index - 1}"
        ))

    nav_buttons.append(InlineKeyboardButton(
        text=f"{current_index + 1}/{total}",
        callback_data="none"
    ))

    if current_index < total - 1:
        nav_buttons.append(InlineKeyboardButton(
            text="След. ➡️",
            callback_data=f"next_search_{query}_{current_index + 1}"
        ))

    if nav_buttons:
        buttons.append(nav_buttons)

    return InlineKeyboardMarkup(inline_keyboard=buttons)




# Клавиатура для фотографий товара
def get_product_images_keyboard(product_id: int, query: str, current_index: int):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Назад к результатам", callback_data=f"back_to_search_{query}_{current_index}")]
    ])

# Клавиатура для характеристик товара
def get_product_specs_keyboard(product_id: int, query: str, current_index: int):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Назад к результатам", callback_data=f"back_to_search_{query}_{current_index}")]
    ])