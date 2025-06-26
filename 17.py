from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from sqlalchemy.orm import selectinload
from sqlalchemy.future import select
from api_server import models  # Замена относительного импорта на абсолютный
from api_server.schemas import (  # Замена относительного импорта на абсолютный
    ProductCreate, ProductImageCreate, ProductSpecificationCreate,
    UserCreate, BannerCreate, CategoryCreate, SubcategoryCreate,
    CartItemCreate, OrderCreate, OrderItemCreate
)

import bcrypt


# Product CRUD
async def get_product(db: AsyncSession, product_id: int):
    result = await db.execute(
        select(models.Product)
        .options(
            joinedload(models.Product.images),
            joinedload(models.Product.specifications),
            joinedload(models.Product.subcategory)
        )
        .where(models.Product.id == product_id)
    )
    product = result.scalars().first()

    if product and product.images:
        for image in product.images:
            if image.image_url and not image.image_url.startswith("http"):
                image.image_url = convert_file_id_to_image_url(image.image_url)

    return product


async def get_products(db: AsyncSession, skip: int = 0, limit: int = 100):
    result = await db.execute(select(models.Product).offset(skip).limit(limit))
    return result.scalars().all()


async def create_product(db: AsyncSession, product: ProductCreate):
    db_product = models.Product(**product.dict())
    db.add(db_product)
    await db.commit()
    await db.refresh(db_product)
    return db_product


async def update_product(db: AsyncSession, product_id: int, product_data: dict):
    result = await db.execute(select(models.Product).filter(models.Product.id == product_id))
    db_product = result.scalars().first()
    if not db_product:
        return None
    for key, value in product_data.items():
        setattr(db_product, key, value)
    await db.commit()
    await db.refresh(db_product)
    return db_product


async def delete_product(db: AsyncSession, product_id: int):
    result = await db.execute(select(models.Product).filter(models.Product.id == product_id))
    db_product = result.scalars().first()
    if not db_product:
        return None
    await db.delete(db_product)
    await db.commit()
    return db_product


# Product Image CRUD
async def get_product_images(db: AsyncSession, product_id: int):
    """
    Получает все изображения для указанного продукта
    Возвращает данные как есть, без преобразования image_url
    """
    result = await db.execute(
        select(models.ProductImage)
        .filter(models.ProductImage.product_id == product_id)
    )
    return result.scalars().all()


async def get_product_details(db: AsyncSession, product_id: int):
    """
    Получает детали продукта с изображениями, характеристиками и подкатегорией
    Возвращает данные как есть, без преобразования image_url
    """
    result = await db.execute(
        select(models.Product)
        .options(
            selectinload(models.Product.images),
            selectinload(models.Product.specifications),
            selectinload(models.Product.subcategory)
        )
        .filter(models.Product.id == product_id)
    )
    return result.scalars().first()


async def create_product_image(db: AsyncSession, product_image: ProductImageCreate):
    # Если передан file_id, преобразуем его в URL
    if not product_image.image_url.startswith("http"):
        product_image.image_url = convert_file_id_to_image_url(product_image.image_url)

    db_image = models.ProductImage(**product_image.dict())
    db.add(db_image)
    await db.commit()
    await db.refresh(db_image)
    return db_image


async def update_product_image(db: AsyncSession, image_id: int, image_data: dict):
    result = await db.execute(select(models.ProductImage).filter(models.ProductImage.id == image_id))
    db_image = result.scalars().first()

    if not db_image:
        return None

    for key, value in image_data.items():
        setattr(db_image, key, value)

    if "image_url" in image_data and not db_image.image_url.startswith("http"):
        db_image.image_url = convert_file_id_to_image_url(db_image.image_url)

    await db.commit()
    await db.refresh(db_image)
    return db_image


# Product Specification CRUD
async def get_product_specifications(db: AsyncSession, product_id: int):
    result = await db.execute(
        select(models.ProductSpecification).filter(models.ProductSpecification.product_id == product_id))
    return result.scalars().all()


async def create_product_specification(db: AsyncSession, specification: ProductSpecificationCreate):
    db_spec = models.ProductSpecification(**specification.dict())
    db.add(db_spec)
    await db.commit()
    await db.refresh(db_spec)
    return db_spec


# User CRUD
async def get_user(db: AsyncSession, user_id: int):
    result = await db.execute(select(models.User).filter(models.User.user_id == user_id))
    return result.scalars().first()


async def get_users(db: AsyncSession, skip: int = 0, limit: int = 100):
    result = await db.execute(select(models.User).offset(skip).limit(limit))
    return result.scalars().all()


