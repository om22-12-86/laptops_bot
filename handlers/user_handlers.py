from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from sqlalchemy import func
from keyboards.user_kb import (
    user_menu,
    get_cart_keyboard,
    get_search_results_keyboard,
    get_categories_keyboard,
    get_subcategories_keyboard,
    get_empty_cart_keyboard,
    get_product_keyboard,
    get_product_images_keyboard,
    get_product_specs_keyboard
)
from database.crud import (
    get_banner,
    get_categories,
    get_cart_items,
    get_subcategories_by_category_id,
    get_products_by_subcategory_id,
    get_product_images,
    get_product_specifications,
    get_orders,
    get_order_items,
    get_product_by_id
)
from database.database import AsyncSessionLocal
from utils.utils import is_admin
from aiogram import Bot
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy import select
from database.models import Category, Product, User, CartItem, Order, OrderItem, Subcategory, OrderStatus
import logging

logging.basicConfig(level=logging.DEBUG)
router = Router()

ORDER_STATUS_TRANSLATION = {
    OrderStatus.PROCESSING: "В обработке",
    OrderStatus.READY_FOR_PICKUP: "Готов к получению",
    OrderStatus.COMPLETED: "Выдан",
    OrderStatus.CANCELLED: "Отменен",
}


async def delete_previous_message(callback: types.CallbackQuery):
    """Удаляет предыдущее сообщение."""
    try:
        await callback.message.delete()
    except Exception as e:
        print(f"Ошибка при удалении сообщения: {e}")

async def show_main_menu(message_or_callback, bot: Bot = None):
    async with AsyncSessionLocal() as session:
        banner = await get_banner(session, "main_menu")

        if banner:
            if banner.file_type == "photo":
                await message_or_callback.answer_photo(
                    photo=banner.image_url,
                    caption=banner.description,
                    reply_markup=user_menu
                )
            elif banner.file_type == "animation":
                await message_or_callback.answer_animation(
                    animation=banner.image_url,
                    caption=banner.description,
                    reply_markup=user_menu
                )
            else:
                await message_or_callback.answer("Тип файла не поддерживается.", reply_markup=user_menu)
        else:
            await message_or_callback.answer("Баннер не найден!", reply_markup=user_menu)

@router.message(Command("start"))
async def start(message: types.Message, bot: Bot):
    await show_main_menu(message, bot)

@router.callback_query(F.data == "main_menu")
async def back_to_main_handler(callback: types.CallbackQuery, bot: Bot):
    await delete_previous_message(callback)
    await show_main_menu(callback.message, bot)
    await callback.answer()

@router.callback_query(F.data == "catalog")
async def catalog_handler(callback: types.CallbackQuery):
    await delete_previous_message(callback)  # Удаляем предыдущее сообщение
    async with AsyncSessionLocal() as session:
        banner = await get_banner(session, "catalog")
        categories = await get_categories(session)
        keyboard = get_categories_keyboard(categories)

        if banner:
            if banner.file_type == "photo":
                await callback.message.answer_photo(
                    photo=banner.image_url,
                    caption=banner.description,
                    reply_markup=keyboard
                )
            elif banner.file_type == "animation":
                await callback.message.answer_animation(
                    animation=banner.image_url,
                    caption=banner.description,
                    reply_markup=keyboard
                )
            else:
                await callback.message.answer("Тип файла не поддерживается.", reply_markup=keyboard)
        else:
            await callback.message.answer("Баннер для каталога не найден!", reply_markup=keyboard)




