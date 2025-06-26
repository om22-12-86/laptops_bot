from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import User, Product, Banner, Category, CartItem, Subcategory, ProductImage, ProductSpecification, Order, OrderItem, OrderStatus
from sqlalchemy.future import select
from datetime import datetime
from sqlalchemy import update, delete
from sqlalchemy.orm import selectinload
from sqlalchemy.orm import joinedload
import logging

logging.basicConfig(level=logging.DEBUG)


async def create_product(db: AsyncSession, name: str, description: str, price: float,
                        image_url: str, file_type: str, sku: str,
                        subcategory_id: int):
    """
    Создает новый товар в указанной подкатегории.
    """
    # Проверяем существование товара с таким SKU
    existing_product = await db.execute(select(Product).where(Product.sku == sku))
    existing_product = existing_product.scalars().first()

    if existing_product:
        await db.delete(existing_product)
        await db.commit()

    new_product = Product(
        name=name,
        description=description,
        price=price,
        image_url=image_url,
        file_type=file_type,
        sku=sku,
        subcategory_id=subcategory_id
    )
    db.add(new_product)
    await db.commit()
    await db.refresh(new_product)
    return new_product


async def create_banner(session: AsyncSession, title: str, image_url: str, description: str, banner_type: str, file_type: str):
    new_banner = Banner(
        title=title,
        image_url=image_url,
        description=description,
        banner_type=banner_type,
        file_type=file_type,
        created_at=datetime.utcnow()
    )
    session.add(new_banner)
    await session.commit()

async def update_banner(session: AsyncSession, title: str, image_url: str, description: str, banner_type: str, file_type: str):
    logging.debug(f"Updating banner: {title}, {image_url}, {description}, {banner_type}, {file_type}")

    result = await session.execute(select(Banner).filter_by(banner_type=banner_type))
    existing_banner = result.scalars().first()

    if existing_banner:
        logging.debug(f"Deleting existing banner: {existing_banner}")
        await session.delete(existing_banner)
        await session.commit()

    new_banner = Banner(
        title=title,
        image_url=image_url,
        description=description,
        banner_type=banner_type,
        file_type=file_type,
        created_at=datetime.utcnow()
    )

    logging.debug(f"Adding new banner: {new_banner}")
    session.add(new_banner)
    await session.commit()

async def get_banner(db: AsyncSession, banner_type: str):
    result = await db.execute(select(Banner).where(Banner.banner_type == str(banner_type)))
    return result.scalars().first()

async def create_category(db: AsyncSession, name: str):
    new_category = Category(name=name)
    db.add(new_category)
    await db.commit()

async def get_categories(db: AsyncSession):
    result = await db.execute(select(Category))
    return result.scalars().all()


async def get_cart_items(db: AsyncSession, user_telegram_id: int):
    try:
        logging.debug(f"Поиск корзины для пользователя с ID: {user_telegram_id}")

        result = await db.execute(
            select(CartItem)
            .join(Product)
            .where(CartItem.user_id == user_telegram_id)  # Прямое сравнение с числовым ID
        )

        cart_items = result.scalars().all()
        logging.debug(f"Найдено товаров в корзине: {len(cart_items)}")
        return cart_items
    except Exception as e:
        logging.error(f"Ошибка при запросе корзины: {e}")
        raise



async def get_user_by_id(db: AsyncSession, user_id: int):
    result = await db.execute(select(User).where(User.user_id == int(user_id)))
    return result.scalars().first()

async def get_subcategories_by_category_id(db: AsyncSession, category_id: int):
    result = await db.execute(select(Subcategory).where(Subcategory.category_id == category_id))
    return result.scalars().all()

async def get_products_by_subcategory_id(db: AsyncSession, subcategory_id: int):
    result = await db.execute(select(Product).where(Product.subcategory_id == subcategory_id))
    return result.scalars().all()

async def get_product_images(db: AsyncSession, product_id: int):
    try:
        result = await db.execute(
            select(ProductImage)
            .where(ProductImage.product_id == product_id)
            .order_by(ProductImage.id)
        )
        return result.scalars().all()
    except Exception as e:
        logging.error(f"Error getting images for product {product_id}: {e}")
        return []


