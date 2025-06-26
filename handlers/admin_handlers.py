from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from keyboards.admin_kb import admin_menu
from database.crud import (
    get_user_by_id, create_product, create_banner, get_banner, get_categories, get_order_items, update_order_status, delete_order,
    update_banner, create_category, get_product_by_sku, create_product_image, get_all_orders, get_orders,
    create_order, restore_order, get_subcategories_by_category_id, get_products_by_subcategory_id,
    update_product_stock_status, get_cart_items
)
from database.database import AsyncSessionLocal
from aiogram.fsm.state import State, StatesGroup
from utils.utils import is_admin
from aiogram import Bot
from sqlalchemy import select, delete
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from database.models import Category, Product, ProductImage, ProductSpecification, Order, OrderItem, OrderStatus, User

import logging

router = Router()

async def delete_previous_message(message_or_callback):
    """Удаляет предыдущее сообщение."""
    try:
        if isinstance(message_or_callback, types.CallbackQuery):
            await message_or_callback.message.delete()
        elif isinstance(message_or_callback, types.Message):
            await message_or_callback.delete()
    except Exception as e:
        print(f"Ошибка при удалении сообщения: {e}")

# Статусы для добавления товара
class AddProduct(StatesGroup):
    name = State()
    description = State()
    price = State()
    image_url = State()
    file_type = State()
    sku = State()
    category_id = State()

# Статусы для изменения товара
class EditProduct(StatesGroup):
    sku = State()  # Артикул товара
    name = State()
    description = State()
    price = State()
    image_url = State()
    file_type = State()
    category_id = State()

# Статусы для добавления баннера
class AddBanner(StatesGroup):
    image_url = State()
    title = State()
    description = State()
    type = State()

# Статусы для добавления данных для товара
class AddProductData(StatesGroup):
    sku = State()  # Артикул товара
    specs_text = State()  # Текст с характеристиками
    product_images = State()  # Фотографии товара

# Добавьте этот класс
class EditSpecs(StatesGroup):
    sku = State()  # Артикул товара
    specs_text = State()  # Новые характеристики

class DeleteSpecs(StatesGroup):
    sku = State()  # Артикул товара

# Определяем состояние для ввода ID пользователя
class OrderState(StatesGroup):
    waiting_for_user_id = State()

# Состояния для изменения статуса товара
class UpdateStockStatus(StatesGroup):
    product_sku = State()  # Артикул товара
    stock_status = State()  # Новый статус наличия

# Определяем состояние для поиска товара
class SearchProduct(StatesGroup):
    query = State()  # Ожидаем ввод артикул/бренд

# Словарь для перевода статусов заказа
ORDER_STATUS_TRANSLATION = {
    OrderStatus.PROCESSING: "В обработке",
    OrderStatus.READY_FOR_PICKUP: "Готов к получению",
    OrderStatus.COMPLETED: "Выдан",
    OrderStatus.CANCELLED: "Отменен",
}


# Команда для доступа в админ-панель
@router.message(Command("admin"))
async def admin_panel(message: types.Message, bot: Bot):
    if await is_admin(bot, message.from_user.id):
        await message.answer("Админ-панель", reply_markup=admin_menu)
    else:
        await message.answer("У вас нет доступа к админ-панели.")

# Команда для выхода из админ-панели
@router.message(F.text == "Выйти из админ-панели")
async def exit_admin_panel(message: types.Message):
    await message.answer("Вы вышли из админ-панели.", reply_markup=user_menu)

# Команда для добавления товара
@router.message(F.text == "Добавить/Изменить товар")
async def add_product_start(message: types.Message, state: FSMContext):
    await delete_previous_message(message)
    await message.answer("Введите название товара:")
    await state.set_state(AddProduct.name)

@router.message(AddProduct.name)
async def add_product_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("Введите описание товара:")
    await state.set_state(AddProduct.description)

@router.message(AddProduct.description)
async def add_product_description(message: types.Message, state: FSMContext):
    await state.update_data(description=message.text)
    await message.answer("Введите цену товара:")
    await state.set_state(AddProduct.price)

@router.message(AddProduct.price)
async def add_product_price(message: types.Message, state: FSMContext):
    try:
        await state.update_data(price=float(message.text))
        await message.answer("Отправьте изображение или гифку товара:")
        await state.set_state(AddProduct.image_url)
    except ValueError:
        await message.answer("Введите корректную цену.")

@router.message(AddProduct.image_url)
async def add_product_image_url(message: types.Message, state: FSMContext):
    if message.photo:
        file_id = message.photo[-1].file_id
        file_type = "photo"
    elif message.animation:
        file_id = message.animation.file_id
        file_type = "animation"
    else:
        await message.answer("Пожалуйста, отправьте изображение или гифку.")
        return

    await state.update_data(image_url=file_id, file_type=file_type)
    await message.answer("Введите артикул товара (SKU):")
    await state.set_state(AddProduct.sku)

@router.message(AddProduct.sku)
async def add_product_sku(message: types.Message, state: FSMContext):
    await state.update_data(sku=message.text)
    await message.answer("Введите ID подкатегории товара:")
    await state.set_state(AddProduct.category_id)

@router.message(AddProduct.category_id)
async def add_product_category_id(message: types.Message, state: FSMContext):
    try:
        subcategory_id = int(message.text)
        data = await state.get_data()

        async with AsyncSessionLocal() as session:
            await create_product(
                session,
                name=data.get('name'),
                description=data.get('description'),
                price=data.get('price'),
                image_url=data.get('image_url'),
                file_type=data.get('file_type'),
                sku=data.get('sku'),
                subcategory_id=subcategory_id
            )

        await message.answer("Товар успешно добавлен!", reply_markup=admin_menu)
        await state.clear()  # Очищаем состояние после успешного добавления
    except ValueError:
        await message.answer("Введите корректный ID подкатегории.", reply_markup=admin_menu)


