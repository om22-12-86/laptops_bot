from aiogram.fsm.state import StatesGroup, State

class AddProduct(StatesGroup):
    name = State()
    description = State()
    price = State()
    image_url = State()
    category_id = State()

class AddCategory(StatesGroup):
    name = State()

class AddBanner(StatesGroup):
    image_url = State()
    description = State()