@router.callback_query(F.data.startswith("category_"))
async def category_handler(callback: types.CallbackQuery):
    await delete_previous_message(callback)
    category_id = int(callback.data.replace("category_", ""))
    async with AsyncSessionLocal() as session:
        category = await session.execute(select(Category).where(Category.id == category_id))
        category = category.scalars().first()

        if category:
            subcategories = await get_subcategories_by_category_id(session, category.id)
            banner = await get_banner(session, "laptops")

            if banner:
                if banner.file_type == "photo":
                    await callback.message.answer_photo(
                        photo=banner.image_url,
                        caption=banner.description,
                        reply_markup=get_subcategories_keyboard(subcategories)
                    )
                elif banner.file_type == "animation":
                    await callback.message.answer_animation(
                        animation=banner.image_url,
                        caption=banner.description,
                        reply_markup=get_subcategories_keyboard(subcategories)
                    )
                else:
                    await callback.message.answer("Тип файла не поддерживается.", reply_markup=get_subcategories_keyboard(subcategories))
            else:
                await callback.message.answer(f"{category.name}!", reply_markup=get_subcategories_keyboard(subcategories))
        else:
            await callback.message.answer("Категория не найдена.")


@router.callback_query(F.data.startswith("subcategory_"))
async def subcategory_handler(callback: types.CallbackQuery):
    try:
        subcategory_id = int(callback.data.replace("subcategory_", ""))
    except ValueError:
        return await callback.answer("Ошибка: неверный формат данных!", show_alert=True)

    async with AsyncSessionLocal() as session:
        products = await get_products_by_subcategory_id(session, subcategory_id)

        if not products:
            subcategories = await get_subcategories_by_category_id(session, subcategory_id)
            return await callback.message.answer(
                "Товары в этой подкатегории отсутствуют.",
                reply_markup=get_subcategories_keyboard(subcategories)
            )

        await show_product(callback, products[0], 0, len(products), subcategory_id)


async def show_product(callback: types.CallbackQuery, product, page: int, total_products: int, subcategory_id: int):
    try:
        async with AsyncSessionLocal() as session:
            print(f"Показ товара: {product.name}")

            images = await get_product_images(session, product.id)
            specs = await get_product_specifications(session, product.id)

            print(f"Изображения: {images}")
            print(f"Характеристики: {specs}")

            product_text = (
                f"🔹 Название: {product.name}\n"
                f"🔹 Описание: {product.description}\n"
                f"🔹 Цена: {product.price} руб.\n"
                f"🔹 Наличие: {'В наличии' if product.in_stock else 'Под заказ'}\n"
                f"🔹 Артикул: {product.sku}\n"
            )

            await delete_previous_message(callback)

            keyboard = get_product_keyboard(product.id, page, total_products, subcategory_id)

            if product.image_url:
                print(f"Попытка отправить сообщение с изображением: {product.image_url}")
                if product.file_type == "photo":
                    await callback.message.answer_photo(
                        photo=product.image_url,
                        caption=product_text,
                        reply_markup=keyboard
                    )
                elif product.file_type == "animation":
                    await callback.message.answer_animation(
                        animation=product.image_url,
                        caption=product_text,
                        reply_markup=keyboard
                    )
            else:
                print("Изображение отсутствует, отправляем текстовое сообщение.")
                await callback.message.answer(
                    product_text,
                    reply_markup=keyboard
                )
    except Exception as e:
        print(f"Ошибка в show_product: {e}")
        await callback.answer("Произошла ошибка при отображении товара.", show_alert=True)



@router.callback_query(F.data.startswith("next_product_"))
async def next_product_handler(callback: types.CallbackQuery):
    try:
        data = callback.data.replace("next_product_", "")
        values = data.split("_")

        if len(values) != 2:
            print(f"Ошибка: некорректные данные callback: {callback.data}")
            return await callback.answer("Ошибка при переключении товаров.", show_alert=True)

        subcategory_id, current_page = map(int, values)

        async with AsyncSessionLocal() as session:
            products = await get_products_by_subcategory_id(session, subcategory_id)

            if not products:
                return await callback.answer("Товары в этой подкатегории отсутствуют.", show_alert=True)

            new_page = current_page + 1
            if new_page >= len(products):  # Защита от выхода за границы
                new_page = len(products) - 1

            await show_product(callback, products[new_page], new_page, len(products), subcategory_id)

    except Exception as e:
        print(f"Ошибка в next_product_handler: {e}")
        await callback.answer("Произошла ошибка при переключении товаров.", show_alert=True)