# Команда для изменения товара
@router.message(F.text == "Изменить товар")
async def edit_product_start(message: types.Message, state: FSMContext):
    await delete_previous_message(message)
    await message.answer("Введите артикул (SKU) товара, который хотите изменить:")
    await state.set_state(EditProduct.sku)

@router.message(EditProduct.sku)
async def edit_product_sku(message: types.Message, state: FSMContext):
    sku = message.text
    await state.update_data(sku=sku)
    await message.answer("Введите новое название товара (или '.' чтобы оставить без изменений):")
    await state.set_state(EditProduct.name)

@router.message(EditProduct.name)
async def edit_product_name(message: types.Message, state: FSMContext):
    if message.text == ".":  # Если введена точка, пропускаем изменение
        await message.answer("Название товара осталось без изменений.")
    else:
        await state.update_data(name=message.text)  # Обновляем название, если введено не "."
    await message.answer("Введите новое описание товара (или '.' чтобы оставить без изменений):")
    await state.set_state(EditProduct.description)


@router.message(EditProduct.description)
async def edit_product_description(message: types.Message, state: FSMContext):
    if message.text != ".":  # Если введена не точка, обновляем описание
        await state.update_data(description=message.text)
    await message.answer("Введите новую цену товара (или '.' чтобы оставить без изменений):")
    await state.set_state(EditProduct.price)

@router.message(EditProduct.price)
async def edit_product_price(message: types.Message, state: FSMContext):
    if message.text != ".":  # Если введена не точка, обновляем цену
        try:
            await state.update_data(price=float(message.text))
        except ValueError:
            await message.answer("Введите корректную цену.")
            return
    await message.answer("Отправьте новое изображение или гифку товара (или '.' чтобы оставить без изменений):")
    await state.set_state(EditProduct.image_url)

@router.message(EditProduct.image_url)
async def edit_product_image_url(message: types.Message, state: FSMContext):
    if message.text != ".":  # Если введена не точка, обновляем изображение
        if message.photo:
            file_id = message.photo[-1].file_id
            file_type = "photo"
        elif message.animation:
            file_id = message.animation.file_id
            file_type = "animation"
        else:
            await message.answer("Пожалуйста, отправьте изображение или гифку.")
            return

        await state.update_data(image_url=file_id, file_type=file_type)
    await message.answer("Введите новый ID подкатегории товара (или '.' чтобы оставить без изменений):")
    await state.set_state(EditProduct.category_id)

@router.message(EditProduct.category_id)
async def edit_product_category_id(message: types.Message, state: FSMContext):
    data = await state.get_data()
    sku = data.get('sku')  # Получаем sku из состояния

    async with AsyncSessionLocal() as session:
        # Ищем товар по sku
        product = await get_product_by_sku(session, sku)

        if not product:
            await message.answer("Товар с таким артикулом не найден!", reply_markup=admin_menu)
            await state.clear()
            return

        # Обновляем поля товара, если они были изменены
        if 'name' in data:
            product.name = data.get('name')
        if 'description' in data:
            product.description = data.get('description')
        if 'price' in data:
            product.price = data.get('price')
        if 'image_url' in data:
            product.image_url = data.get('image_url')
        if 'file_type' in data:
            product.file_type = data.get('file_type')
        if message.text != ".":  # Если введена не точка, обновляем подкатегорию
            try:
                product.subcategory_id = int(message.text)
            except ValueError:
                await message.answer("Введите корректный ID подкатегории.", reply_markup=admin_menu)
                return

        await session.commit()

    await message.answer("Товар успешно изменен!", reply_markup=admin_menu)
    await state.clear()

# Команда для создания/изменения баннера
@router.message(F.text == "Создать/Изменить баннер")
async def add_banner_start(message: types.Message, state: FSMContext):
    await state.clear()  # Очищаем состояние перед началом работы с баннерами
    await delete_previous_message(message)
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Главная страница", callback_data="admin_main_menu")],
        [InlineKeyboardButton(text="Каталог", callback_data="admin_catalog")],
        [InlineKeyboardButton(text="О нас", callback_data="admin_about")],
        [InlineKeyboardButton(text="Контакты", callback_data="admin_contact")],
        [InlineKeyboardButton(text="Корзина", callback_data="admin_cart")],
        [InlineKeyboardButton(text="Заказы", callback_data="admin_orders")],
        [InlineKeyboardButton(text="Доставка", callback_data="admin_delivery")],
        [InlineKeyboardButton(text="Ноутбуки", callback_data="admin_laptops")]
    ])
    await message.answer("Выберите место для добавления баннера:", reply_markup=keyboard)


@router.message(F.text.lower().in_(["отмена", "."]))
async def cancel_handler(message: types.Message, state: FSMContext):
    await state.clear()  # Сбрасываем текущее состояние
    await message.answer("Действие отменено. Возврат в админ-панель.", reply_markup=admin_menu)

# Обработчик для получения выбора места и перехода к загрузке изображения
@router.callback_query(F.data.startswith("admin_"))
async def select_banner_place(callback: types.CallbackQuery, state: FSMContext):
    await delete_previous_message(callback.message)
    banner_type = callback.data.replace("admin_", "")
    await state.update_data(banner_type=banner_type)
    await callback.message.answer("Отправьте изображение или гифку для баннера:")
    await state.set_state(AddBanner.image_url)