async def get_product_specifications(db: AsyncSession, product_id: int):
    """Получает характеристики товара."""
    result = await db.execute(
        select(ProductSpecification).where(ProductSpecification.product_id == product_id)
    )
    return result.scalars().all()  # Возвращаем список характеристик


async def get_product_by_sku(db: AsyncSession, sku: str):
    result = await db.execute(select(Product).where(Product.sku == sku))
    return result.scalars().first()

async def create_product_image(db: AsyncSession, product_id: int, image_url: str, file_type: str):
    product_image = ProductImage(
        product_id=product_id,
        image_url=image_url,
        file_type=file_type
    )
    db.add(product_image)
    await db.commit()
    await db.refresh(product_image)
    return product_image

async def get_orders(db: AsyncSession, user_id: int):
    result = await db.execute(
        select(Order)
        .where(Order.user_id == user_id)
        .where(Order.is_deleted == False)  # Исключаем удаленные заказы
        .order_by(Order.created_at.desc())
    )
    return result.scalars().all()

async def get_order_items(session: AsyncSession, order_id: int) -> list[OrderItem]:
    query = select(OrderItem).options(selectinload(OrderItem.product)).where(OrderItem.order_id == order_id)
    result = await session.execute(query)
    return result.scalars().all()


async def get_all_orders(session: AsyncSession, include_deleted: bool = False) -> list[Order]:
    query = select(Order).options(selectinload(Order.user))
    if not include_deleted:
        query = query.where(Order.is_deleted == False)  # Только активные заказы
    else:
        query = query.where(Order.is_deleted == True)  # Только удаленные заказы
    result = await session.execute(query)
    return result.scalars().all()

async def get_orders_by_user(db: AsyncSession, user_id: int):
    result = await db.execute(
        select(Order)
        .where(Order.user_id == user_id)
        .options(joinedload(Order.user))
        .order_by(Order.created_at.desc())
    )
    return result.scalars().all()


async def update_order_status(db: AsyncSession, order_id: int, status: OrderStatus):
    """Обновляет статус заказа и возвращает обновленный объект."""
    await db.execute(
        update(Order)
        .where(Order.id == order_id)
        .values(status=status.value)  # Сохраняем строковое представление статуса
    )
    await db.commit()

    # Обновляем объект в сессии
    result = await db.execute(select(Order).where(Order.id == order_id))
    order = result.scalars().first()

    if order:
        await db.refresh(order)  # Загружаем актуальные данные из БД

    return order



async def delete_order(db: AsyncSession, order_id: int):
    # Находим заказ по ID
    result = await db.execute(select(Order).where(Order.id == order_id))
    order = result.scalars().first()

    if order:
        # Удаляем все связанные записи из order_items
        await db.execute(delete(OrderItem).where(OrderItem.order_id == order_id))

        # Удаляем заказ из базы данных
        await db.delete(order)
        await db.commit()
    else:
        logging.warning(f"Заказ с ID {order_id} не найден.")

async def create_order(db: AsyncSession, user_id: int, status: OrderStatus = OrderStatus.PROCESSING):
    order = Order(
        user_id=user_id,
        created_at=datetime.utcnow(),
        status=status.value
    )
    db.add(order)
    await db.commit()
    await db.refresh(order)
    return order

async def restore_order(db: AsyncSession, order_id: int):
    await db.execute(
        update(Order)
        .where(Order.id == order_id)
        .values(is_deleted=False)
    )
    await db.commit()

async def get_products_by_category(db: AsyncSession, category_id: int):
    result = await db.execute(
        select(Product)
        .join(Subcategory)
        .where(Subcategory.category_id == category_id)
    )
    return result.scalars().all()

async def update_product_stock_status(db: AsyncSession, product_id: int, in_stock: bool):
    await db.execute(
        update(Product)
        .where(Product.id == product_id)
        .values(in_stock=in_stock)
    )
    await db.commit()


async def get_product_by_id(db: AsyncSession, product_id: int):
    result = await db.execute(select(Product).where(Product.id == product_id))
    return result.scalars().first()