@router.callback_query(F.data.startswith("prev_product_"))
async def prev_product_handler(callback: types.CallbackQuery):
    try:
        data = callback.data.replace("prev_product_", "")
        values = data.split("_")

        if len(values) != 2:
            print(f"Ошибка: некорректные данные callback: {callback.data}")
            return await callback.answer("Ошибка при переключении товаров.", show_alert=True)

        subcategory_id, current_page = map(int, values)

        async with AsyncSessionLocal() as session:
            products = await get_products_by_subcategory_id(session, subcategory_id)

            if not products:
                return await callback.answer("Товары в этой подкатегории отсутствуют.", show_alert=True)

            new_page = max(0, current_page - 1)  # Не даем выйти за границы

            await show_product(callback, products[new_page], new_page, len(products), subcategory_id)

    except Exception as e:
        print(f"Ошибка в prev_product_handler: {e}")
        await callback.answer("Произошла ошибка при переключении товаров.", show_alert=True)


@router.callback_query(F.data.startswith("product_images_"))
async def show_product_images(callback: types.CallbackQuery):
    await delete_previous_message(callback)
    product_id = int(callback.data.replace("product_images_", ""))
    async with AsyncSessionLocal() as session:
        images = await get_product_images(session, product_id)

        if images:
            for image in images[:5]:
                if image.file_type == "photo":
                    await callback.message.answer_photo(
                        photo=image.image_url,
                        reply_markup=get_product_images_keyboard(product_id)
                    )
                elif image.file_type == "animation":
                    await callback.message.answer_animation(
                        animation=image.image_url,
                        reply_markup=get_product_images_keyboard(product_id)
                    )
        else:
            await callback.message.answer("Фотографии отсутствуют.", reply_markup=get_product_images_keyboard(product_id))

@router.callback_query(F.data.startswith("product_specs_"))
async def show_product_specs(callback: types.CallbackQuery):
    await delete_previous_message(callback)
    product_id = int(callback.data.replace("product_specs_", ""))
    async with AsyncSessionLocal() as session:
        specs = await get_product_specifications(session, product_id)

        if specs:
            specs_text = "📊 Характеристики товара:\n\n"
            for spec in specs:
                specs_text += f"🔹 {spec.key}: {spec.value}\n"

            await callback.message.answer(
                specs_text,
                reply_markup=get_product_specs_keyboard(product_id))
        else:
            await callback.message.answer("Характеристики отсутствуют.", reply_markup=get_product_specs_keyboard(product_id))


@router.callback_query(F.data.startswith("back_to_product_"))
async def back_to_product(callback: types.CallbackQuery):
    product_id = int(callback.data.replace("back_to_product_", ""))
    async with AsyncSessionLocal() as session:
        try:
            # Получаем продукт по ID
            product = await session.get(Product, product_id)
            if not product:
                await callback.answer("Товар не найден.", show_alert=True)
                return

            # Получаем подкатегорию продукта
            subcategory_id = product.subcategory_id
            subcategory = await session.get(Subcategory, subcategory_id)
            if not subcategory:
                await callback.answer("Подкатегория не найдена.", show_alert=True)
                return

            # Получаем общее количество товаров в подкатегории
            total_products = await session.execute(
                select(func.count()).where(Product.subcategory_id == subcategory_id)
            )
            total_products = total_products.scalar()

            # Вызываем функцию show_product с правильными аргументами
            await show_product(callback, product, 0, total_products, subcategory_id)
        except Exception as e:
            print(f"Ошибка в back_to_product: {e}")
            await callback.answer("Произошла ошибка при переходе к товару.", show_alert=True)