# Шаг 2: Получаем изображение или гифку
@router.message(AddBanner.image_url)
async def add_banner_image_url(message: types.Message, state: FSMContext):
    if message.text.lower() == "отмена":  # Обработка команды "отмена"
        await state.clear()
        await message.answer("Действие отменено. Возврат в админ-панель.", reply_markup=admin_menu)
        return

    if message.photo:
        file_id = message.photo[-1].file_id
        file_type = "photo"
    elif message.animation:
        file_id = message.animation.file_id
        file_type = "animation"
    else:
        await message.answer("Пожалуйста, отправьте изображение или гифку.")
        return

    await state.update_data(image_url=file_id, file_type=file_type)
    await message.answer("Введите заголовок баннера (или '.' чтобы оставить без изменений):")
    await state.set_state(AddBanner.title)

@router.message(AddBanner.title)
async def add_banner_title(message: types.Message, state: FSMContext):
    if message.text == ".":  # Если введена точка, пропускаем изменение
        await message.answer("Заголовок баннера остался без изменений.")
    else:
        await state.update_data(title=message.text)  # Обновляем заголовок, если введено не "."
    await message.answer("Теперь отправьте описание для баннера (или '.' чтобы оставить без изменений).")
    await state.set_state(AddBanner.description)

# Шаг 3: Ввод заголовка баннера
@router.message(AddBanner.title)
async def add_banner_title(message: types.Message, state: FSMContext):
    await state.update_data(title=message.text)
    await message.answer("Теперь отправьте описание для баннера.")
    await state.set_state(AddBanner.description)

# Шаг 4: Ввод описания баннера
@router.message(AddBanner.description)
async def add_banner_description(message: types.Message, state: FSMContext):
    data = await state.get_data()
    image_url = data.get('image_url')
    title = data.get('title')
    description = message.text
    banner_type = data.get('banner_type')
    file_type = data.get('file_type')

    if not image_url or not title or not description or not banner_type or not file_type:
        await message.answer("Ошибка! Одно из полей не было заполнено.", reply_markup=admin_menu)
        return

    async with AsyncSessionLocal() as session:
        try:
            await update_banner(
                session,
                title=title,
                image_url=image_url,
                description=description,
                banner_type=banner_type,
                file_type=file_type
            )
            await message.answer("Баннер успешно обновлен!", reply_markup=admin_menu)
        except Exception as e:
            await message.answer(f"Ошибка при обновлении баннера: {e}", reply_markup=admin_menu)

    await state.clear()

# Статусы для добавления категории
class AddCategory(StatesGroup):
    name = State()

# Обработчик для кнопки "Добавить/Изменить категорию"
@router.message(F.text == "Добавить/Изменить категорию")
async def add_category_start(message: types.Message, state: FSMContext):
    await delete_previous_message(message)
    await message.answer("Введите название категории:")
    await state.set_state(AddCategory.name)

@router.message(AddCategory.name)
async def add_category_name(message: types.Message, state: FSMContext):
    if message.text.lower() == "отмена":  # Обработка команды "отмена"
        await state.clear()
        await message.answer("Действие отменено. Возврат в админ-панель.", reply_markup=admin_menu)
        return

    category_name = message.text

    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Category).where(Category.name == category_name))
        existing_category = result.scalars().first()

        if existing_category:
            await message.answer(f"Категория '{category_name}' уже существует!", reply_markup=admin_menu)
        else:
            await create_category(session, category_name)
            await message.answer(f"Категория '{category_name}' успешно создана!", reply_markup=admin_menu)

    await state.clear()



# Обработчик для кнопки "Добавить данные для товара"
@router.message(F.text == "Добавить данные для товара")
async def add_product_data_start(message: types.Message, state: FSMContext):
    await delete_previous_message(message)
    await message.answer("Введите артикул (SKU) товара, для которого хотите добавить данные:")
    await state.set_state(AddProductData.sku)

@router.message(AddProductData.sku)
async def add_product_data_sku(message: types.Message, state: FSMContext):
    sku = message.text
    await state.update_data(sku=sku)
    await message.answer("Введите характеристики товара в формате:\n\n"
                         "Ключ1: Значение1\n"
                         "Ключ2: Значение2\n"
                         "Ключ3: Значение3\n\n"
                         "Пример:\n"
                         "Процессор: Intel Core i7-13620H\n"
                         "Оперативная память: 16 ГБ\n"
                         "Тип видеокарты: NVIDIA GeForce RTX 4060")
    await state.set_state(AddProductData.specs_text)

@router.message(AddProductData.specs_text)
async def add_product_data_specs_text(message: types.Message, state: FSMContext):
    data = await state.get_data()
    sku = data.get('sku')  # Получаем sku из состояния
    specs_text = message.text  # Получаем текст с характеристиками

    async with AsyncSessionLocal() as session:
        # Ищем товар по sku
        product = await get_product_by_sku(session, sku)

        if not product:
            await message.answer("Товар с таким артикулом не найден!", reply_markup=admin_menu)
            await state.clear()
            return

        # Разбиваем текст на строки
        lines = specs_text.split('\n')
        for line in lines:
            if ':' in line:
                key, value = line.split(':', 1)  # Разделяем по первому символу ':'
                key = key.strip()  # Убираем лишние пробелы
                value = value.strip()

                # Добавляем характеристику товара
                product_spec = ProductSpecification(
                    product_id=product.id,  # Используем id товара, найденного по sku
                    key=key,
                    value=value
                )
                session.add(product_spec)

        await session.commit()

    await message.answer("Характеристики для товара успешно добавлены! Теперь отправьте фотографии товара.")
    await state.set_state(AddProductData.product_images)

