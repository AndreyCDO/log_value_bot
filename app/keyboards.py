from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


startbutton = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Далее', callback_data='startbutton')]
])

terrace_exists_kb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Да', callback_data='Терраса есть'),
     InlineKeyboardButton(text='Нет', callback_data='Террасы нет')]
])

terrace_railings_kb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Да', callback_data='Перила из материала сруба'),
     InlineKeyboardButton(text='Нет', callback_data='Перил террасы нет')]
])

first_floor_windows_kb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Максимально большие, в пол', callback_data='Окна 1го этажа большие, в пол')],
    [InlineKeyboardButton(text='Большие, широкие', callback_data='Окна 1го этажа большие, широкие')],
    [InlineKeyboardButton(text='Стандартные', callback_data='Окна 1го этажа стандартные')]
])

second_floor_exists_kb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Нет, будет только один этаж', callback_data='Второго этажа нет')],
    [InlineKeyboardButton(text='Да, мансардного типа', callback_data='Второй этаж мансардного типа')],
    [InlineKeyboardButton(text='Да, полноценный второй этаж', callback_data='Полноценный второй этаж')]
])

second_floor_windows_kb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Максимально большие, в пол', callback_data='Окна 2го этажа большие, в пол')],
    [InlineKeyboardButton(text='Большие, широкие', callback_data='Окна 2го этажа большие, широкие')],
    [InlineKeyboardButton(text='Стандартные', callback_data='Окна 2го этажа стандартные')]
])

balcony_exists_kb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Да', callback_data='Балкон есть'),
     InlineKeyboardButton(text='Нет', callback_data='Балкона нет')]
])

roof_type_kb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Односкатная', callback_data='Односкатная')],
    [InlineKeyboardButton(text='Двускатная', callback_data='Двускатная')],
    [InlineKeyboardButton(text='Вальмовая (четырёхскатная)', callback_data='Вальмовая')]
])

fronton_type_kb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Да, из того же', callback_data='Фронтоны полноценные')],
    [InlineKeyboardButton(text='Нет, будут зашиваться доской', callback_data='Фронтоны зашиваются доской')]
])

foundation_type_kb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Свайный', callback_data='Свайный')],
    [InlineKeyboardButton(text='Ленточный', callback_data='Ленточный')],
    [InlineKeyboardButton(text='Монолитная плита', callback_data='Монолитная плита')]
])

house_material_kb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Оцилиндрованное бревно', callback_data='Оцилиндрованное бревно')],
    [InlineKeyboardButton(text='Профилированный, клееный брус', callback_data='Профилированный, клееный брус')],
    [InlineKeyboardButton(text='Строганный брус', callback_data='Строганный брус')]
])

calculation_or_back_kb  = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Всё верно. Сделать расчёт.', callback_data='calculation_step')],
    [InlineKeyboardButton(text='Допущена ошибка. Начнём сначала.', callback_data='startbutton')]
])

finalbutton_kb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Новый расчёт', callback_data='startbutton')]
])