@router.callback_query(F.data.startswith("back_to_subcategory_"))
async def back_to_subcategory(callback: types.CallbackQuery):
    await delete_previous_message(callback)

    try:
        subcategory_id = int(callback.data.replace("back_to_subcategory_", ""))
        async with AsyncSessionLocal() as session:
            subcategory = await get_entity_by_id(session, Subcategory, subcategory_id)
            if not subcategory:
                await callback.answer("Подкатегория не найдена.", show_alert=True)
                return

            category = await get_entity_by_id(session, Category, subcategory.category_id)
            if not category:
                await callback.answer("Категория не найдена.", show_alert=True)
                return

            subcategories = await get_subcategories_by_category_id(session, category.id)
            if not subcategories:
                await handle_no_subcategories(session, callback)
            else:
                await handle_subcategories(session, callback, category, subcategories)

    except Exception as e:
        print(f"Ошибка в back_to_subcategory: {e}")
        await callback.answer("Произошла ошибка при переходе назад.", show_alert=True)


async def get_entity_by_id(session, model, entity_id):
    """Получает сущность по ID."""
    return await session.get(model, entity_id)


async def handle_no_subcategories(session, callback):
    """Обрабатывает случай, когда подкатегорий нет."""
    categories = await get_categories(session)
    banner = await get_banner(session, "catalog")
    message_text = "Список категорий:"
    keyboard = get_categories_keyboard(categories)

    await send_banner_message(callback, banner, message_text, keyboard)


async def handle_subcategories(session, callback, category, subcategories):
    """Обрабатывает случай, когда есть подкатегории."""
    banner_type = "laptops"  # Можно заменить на более универсальный подход
    banner = await get_banner(session, banner_type) or await get_banner(session, category.name)

    message_text = f"Подкатегории для категории {category.name}:"
    keyboard = get_subcategories_keyboard(subcategories)

    await send_banner_message(callback, banner, message_text, keyboard)


async def send_banner_message(callback, banner, message_text, keyboard):
    """Отправляет сообщение с баннером или без него."""
    if banner:
        if banner.file_type == "photo":
            await callback.message.answer_photo(
                photo=banner.image_url,
                caption=message_text,
                reply_markup=keyboard
            )
        elif banner.file_type == "animation":
            await callback.message.answer_animation(
                animation=banner.image_url,
                caption=message_text,
                reply_markup=keyboard
            )
        else:
            await callback.message.answer(message_text, reply_markup=keyboard)
    else:
        await callback.message.answer(message_text, reply_markup=keyboard)



@router.callback_query(F.data == "laptops")
async def laptops_handler(callback: types.CallbackQuery):
    await delete_previous_message(callback)
    async with AsyncSessionLocal() as session:
        banner = await get_banner(session, "laptops")
        category = await session.execute(select(Category).where(Category.name == "Ноутбуки"))
        category = category.scalars().first()

        if category:
            subcategories = await get_subcategories_by_category_id(session, category.id)

            if banner:
                if banner.file_type == "photo":
                    await callback.message.answer_photo(
                        photo=banner.image_url,
                        caption=banner.description,
                        reply_markup=get_subcategories_keyboard(subcategories)
                    )
                elif banner.file_type == "animation":
                    await callback.message.answer_animation(
                        animation=banner.image_url,
                        caption=banner.description,
                        reply_markup=get_subcategories_keyboard(subcategories)
                    )
                else:
                    await callback.message.answer("Тип файла не поддерживается.", reply_markup=get_subcategories_keyboard(subcategories))
            else:
                await callback.message.answer("Ноутбуки!", reply_markup=get_subcategories_keyboard(subcategories))
        else:
            await callback.message.answer("Категория 'Ноутбуки' не найдена.")