@router.message(AddProductData.product_images)
async def add_product_data_images(message: types.Message, state: FSMContext):
    data = await state.get_data()
    sku = data.get('sku')  # Получаем sku из состояния

    if message.photo:
        file_id = message.photo[-1].file_id
        file_type = "photo"
    elif message.animation:
        file_id = message.animation.file_id
        file_type = "animation"
    else:
        await message.answer("Пожалуйста, отправьте изображение или гифку.")
        return

    async with AsyncSessionLocal() as session:
        # Ищем товар по sku
        product = await get_product_by_sku(session, sku)

        if not product:
            await message.answer("Товар с таким артикулом не найден!", reply_markup=admin_menu)
            await state.clear()
            return

        # Добавляем изображение товара
        product_image = ProductImage(
            product_id=product.id,
            image_url=file_id,
            file_type=file_type
        )
        session.add(product_image)
        await session.commit()

    await message.answer("Фотография товара успешно добавлена! Отправьте ещё фотографии или нажмите /done для завершения.")

@router.message(Command("done"))
async def finish_adding_images(message: types.Message, state: FSMContext):
    await message.answer("Добавление данных для товара завершено!", reply_markup=admin_menu)
    await state.clear()





# Обработчик для кнопки "Ассортимент" (админская версия)
@router.message(F.text == "Ассортимент")
async def show_admin_assortment(message: types.Message):
    await delete_previous_message(message)
    async with AsyncSessionLocal() as session:
        categories = await get_categories(session)  # Получаем список категорий
        if categories:
            # Создаем клавиатуру с кнопками для каждой категории в два столбца
            keyboard_buttons = []
            for i in range(0, len(categories), 2):
                row = []
                if i < len(categories):
                    row.append(InlineKeyboardButton(text=categories[i].name, callback_data=f"admin_category_{categories[i].id}"))
                if i + 1 < len(categories):
                    row.append(InlineKeyboardButton(text=categories[i + 1].name, callback_data=f"admin_category_{categories[i + 1].id}"))
                keyboard_buttons.append(row)

            keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
            await message.answer("Выберите категорию:", reply_markup=keyboard)
        else:
            await message.answer("Категории не найдены.", reply_markup=admin_menu)




# Обработчик для выбора категории (админская версия)
@router.callback_query(F.data.startswith("admin_category_"))
async def show_admin_subcategories(callback: types.CallbackQuery):
    await delete_previous_message(callback)  # Удаляем предыдущее сообщение
    category_id = int(callback.data.replace("admin_category_", ""))  # Получаем ID категории
    async with AsyncSessionLocal() as session:
        subcategories = await get_subcategories_by_category_id(session, category_id)  # Получаем подкатегории
        if subcategories:
            # Создаем клавиатуру с кнопками для каждой подкатегории в два столбца
            keyboard_buttons = []
            for i in range(0, len(subcategories), 2):
                row = []
                if i < len(subcategories):
                    row.append(InlineKeyboardButton(text=subcategories[i].name, callback_data=f"admin_subcategory_{subcategories[i].id}"))
                if i + 1 < len(subcategories):
                    row.append(InlineKeyboardButton(text=subcategories[i + 1].name, callback_data=f"admin_subcategory_{subcategories[i + 1].id}"))
                keyboard_buttons.append(row)

            keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
            await callback.message.answer("Выберите подкатегорию:", reply_markup=keyboard)
        else:
            # Если подкатегорий нет, сразу показываем товары в категории
            await show_admin_products_in_category(callback, category_id)


# Обработчик для отображения товаров в подкатегории (админская версия)
@router.callback_query(F.data.startswith("admin_subcategory_"))
async def show_admin_products_in_category(callback: types.CallbackQuery):
    await delete_previous_message(callback)  # Удаляем предыдущее сообщение
    subcategory_id = int(callback.data.replace("admin_subcategory_", ""))  # Получаем ID подкатегории
    async with AsyncSessionLocal() as session:
        products = await get_products_by_subcategory_id(session, subcategory_id)  # Получаем товары по подкатегории
        if products:
            await show_admin_products_page(callback.message, products, 0)  # Показываем товары с пагинацией
        else:
            await callback.message.answer("Товары в этой подкатегории отсутствуют.", reply_markup=admin_menu)



@router.callback_query(F.data.startswith("delete_product_"))
async def delete_product_handler(callback: types.CallbackQuery):
    product_id = int(callback.data.replace("delete_product_", ""))
    async with AsyncSessionLocal() as session:
        product = await session.get(Product, product_id)
        if product:
            await session.delete(product)
            await session.commit()
            await callback.answer("Товар успешно удален.", show_alert=True)
        else:
            await callback.answer("Товар не найден.", show_alert=True)

@router.callback_query(F.data.startswith("edit_product_"))
async def edit_product_handler(callback: types.CallbackQuery, state: FSMContext):
    product_id = int(callback.data.replace("edit_product_", ""))
    await state.update_data(product_id=product_id)
    await callback.message.answer("Введите новое название товара (или '.' чтобы оставить без изменений):")
    await state.set_state(EditProduct.name)


