from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Boolean, Enum, BigInteger
from sqlalchemy.orm import declarative_base, relationship
from enum import Enum as PyEnum
from datetime import datetime

Base = declarative_base()

# Определяем перечисление для статусов заказа
class OrderStatus(str, PyEnum):
    PROCESSING = "PROCESSING"
    READY_FOR_PICKUP = "READY_FOR_PICKUP"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"

# Модель пользователя
class User(Base):
    __tablename__ = 'users'
    user_id = Column(BigInteger, primary_key=True)  # Используем BigInteger для user_id
    username = Column(String)
    full_name = Column(String)
    is_admin = Column(Boolean, default=False)
    orders = relationship('Order', back_populates='user')
    cart_items = relationship('CartItem', back_populates='user', cascade="all, delete-orphan")

# Модель баннера
class Banner(Base):
    __tablename__ = 'banner'
    id = Column(Integer, primary_key=True, index=True)
    image_url = Column(String, nullable=False)
    file_type = Column(String, nullable=False)
    description = Column(String, nullable=True)
    title = Column(String, nullable=True)
    banner_type = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

# Модель категории
class Category(Base):
    __tablename__ = 'categories'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    subcategories = relationship('Subcategory', back_populates='category')

# Модель подкатегории
class Subcategory(Base):
    __tablename__ = 'subcategories'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    category_id = Column(Integer, ForeignKey('categories.id'))
    category = relationship('Category', back_populates='subcategories')
    products = relationship('Product', back_populates='subcategory')

# Модель изображения продукта
class ProductImage(Base):
    __tablename__ = 'product_images'
    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey('products.id'))
    image_url = Column(String, nullable=False)
    file_type = Column(String, nullable=False)
    product = relationship('Product', back_populates='images')

# Модель спецификаций продукта
class ProductSpecification(Base):
    __tablename__ = 'product_specifications'
    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey('products.id'))
    key = Column(String, nullable=False)
    value = Column(String, nullable=False)
    product = relationship('Product', back_populates='specifications')

# Модель продукта
class Product(Base):
    __tablename__ = 'products'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=False)
    price = Column(Float, nullable=False)
    image_url = Column(String, nullable=False)
    in_stock = Column(Boolean, default=True)
    file_type = Column(String, nullable=False)
    sku = Column(String, nullable=False, unique=True)
    subcategory_id = Column(Integer, ForeignKey('subcategories.id'), nullable=False)
    brand = Column(String)  # Поле для бренда
    diagonal = Column(String)  # Поле для диагонали

    # Связи с другими таблицами
    subcategory = relationship('Subcategory', back_populates='products')
    cart_items = relationship('CartItem', back_populates='product', cascade="all, delete-orphan")
    order_items = relationship('OrderItem', back_populates='product', cascade="all, delete-orphan")
    images = relationship('ProductImage', back_populates='product', cascade="all, delete-orphan")
    specifications = relationship('ProductSpecification', back_populates='product', cascade="all, delete-orphan")

# Модель записи в корзину
class CartItem(Base):
    __tablename__ = 'cart_items'
    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, ForeignKey('users.user_id'))  # Изменено на BigInteger для user_id
    product_id = Column(Integer, ForeignKey('products.id'))
    quantity = Column(Integer, default=1)
    user = relationship('User', back_populates='cart_items')
    product = relationship('Product', back_populates='cart_items')

# Модель заказа
class Order(Base):
    __tablename__ = 'orders'
    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, ForeignKey('users.user_id'))  # Изменено на BigInteger для user_id
    created_at = Column(DateTime, default=datetime.utcnow)
    status = Column(Enum(OrderStatus, name="order_status"), default=OrderStatus.PROCESSING.value)
    user = relationship('User', back_populates='orders')
    items = relationship('OrderItem', back_populates='order', cascade="all, delete-orphan")
    is_deleted = Column(Boolean, default=False)

# Модель товара в заказе
class OrderItem(Base):
    __tablename__ = 'order_items'
    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey('orders.id'))
    product_id = Column(Integer, ForeignKey('products.id'))
    quantity = Column(Integer)
    order = relationship('Order', back_populates='items')
    product = relationship('Product')