@router.callback_query(F.data == "delivery")
async def delivery_handler(callback: types.CallbackQuery):
    await delete_previous_message(callback)
    async with AsyncSessionLocal() as session:
        banner = await get_banner(session, "delivery")
        if banner:
            markup = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="⬅️ Назад", callback_data="main_menu"),
                 InlineKeyboardButton(text="Контакт", callback_data="contact")]
            ])

            if banner.file_type == "photo":
                await callback.message.answer_photo(
                    photo=banner.image_url,
                    caption=banner.description,
                    reply_markup=markup
                )
            elif banner.file_type == "animation":
                await callback.message.answer_animation(
                    animation=banner.image_url,
                    caption=banner.description,
                    reply_markup=markup
                )



@router.callback_query(F.data.startswith("buy_product_"))
async def add_to_cart_handler(callback: types.CallbackQuery, state: FSMContext):
    try:
        async with AsyncSessionLocal() as session:
            # Получаем product_id из callback_data
            product_id = int(callback.data.replace("buy_product_", ""))

            # Получаем товар из базы данных
            product = await session.get(Product, product_id)
            if not product:
                await callback.answer("Товар не найден.", show_alert=True)
                return

            # Проверяем наличие товара
            if not product.in_stock:
                await callback.answer(
                    "Этот товар сейчас отсутствует в наличии. Пожалуйста, свяжитесь с администратором для уточнения возможности заказа.",
                    show_alert=True
                )
                return

            # Получаем пользователя из базы данных
            user_result = await session.execute(select(User).where(User.user_id == callback.from_user.id))
            user = user_result.scalars().first()

            # Если пользователь не найден, создаем его
            if not user:
                user = User(
                    user_id=callback.from_user.id,
                    username=callback.from_user.username,
                    full_name=callback.from_user.full_name
                )
                session.add(user)
                await session.commit()
                await session.refresh(user)

            # Проверяем, есть ли товар уже в корзине
            cart_item_result = await session.execute(
                select(CartItem).where(CartItem.user_id == user.user_id, CartItem.product_id == product_id)
            )
            cart_item = cart_item_result.scalars().first()

            if cart_item:
                # Если товар уже в корзине, увеличиваем количество
                cart_item.quantity += 1
            else:
                # Если товара нет в корзине, создаем новую запись
                cart_item = CartItem(
                    user_id=user.user_id,
                    product_id=product_id,
                    quantity=1
                )
                session.add(cart_item)

            await session.commit()
            await callback.answer(f"Товар {product.name} добавлен в корзину!", show_alert=True)
            await state.clear()

    except Exception as e:
        logging.error(f"Ошибка при добавлении товара в корзину: {e}")
        await callback.answer("Произошла ошибка при добавлении товара в корзину.", show_alert=True)


@router.callback_query(F.data == "cart")
async def cart_handler(callback: types.CallbackQuery, state: FSMContext):
    try:
        await state.clear()
        await delete_previous_message(callback)

        async with AsyncSessionLocal() as session:
            # Получаем товары в корзине
            cart_items = await get_cart_items(session, callback.from_user.id)

            if not cart_items:
                banner = await get_banner(session, "cart")
                if banner:
                    if banner.file_type == "photo":
                        await callback.message.answer_photo(
                            photo=banner.image_url,
                            caption="Ваша корзина пуста.",
                            reply_markup=get_empty_cart_keyboard())
                    elif banner.file_type == "animation":
                        await callback.message.answer_animation(
                            animation=banner.image_url,
                            caption="Ваша корзина пуста.",
                            reply_markup=get_empty_cart_keyboard())
                    else:
                        await callback.message.answer(
                            "Ваша корзина пуста.",
                            reply_markup=get_empty_cart_keyboard())
                else:
                    await callback.message.answer(
                        "Ваша корзина пуста.",
                        reply_markup=get_empty_cart_keyboard())
                return

            # Отображаем первый товар в корзине
            await update_cart_message(callback.message, 0)

    except Exception as e:
        logging.error(f"Ошибка в cart_handler: {e}")
        await callback.answer("Произошла ошибка при обработке корзины.", show_alert=True)