async def create_user(db: AsyncSession, user: UserCreate):
    # Проверка существующего пользователя
    result = await db.execute(
        select(models.User).where(
            (models.User.username == user.username) |
            (models.User.email == user.email)
        )
    )
    existing_user = result.scalars().first()

    if existing_user:
        raise HTTPException(status_code=400, detail="User already exists")

    # Хеширование пароля
    hashed_password = hash_password(user.password)

    # Создание пользователя
    db_user = models.User(
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        password=hashed_password,
        is_admin=False
    )

    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user


async def generate_new_user_id(db: AsyncSession) -> int:
    result = await db.execute(func.max(models.User.user_id))
    last_id = result.scalar() or 0
    return last_id + 1


def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode(), salt)
    return hashed.decode()


# Banner CRUD
async def get_banners(db: AsyncSession, skip: int = 0, limit: int = 100):
    result = await db.execute(select(models.Banner).offset(skip).limit(limit))
    return result.scalars().all()


async def create_banner(db: AsyncSession, banner: BannerCreate):
    db_banner = models.Banner(**banner.dict())
    db.add(db_banner)
    await db.commit()
    await db.refresh(db_banner)
    return db_banner


# Category CRUD
async def get_categories(db: AsyncSession, skip: int = 0, limit: int = 100):
    result = await db.execute(select(models.Category).offset(skip).limit(limit))
    return result.scalars().all()


async def create_category(db: AsyncSession, category: CategoryCreate):
    existing_category = await db.execute(
        select(models.Category).filter(models.Category.name == category.name)
    )
    if existing_category.scalars().first():
        raise HTTPException(status_code=400, detail="Категория с таким именем уже существует")
    db_category = models.Category(**category.model_dump())
    db.add(db_category)
    await db.commit()
    await db.refresh(db_category)
    return db_category


# Subcategory CRUD
async def get_subcategories(db: AsyncSession, skip: int = 0, limit: int = 100):
    result = await db.execute(select(models.Subcategory).offset(skip).limit(limit))
    return result.scalars().all()


async def create_subcategory(db: AsyncSession, subcategory: SubcategoryCreate):
    db_subcategory = models.Subcategory(**subcategory.dict())
    db.add(db_subcategory)
    await db.commit()
    await db.refresh(db_subcategory)
    return db_subcategory


# Cart CRUD
async def get_cart_items(db: AsyncSession, user_id: int):
    result = await db.execute(select(models.CartItem).filter(models.CartItem.user_id == user_id))
    return result.scalars().all()


async def create_cart_item(db: AsyncSession, cart_item: CartItemCreate):
    db_item = models.CartItem(**cart_item.dict())
    db.add(db_item)
    await db.commit()
    await db.refresh(db_item)
    return db_item


async def delete_cart_item(db: AsyncSession, cart_item_id: int):
    result = await db.execute(select(models.CartItem).filter(models.CartItem.id == cart_item_id))
    db_item = result.scalars().first()
    if not db_item:
        return None
    await db.delete(db_item)
    await db.commit()
    return db_item


# Order CRUD
async def get_orders(db: AsyncSession, skip: int = 0, limit: int = 100):
    result = await db.execute(select(models.Order).offset(skip).limit(limit))
    return result.scalars().all()


async def get_user_orders(db: AsyncSession, user_id: int):
    result = await db.execute(select(models.Order).filter(models.Order.user_id == user_id))
    return result.scalars().all()


async def create_order(db: AsyncSession, order: OrderCreate):
    db_order = models.Order(**order.dict())
    db.add(db_order)
    await db.commit()
    await db.refresh(db_order)
    return db_order


async def create_order_item(db: AsyncSession, order_item: OrderItemCreate, order_id: int):
    db_item = models.OrderItem(**order_item.dict(), order_id=order_id)
    db.add(db_item)
    await db.commit()
    await db.refresh(db_item)
    return db_item


async def update_order_status(db: AsyncSession, order_id: int, status: str):
    result = await db.execute(select(models.Order).filter(models.Order.id == order_id))
    db_order = result.scalars().first()
    if not db_order:
        return None
    db_order.status = status
    await db.commit()
    await db.refresh(db_order)
    return db_order


async def get_products_by_subcategory(
        db: AsyncSession,
        subcategory_id: int,
        skip: int = 0,
        limit: int = 100
):
    query = (
        select(models.Product)
        .where(models.Product.subcategory_id == subcategory_id)
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(query)
    return result.scalars().all()


async def get_subcategories_by_category(
        db: AsyncSession,
        category_id: int,
        skip: int = 0,
        limit: int = 100
):
    query = (
        select(models.Subcategory)
        .where(models.Subcategory.category_id == category_id)
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(query)
    return result.scalars().all()