# Функция для отображения товаров с админскими кнопками
async def show_admin_products_page(message: types.Message, products: list[Product], page: int):
    start_index = page * 5
    end_index = start_index + 5
    products_to_show = products[start_index:end_index]

    if not products_to_show:
        await message.answer("Товары закончились.", reply_markup=admin_menu)
        return

    for product in products_to_show:
        product_text = (
            f"🔹 Название: {product.name}\n"
            f"🔹 Описание: {product.description}\n"
            f"🔹 Цена: {product.price} руб.\n"
            f"🔹 Артикул: {product.sku}\n"
            f"🔹 Наличие: {'В наличии' if product.in_stock else 'Ожидаем'}\n"
        )

        # Создаем кнопки для админа
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="Удалить", callback_data=f"admin_delete_product_{product.id}"),
                InlineKeyboardButton(text="Изменить", callback_data=f"admin_edit_product_{product.id}")
            ],
            [
                InlineKeyboardButton(text="Изменить наличие", callback_data=f"admin_update_stock_{product.id}")
            ]
        ])

        # Проверяем, что image_url является file_id
        if product.image_url and product.image_url.startswith("AgAC"):  # Пример проверки file_id
            if product.file_type == "photo":
                await message.answer_photo(
                    photo=product.image_url,
                    caption=product_text,
                    reply_markup=keyboard
                )
            elif product.file_type == "animation":
                await message.answer_animation(
                    animation=product.image_url,
                    caption=product_text,
                    reply_markup=keyboard
                )
        else:
            await message.answer(
                product_text,
                reply_markup=keyboard
            )

    # Кнопки для навигации по страницам
    navigation_buttons = []
    if page > 0:
        navigation_buttons.append(InlineKeyboardButton(text="⬅️ Назад", callback_data=f"admin_products_page_{page - 1}"))
    if end_index < len(products):
        navigation_buttons.append(InlineKeyboardButton(text="➡️ Вперед", callback_data=f"admin_products_page_{page + 1}"))

    if navigation_buttons:
        await message.answer("Навигация по страницам:", reply_markup=InlineKeyboardMarkup(inline_keyboard=[navigation_buttons]))



# Обработчик для пагинации (админская версия)
@router.callback_query(F.data.startswith("admin_products_page_"))
async def handle_admin_products_page(callback: types.CallbackQuery):
    page = int(callback.data.replace("admin_products_page_", ""))
    async with AsyncSessionLocal() as session:
        # Получаем товары для текущей подкатегории
        subcategory_id = ...  # Нужно сохранить subcategory_id в состоянии или передать его через callback_data
        products = await get_products_by_subcategory_id(session, subcategory_id)
        await show_admin_products_page(callback.message, products, page)


# Обработчик для выбора подкатегории
@router.callback_query(F.data.startswith("subcategory_"))
async def show_products(callback: types.CallbackQuery):
    subcategory_id = int(callback.data.replace("subcategory_", ""))  # Получаем ID подкатегории
    async with AsyncSessionLocal() as session:
        products = await get_products_by_subcategory_id(session, subcategory_id)  # Получаем товары
        if products:
            await show_products_page(callback.message, products, 0)  # Показываем первую страницу товаров
        else:
            await callback.message.answer("Товары в этой подкатегории отсутствуют.", reply_markup=admin_menu)




# Обработчик для пагинации
@router.callback_query(F.data.startswith("products_page_"))
async def handle_products_page(callback: types.CallbackQuery):
    page = int(callback.data.replace("products_page_", ""))
    async with AsyncSessionLocal() as session:
        # Получаем товары для текущей подкатегории
        subcategory_id = ...  # Нужно сохранить subcategory_id в состоянии или передать его через callback_data
        products = await get_products_by_subcategory_id(session, subcategory_id)
        await show_products_page(callback.message, products, page)






@router.message(F.text == "Редактировать характеристики")
async def edit_specs_start(message: types.Message, state: FSMContext):
    await message.answer("Введите артикул товара (SKU), характеристики которого хотите изменить:")
    await state.set_state(EditSpecs.sku)

@router.callback_query(F.data == "place_order")
async def place_order_handler(callback: types.CallbackQuery):
    user_telegram_id = callback.from_user.id  # Telegram ID пользователя

    async with AsyncSessionLocal() as session:
        # Получаем пользователя из базы данных
        user_result = await session.execute(select(User).where(User.user_id == user_telegram_id))
        user = user_result.scalars().first()

        if not user:
            logging.warning(f"Пользователь с Telegram ID {user_telegram_id} не найден! Создаём нового.")
            user = User(
                user_id=user_telegram_id,
                username=callback.from_user.username,
                full_name=callback.from_user.full_name
            )
            session.add(user)
            await session.commit()
            await session.refresh(user)

        # Получаем товары из корзины пользователя
        cart_items = await get_cart_items(session, user.user_id)  # Используем user.user_id
        if not cart_items:
            await callback.answer("Ваша корзина пуста!", show_alert=True)
            return

        # Создаем новый заказ
        new_order = Order(user_id=user.user_id, status=OrderStatus.PROCESSING.value)  # Используем user.user_id
        session.add(new_order)
        await session.commit()
        await session.refresh(new_order)

        # Добавляем товары из корзины в заказ
        for item in cart_items:
            order_item = OrderItem(
                order_id=new_order.id,
                product_id=item.product_id,
                quantity=item.quantity
            )
            session.add(order_item)

        # Очищаем корзину пользователя
        for item in cart_items:
            await session.delete(item)

        await session.commit()

        await callback.answer("Заказ успешно создан!", show_alert=True)
        await callback.message.answer("Ваш заказ успешно создан. Ожидайте подтверждения.")



@router.message(F.text == "Удалить характеристики")
async def delete_specs_start(message: types.Message, state: FSMContext):
    await message.answer("Введите артикул товара (SKU), характеристики которого хотите удалить:")
    await state.set_state(DeleteSpecs.sku)

@router.message(DeleteSpecs.sku)
async def delete_specs_sku(message: types.Message, state: FSMContext):
    sku = message.text
    async with AsyncSessionLocal() as session:
        product = await get_product_by_sku(session, sku)
        if not product:
            await message.answer("Товар с таким артикулом не найден!", reply_markup=admin_menu)
            await state.clear()
            return

        # Удаляем все характеристики товара
        await session.execute(
            delete(ProductSpecification).where(ProductSpecification.product_id == product.id)
        )
        await session.commit()

    await message.answer("Характеристики успешно удалены!", reply_markup=admin_menu)
    await state.clear()