@router.callback_query(F.data == "ignore")
async def ignore_handler(callback: types.CallbackQuery):
    await callback.answer()


@router.callback_query(F.data.startswith("increase_"))
async def increase_quantity_handler(callback: types.CallbackQuery, state: FSMContext):
    try:
        product_id = int(callback.data.replace("increase_", ""))
        logging.debug(f"Увеличение количества товара: product_id={product_id}, user_id={callback.from_user.id}")

        async with AsyncSessionLocal() as session:
            user_result = await session.execute(select(User).where(User.user_id == callback.from_user.id))
            user = user_result.scalars().first()

            if not user:
                logging.debug("Пользователь не найден.")
                await callback.answer("Пользователь не найден.", show_alert=True)
                return

            cart_item = await session.execute(
                select(CartItem)
                .where(CartItem.user_id == user.user_id)  # Используем user.user_id
                .where(CartItem.product_id == product_id)
            )
            cart_item = cart_item.scalars().first()

            if cart_item:
                logging.debug(f"Товар найден в корзине: {cart_item}")
                cart_item.quantity += 1
                await session.commit()
                await callback.answer(f"Количество товара увеличено до {cart_item.quantity}.")
            else:
                logging.debug("Товар не найден в корзине.")
                await callback.answer("Товар не найден в корзине.", show_alert=True)

        await cart_handler(callback, state)
    except Exception as e:
        logging.error(f"Ошибка при увеличении количества товара: {e}")
        await callback.answer("Произошла ошибка при изменении количества товара.", show_alert=True)



@router.callback_query(F.data.startswith("decrease_"))
async def decrease_quantity_handler(callback: types.CallbackQuery, state: FSMContext):
    try:
        product_id = int(callback.data.replace("decrease_", ""))
        async with AsyncSessionLocal() as session:
            # Получаем пользователя по user_id
            user_result = await session.execute(select(User).where(User.user_id == callback.from_user.id))
            user = user_result.scalars().first()

            if not user:
                await callback.answer("Пользователь не найден.", show_alert=True)
                return

            # Ищем товар в корзине по user.user_id и product_id
            cart_item = await session.execute(
                select(CartItem)
                .where(CartItem.user_id == user.user_id)  # Используем user.user_id вместо user.id
                .where(CartItem.product_id == product_id)
            )
            cart_item = cart_item.scalars().first()

            if cart_item:
                if cart_item.quantity > 1:
                    cart_item.quantity -= 1
                    await session.commit()
                    await callback.answer(f"Количество товара уменьшено до {cart_item.quantity}.")
                else:
                    # Если количество равно 1, удаляем товар из корзины
                    await session.delete(cart_item)
                    await session.commit()
                    await callback.answer("Товар удален из корзины.", show_alert=True)
            else:
                await callback.answer("Товар не найден в корзине.", show_alert=True)

        # Обновляем сообщение с корзиной
        await cart_handler(callback, state)
    except Exception as e:
        logging.error(f"Ошибка при уменьшении количества товара: {e}")
        await callback.answer("Произошла ошибка при изменении количества товара.", show_alert=True)



@router.callback_query(F.data.startswith("prev_cart_item_"))
async def prev_cart_item_handler(callback: types.CallbackQuery, state: FSMContext):
    try:
        current_index = int(callback.data.replace("prev_cart_item_", ""))
        new_index = max(0, current_index - 1)
        await update_cart_message(callback.message, new_index)
        await callback.answer()
    except Exception as e:
        logging.error(f"Ошибка в prev_cart_item_handler: {e}")
        await callback.answer("Произошла ошибка при переключении товаров.", show_alert=True)

@router.callback_query(F.data.startswith("next_cart_item_"))
async def next_cart_item_handler(callback: types.CallbackQuery, state: FSMContext):
    try:
        current_index = int(callback.data.replace("next_cart_item_", ""))
        async with AsyncSessionLocal() as session:
            cart_items = await get_cart_items(session, callback.from_user.id)
            new_index = min(len(cart_items) - 1, current_index + 1)
            await update_cart_message(callback.message, new_index)
            await callback.answer()
    except Exception as e:
        logging.error(f"Ошибка в next_cart_item_handler: {e}")
        await callback.answer("Произошла ошибка при переключении товаров.", show_alert=True)


async def update_cart_message(message: types.Message, current_index: int):
    try:
        async with AsyncSessionLocal() as session:
            # Получаем все товары в корзине
            cart_items = await get_cart_items(session, message.from_user.id)

            if not cart_items:
                await message.answer(
                    "Ваша корзина пуста.",
                    reply_markup=get_empty_cart_keyboard())
                return

            # Проверяем корректность индекса
            if current_index < 0 or current_index >= len(cart_items):
                current_index = 0

            # Получаем информацию о всех товарах в корзине
            product_ids = [item.product_id for item in cart_items]
            products_result = await session.execute(
                select(Product).where(Product.id.in_(product_ids))
            )
            products = products_result.scalars().all()
            product_dict = {product.id: product for product in products}

            # Вычисляем общее количество и сумму
            total_quantity = sum(item.quantity for item in cart_items)
            total_price = sum(
                item.quantity * product_dict[item.product_id].price
                for item in cart_items
                if item.product_id in product_dict
            )

            # Получаем текущий товар
            current_item = cart_items[current_index]
            current_product = product_dict.get(current_item.product_id)

            if not current_product:
                await message.answer("Ошибка: товар не найден.")
                return

            # Формируем текст сообщения
            cart_text = (
                f"🛒 Ваша корзина:\n\n"
                f"🔹 Текущий товар:\n"
                f"{current_product.name} - {current_item.quantity} шт. x {current_product.price} руб.\n"
                f"Наличие: {'✅ В наличии' if current_product.in_stock else '⏳ Под заказ'}\n\n"
                f"📦 Товар {current_index + 1} из {len(cart_items)}\n"
                f"📋 Общее количество товаров: {total_quantity} шт.\n"
                f"💳 Общая сумма: {total_price} руб."
            )

            # Редактируем сообщение
            try:
                if message.photo or message.animation:
                    await message.edit_caption(
                        caption=cart_text,
                        reply_markup=get_cart_keyboard(cart_items, current_index)
                    )
                else:
                    await message.edit_text(
                        text=cart_text,
                        reply_markup=get_cart_keyboard(cart_items, current_index)
                    )
            except Exception as e:
                logging.error(f"Ошибка при редактировании сообщения: {e}")
                await message.answer(
                    cart_text,
                    reply_markup=get_cart_keyboard(cart_items, current_index)
                )

    except Exception as e:
        logging.error(f"Ошибка в update_cart_message: {e}")
        await message.answer("Произошла ошибка при обновлении корзины.")


# Обработчик для отображения заказов
@router.callback_query(F.data == "orders")
async def orders_handler(callback: types.CallbackQuery):
    await delete_previous_message(callback)
    user_id = callback.from_user.id

    async with AsyncSessionLocal() as session:
        orders = await get_orders(session, user_id)

        if orders:
            orders_text = "📦 Ваши заказы:\n\n"
            for order in orders:
                order_items = await get_order_items(session, order.id)
                orders_text += f"🔹 Заказ №{order.id} от {order.created_at.strftime('%d.%m.%Y %H:%M')}:\n"

                # Получаем статус как объект OrderStatus
                try:
                    status = OrderStatus(order.status)
                    status_text = ORDER_STATUS_TRANSLATION[status]
                except ValueError:
                    status_text = "Неизвестный статус"

                orders_text += f"🔹 Статус: {status_text}\n"

                for item in order_items:
                    product = await session.get(Product, item.product_id)
                    if product:
                        orders_text += f"  - {product.name} x {item.quantity} шт.\n"
                orders_text += "\n"

            await callback.message.answer(
                orders_text,
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="⬅️ Назад", callback_data="main_menu")]
                ])
            )
        else:
            await callback.message.answer(
                "У вас пока нет заказов.",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="⬅️ Назад", callback_data="main_menu")]
                ])
            )
        await callback.answer()