@router.message(F.text.lower().strip() == "заказы")
async def show_orders(message: types.Message, state: FSMContext):
    logging.debug("Обработчик для кнопки 'Заказы' сработал.")
    await state.clear()

    if await is_admin(message.bot, message.from_user.id):
        logging.debug("Пользователь является администратором.")
        async with AsyncSessionLocal() as session:
            orders = await get_all_orders(session, include_deleted=False)
            logging.debug(f"Найдено заказов: {len(orders)}")

            if orders:
                for order in orders:
                    # Загружаем связанные данные (пользователя) асинхронно
                    await session.refresh(order, attribute_names=["user"])
                    user_name = order.user.full_name if order.user else "Неизвестный пользователь"
                    status = ORDER_STATUS_TRANSLATION.get(order.status, "Неизвестный статус")

                    logging.debug(f"Обработка заказа {order.id} с статусом {status}")

                    # Получаем товары в заказе
                    order_items = await get_order_items(session, order.id)
                    items_text = "\n".join(
                        f"  - {item.product.name} x {item.quantity} шт. (Артикул: {item.product.sku})"
                        for item in order_items
                    )

                    order_text = (
                        f"🔹 Номер заказа: #{order.id}\n"
                        f"🔹 Пользователь: {user_name}\n"
                        f"🔹 Дата: {order.created_at.strftime('%d.%m.%Y %H:%M')}\n"
                        f"🔹 Статус: {status}\n"
                        f"🔹 Товары:\n{items_text}\n"
                        f"🔹 Артикулы товаров: {', '.join(item.product.sku for item in order_items)}\n"
                    )

                    keyboard = InlineKeyboardMarkup(inline_keyboard=[
                        [
                            InlineKeyboardButton(text="Готов к получению", callback_data=f"order_ready_{order.id}"),
                            InlineKeyboardButton(text="Выдан", callback_data=f"order_completed_{order.id}")
                        ],
                        [
                            InlineKeyboardButton(text="Отменен", callback_data=f"order_cancelled_{order.id}"),
                            InlineKeyboardButton(text="Удалить", callback_data=f"order_delete_{order.id}")
                        ]
                    ])
                    await message.answer(order_text, reply_markup=keyboard)
            else:
                await message.answer("Активных заказов нет.", reply_markup=admin_menu)
    else:
        await message.answer("У вас нет доступа к этой команде.")



async def notify_user_about_order_status(bot: Bot, user_id: int, order_id: int, new_status: OrderStatus):
    """Уведомляет пользователя об изменении статуса заказа."""
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Order).where(Order.id == order_id))
        order = result.scalars().first()

        if order:
            status_text = ORDER_STATUS_TRANSLATION.get(new_status.value, "Неизвестный статус")
            await bot.send_message(
                chat_id=user_id,
                text=f"📦 Статус вашего заказа №{order.id} изменен на: *{status_text}*.",
                parse_mode="Markdown"
            )


@router.callback_query(F.data.startswith("order_ready_"))
async def set_order_ready(callback: types.CallbackQuery, bot: Bot):
    """Меняет статус заказа на 'Готов к получению'."""
    order_id = int(callback.data.replace("order_ready_", ""))
    async with AsyncSessionLocal() as session:
        order = await update_order_status(session, order_id, OrderStatus.READY_FOR_PICKUP)

        if order:
            await callback.answer("Статус заказа изменен на 'Готов к получению'.", show_alert=True)
            await notify_user_about_order_status(bot, order.user_id, order_id, OrderStatus.READY_FOR_PICKUP)



@router.callback_query(F.data.startswith("order_completed_"))
async def set_order_completed(callback: types.CallbackQuery, bot: Bot):
    """Меняет статус заказа на 'Выдан'."""
    order_id = int(callback.data.replace("order_completed_", ""))
    async with AsyncSessionLocal() as session:
        order = await update_order_status(session, order_id, OrderStatus.COMPLETED)

        if order:
            await callback.answer("Статус заказа изменен на 'Выдан'.", show_alert=True)
            await notify_user_about_order_status(bot, order.user_id, order_id, OrderStatus.COMPLETED)


@router.callback_query(F.data.startswith("order_cancelled_"))
async def set_order_cancelled(callback: types.CallbackQuery, bot: Bot):
    """Меняет статус заказа на 'Отменен'."""
    order_id = int(callback.data.replace("order_cancelled_", ""))
    async with AsyncSessionLocal() as session:
        order = await update_order_status(session, order_id, OrderStatus.CANCELLED)

        if order:
            await callback.answer("Статус заказа изменен на 'Отменен'.", show_alert=True)
            await notify_user_about_order_status(bot, order.user_id, order_id, OrderStatus.CANCELLED)


@router.callback_query(F.data.startswith("order_delete_"))
async def delete_order_handler(callback: types.CallbackQuery):
    order_id = int(callback.data.replace("order_delete_", ""))
    async with AsyncSessionLocal() as session:
        order = await session.get(Order, order_id)
        if order:
            order.is_deleted = True  # Помечаем заказ как удаленный
            await session.commit()
            await callback.answer("Заказ успешно удален.", show_alert=True)
        else:
            await callback.answer("Заказ не найден.", show_alert=True)

@router.callback_query(F.data.startswith("restore_order_"))
async def restore_order_handler(callback: types.CallbackQuery):
    order_id = int(callback.data.replace("restore_order_", ""))
    async with AsyncSessionLocal() as session:
        await restore_order(session, order_id)
        await callback.answer("Заказ успешно восстановлен.", show_alert=True)