@router.callback_query(F.data == "place_order_user")
async def place_order_user(callback: types.CallbackQuery):
    user_telegram_id = callback.from_user.id

    async with AsyncSessionLocal() as session:
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

        cart_items = await get_cart_items(session, user_telegram_id)
        if not cart_items:
            await callback.answer("Ваша корзина пуста!", show_alert=True)
            return

        # Проверяем наличие всех товаров в корзине
        product_ids = [item.product_id for item in cart_items]
        products_result = await session.execute(select(Product).where(Product.id.in_(product_ids)))
        products = products_result.scalars().all()

        unavailable_products = [p for p in products if not p.in_stock]

        if unavailable_products:
            # Если есть товары не в наличии, сообщаем пользователю
            unavailable_names = "\n".join([f"- {p.name}" for p in unavailable_products])
            await callback.answer(
                f"Некоторые товары в вашей корзине сейчас отсутствуют в наличии:\n{unavailable_names}\n"
                "Пожалуйста, свяжитесь с администратором для уточнения возможности заказа.",
                show_alert=True
            )
            return

        # Если все товары в наличии, создаем заказ
        new_order = Order(user_id=user.id, status=OrderStatus.PROCESSING.value)
        session.add(new_order)
        await session.commit()
        await session.refresh(new_order)

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

        await callback.answer("Заказ успешно создан!", show_alert=True)
        await callback.message.answer("Ваш заказ успешно создан. Ожидайте подтверждения.")





@router.callback_query(F.data == "about")
async def about_handler(callback: types.CallbackQuery):
    await delete_previous_message(callback)
    async with AsyncSessionLocal() as session:
        banner = await get_banner(session, "about")

        if banner:
            if banner.file_type == "photo":
                await callback.message.answer_photo(
                    photo=banner.image_url,
                    caption=banner.description,
                    reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                        [InlineKeyboardButton(text="⬅️ Назад", callback_data="main_menu")]
                    ])
                )
            elif banner.file_type == "animation":
                await callback.message.answer_animation(
                    animation=banner.image_url,
                    caption=banner.description,
                    reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                        [InlineKeyboardButton(text="⬅️ Назад", callback_data="main_menu")]
                    ])
                )
            else:
                await callback.message.answer(
                    "Тип файла не поддерживается.",
                    reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                        [InlineKeyboardButton(text="⬅️ Назад", callback_data="main_menu")]
                    ])
                )
        else:
            await callback.message.answer(
                "Информация о компании отсутствует.",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="⬅️ Назад", callback_data="main_menu")]
                ])
            )


@router.callback_query(F.data == "contact")
async def contact_handler(callback: types.CallbackQuery):
    await delete_previous_message(callback)
    async with AsyncSessionLocal() as session:
        banner = await get_banner(session, "contact")

        if banner:
            if banner.file_type == "photo":
                await callback.message.answer_photo(
                    photo=banner.image_url,
                    caption=banner.description,
                    reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                        [InlineKeyboardButton(text="⬅️ Назад", callback_data="main_menu")]
                    ])
                )
            elif banner.file_type == "animation":
                await callback.message.answer_animation(
                    animation=banner.image_url,
                    caption=banner.description,
                    reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                        [InlineKeyboardButton(text="⬅️ Назад", callback_data="main_menu")]
                    ])
                )
            else:
                await callback.message.answer(
                    "Тип файла не поддерживается.",
                    reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                        [InlineKeyboardButton(text="⬅️ Назад", callback_data="main_menu")]
                    ])
                )
        else:
            await callback.message.answer(
                "Контактная информация отсутствует.",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="⬅️ Назад", callback_data="main_menu")]
                ])
            )