@router.callback_query(F.data == "show_deleted_orders")
async def show_deleted_orders_handler(callback: types.CallbackQuery):
    async with AsyncSessionLocal() as session:
        orders = await get_all_orders(session, include_deleted=True)  # Получаем все заказы, включая удаленные
        if orders:
            for order in orders:
                if order.is_deleted:  # Показываем только удаленные заказы
                    user_name = order.user.full_name if order.user else "Неизвестный пользователь"
                    order_text = (
                        f"🔹 Заказ №{order.id}\n"
                        f"🔹 Пользователь: {user_name}\n"
                        f"🔹 Дата создания: {order.created_at}\n"
                        f"🔹 Статус: {order.status}\n"
                        f"🔹 Удален: Да\n"
                    )
                    await callback.message.answer(order_text)
        else:
            await callback.message.answer("Удаленных заказов нет.", reply_markup=admin_menu)

@router.message(F.text == "История заказов")
async def show_order_history(message: types.Message, state: FSMContext):
    await state.clear()
    if await is_admin(message.bot, message.from_user.id):
        async with AsyncSessionLocal() as session:
            # Получаем только удаленные заказы
            orders = await get_all_orders(session, include_deleted=True)
            deleted_orders = [order for order in orders if order.is_deleted]

            if deleted_orders:
                for order in deleted_orders:
                    await session.refresh(order, attribute_names=["user"])
                    user_name = order.user.full_name if order.user else "Неизвестный пользователь"
                    order_text = (
                        f"🔹 Заказ №{order.id}\n"
                        f"🔹 Пользователь: {user_name}\n"
                        f"🔹 Дата создания: {order.created_at}\n"
                        f"🔹 Статус: {order.status}\n"
                        f"🔹 Удален: Да\n"
                    )
                    await message.answer(order_text)

                # Кнопка "Очистить историю"
                keyboard = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="Очистить историю", callback_data="clear_deleted_orders")]
                ])
                await message.answer("Вы можете очистить историю удаленных заказов:", reply_markup=keyboard)
            else:
                await message.answer("Удаленных заказов нет.", reply_markup=admin_menu)
    else:
        await message.answer("У вас нет доступа к этой команде.")


@router.callback_query(F.data == "clear_deleted_orders")
async def clear_deleted_orders_handler(callback: types.CallbackQuery):
    async with AsyncSessionLocal() as session:
        try:
            # Удаляем все связанные записи из order_items для удаленных заказов
            await session.execute(
                delete(OrderItem)
                .where(OrderItem.order_id.in_(
                    select(Order.id).where(Order.is_deleted == True)
                ))
            )

            # Удаляем все заказы, помеченные как удаленные
            await session.execute(
                delete(Order).where(Order.is_deleted == True)
            )

            await session.commit()
            await callback.answer("История удаленных заказов очищена.", show_alert=True)
        except Exception as e:
            print(f"Ошибка при удалении заказов: {e}")
            await callback.answer("Произошла ошибка при удалении заказов.", show_alert=True)



@router.callback_query(F.data.startswith("order_details_"))
async def show_order_details(callback: types.CallbackQuery):
    order_id = int(callback.data.replace("order_details_", ""))
    async with AsyncSessionLocal() as session:
        order = await session.get(Order, order_id)
        if order:
            user_name = order.user.full_name if order.user else "Неизвестный пользователь"
            order_text = (
                f"🔹 Заказ №{order.id}\n"
                f"🔹 Пользователь: {user_name}\n"
                f"🔹 Дата создания: {order.created_at}\n"
                f"🔹 Статус: {order.status}\n"
                f"🔹 Удален: {'Да' if order.is_deleted else 'Нет'}\n"
            )

            # Добавляем клавиатуру для управления заказом
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="Удалить заказ", callback_data=f"delete_order_{order.id}")],
                [InlineKeyboardButton(text="Восстановить заказ", callback_data=f"restore_order_{order.id}")],
                [InlineKeyboardButton(text="Показать удаленные заказы", callback_data="show_deleted_orders")]
            ])

            await callback.message.answer(order_text, reply_markup=keyboard)
        else:
            await callback.message.answer("Заказ не найден.", reply_markup=admin_menu)




async def show_orders_page(callback: types.CallbackQuery, orders: list[Order], page: int):
    start_index = page * 5
    end_index = start_index + 5
    orders_to_show = orders[start_index:end_index]

    if not orders_to_show:
        await callback.message.answer("Заказы закончились.", reply_markup=admin_menu)
        return

    for order in orders_to_show:
        user_name = order.user.full_name if order.user else "Неизвестный пользователь"
        order_text = (
            f"🔹 Заказ №{order.id}\n"
            f"🔹 Пользователь: {user_name}\n"
            f"🔹 Дата создания: {order.created_at}\n"
            f"🔹 Статус: {order.status}\n"
            f"🔹 Удален: {'Да' if order.is_deleted else 'Нет'}\n"
        )

        # Добавляем клавиатуру для управления заказом
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Удалить заказ", callback_data=f"delete_order_{order.id}")],
            [InlineKeyboardButton(text="Восстановить заказ", callback_data=f"restore_order_{order.id}")],
            [InlineKeyboardButton(text="Показать удаленные заказы", callback_data="show_deleted_orders")]
        ])

        await callback.message.answer(order_text, reply_markup=keyboard)

    # Кнопки для навигации по страницам
    navigation_buttons = []
    if page > 0:
        navigation_buttons.append(InlineKeyboardButton(text="⬅️ Назад", callback_data=f"orders_page_{page - 1}"))
    if end_index < len(orders):
        navigation_buttons.append(InlineKeyboardButton(text="➡️ Вперед", callback_data=f"orders_page_{page + 1}"))

    if navigation_buttons:
        await callback.message.answer("Навигация по страницам:", reply_markup=InlineKeyboardMarkup(inline_keyboard=[navigation_buttons]))




@router.message(F.text == "Наличие товара")
async def update_stock_status_start(message: types.Message, state: FSMContext):
    await message.answer("Введите артикул (SKU) товара, статус которого хотите изменить:")
    await state.set_state(UpdateStockStatus.product_sku)

@router.message(UpdateStockStatus.product_sku)
async def update_stock_status_sku(message: types.Message, state: FSMContext):
    sku = message.text
    async with AsyncSessionLocal() as session:
        product = await get_product_by_sku(session, sku)
        if not product:
            await message.answer("Товар с таким артикулом не найден!", reply_markup=admin_menu)
            await state.clear()
            return

        await state.update_data(product_id=product.id)  # Сохраняем ID товара в состоянии
        await message.answer(
            f"Текущий статус товара '{product.name}': {'В наличии' if product.in_stock else 'Ожидаем'}.\n"
            f"Выберите новый статус:",
            reply_markup=ReplyKeyboardMarkup(
                keyboard=[
                    [KeyboardButton(text="В наличии"), KeyboardButton(text="Ожидаем")],
                    [KeyboardButton(text="Отмена")]
                ],
                resize_keyboard=True
            )
        )
        await state.set_state(UpdateStockStatus.stock_status)

@router.message(UpdateStockStatus.stock_status)
async def update_stock_status_final(message: types.Message, state: FSMContext):
    if message.text.lower() == "отмена":
        await state.clear()
        await message.answer("Действие отменено. Возврат в админ-панель.", reply_markup=admin_menu)
        return

    new_status = message.text.lower() == "в наличии"  # True - В наличии, False - Ожидаем
    data = await state.get_data()
    product_id = data.get('product_id')

    async with AsyncSessionLocal() as session:
        await update_product_stock_status(session, product_id, new_status)
        product = await session.get(Product, product_id)
        await message.answer(
            f"Статус товара '{product.name}' изменен на: {'В наличии' if new_status else 'Ожидаем'}.",
            reply_markup=admin_menu
        )

    await state.clear()


@router.callback_query(F.data.startswith("update_stock_"))
async def update_stock_handler(callback: types.CallbackQuery, state: FSMContext):
    product_id = int(callback.data.replace("update_stock_", ""))
    await state.update_data(product_id=product_id)
    await callback.message.answer(
        "Выберите новый статус:",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="В наличии"), KeyboardButton(text="Ожидаем")],
                [KeyboardButton(text="Отмена")]
            ],
            resize_keyboard=True
        )
    )
    await state.set_state(UpdateStockStatus.stock_status)









@router.callback_query(F.data == "place_order_admin")
async def place_order_admin(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer("Введите Telegram ID пользователя, для которого хотите создать заказ:")
    await state.set_state(OrderState.waiting_for_user_id)

@router.message(OrderState.waiting_for_user_id)
async def process_user_id(message: types.Message, state: FSMContext):
    try:
        user_id = int(message.text)  # Проверяем, что введённое значение — число
    except ValueError:
        await message.answer("Неверный формат ID. Введите число.")
        return

    async with AsyncSessionLocal() as session:
        user_result = await session.execute(select(User).where(User.user_id == user_id))
        user = user_result.scalars().first()

        if not user:
            await message.answer("Пользователь с таким ID не найден.")
            return

        cart_items = await get_cart_items(session, user_id)
        if not cart_items:
            await message.answer("Корзина у этого пользователя пуста.")
            return

        new_order = Order(user_id=user.id, status=OrderStatus.PROCESSING.value)
        session.add(new_order)
        await session.commit()
        await session.refresh(new_order)  # Получаем new_order.id

        for item in cart_items:
            order_item = OrderItem(
                order_id=new_order.id,
                product_id=item.product_id,
                quantity=item.quantity
            )
            session.add(order_item)

        for item in cart_items:
            await session.delete(item)

        await session.commit()

        await message.answer(f"Заказ для пользователя {user_id} успешно создан!")
        await state.clear()

@router.message(F.text == "🔍 Поиск")
async def search_product_start(message: types.Message, state: FSMContext):
    await message.answer("Введите артикул или название фирмы для поиска товара:")
    await state.set_state(SearchProduct.query)



@router.message(SearchProduct.query)
async def search_product_result(message: types.Message, state: FSMContext):
    query = message.text.strip()  # Убираем лишние пробелы

    async with AsyncSessionLocal() as session:
        # Сначала ищем точное совпадение по артикулу
        product_by_sku = await session.execute(
            select(Product).where(Product.sku == query)
        )
        product_by_sku = product_by_sku.scalars().first()

        # Если по артикулу не нашли, ищем товары по бренду (поиск без учета регистра)
        if not product_by_sku:
            products_by_brand = await session.execute(
                select(Product).where(Product.brand.ilike(f"%{query}%"))
            )
            products_by_brand = products_by_brand.scalars().all()
        else:
            products_by_brand = []

    # Если нашли товар по артикулу — показываем его первым
    if product_by_sku:
        await show_product_info(message, product_by_sku)

    # Если нашли товары по бренду — показываем список
    if products_by_brand:
        for product in products_by_brand:
            await show_product_info(message, product)

    if not product_by_sku and not products_by_brand:
        await message.answer("Товар не найден. Попробуйте еще раз.")

    await state.clear()  # Очищаем состояние после поиска





