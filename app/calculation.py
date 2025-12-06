from typing import Dict, Any
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
import app.keyboards as kb
import math

# Вывод всех введённых параметров сруба
async def output_of_values(message: Message, state: FSMContext) -> None:
    
    # Получаем все данные из FSM
    data: dict = await state.get_data()

    # Словарь ключ FSM -> "Читаемое имя"
    fields = [
        ("width", "Ширина сруба, мм"),
        ("length", "Длина сруба, мм"),
        ("terrace_exists", "Наличие террасы"),
        ("terrace_width", "Ширина террасы, мм"),
        ("terrace_length", "Длина террасы, мм"),
        ("terrace_railings", "Перила террасы"),
        ("first_floor_rooms", "Кол-во помещений 1го этажа"),
        ("first_floor_height", "Высота потолков 1го этажа, мм"),
        ("first_floor_windows", "Окна первого этажа"),
        ("second_floor_exists", "Наличие 2го этажа"),
        ("second_floor_full_height", "Высота стен 2го этажа, мм"),
        ("second_floor_attic_height", "Высота аттиковой стены, мм"),
        ("second_floor_windows", "Окна второго этажа"),
        ("second_floor_rooms", "Кол-во помещений 2го этажа"),
        ("balcony_exists", "Наличие балкона во всю ширину террасы"),
        ("roof_type", "Тип кровли"),
        ("roof_angle", "Угол кровли в градусах"),
        ("fronton_type", "Тип фронтонов"),
        ("foundation_type", "Тип фундамента"),
        ("house_material", "Материал сруба"),
        ("log_diametr", "Диаметр бревна, мм"),
        ("profiled_timber_width", "Ширина профилированного бруса, мм"),
        ("profiled_timber_height", "Габаритная высота бруса, мм"),
        ("profiled_timber_row_height", "Рабочая высота бруса, мм"),
        ("planed_timber_width", "Ширина строганного бруса, мм"),
        ("planed_timber_height", "Высота строганного бруса, мм"),
    ]

    def pretty(value: Any) -> str:
        if value is None or value == "":
            return None  # Если значение пустое, не выводим строку
        if isinstance(value, bool):
            return "Да" if value else "Нет"
        return str(value)

    lines = []
    for key, label in fields:
        value = pretty(data.get(key))
        if value is not None:
            # HTML: название жирным, значение обычным
            lines.append(f"{label}: <b>{value}</b>")

    if lines:
        text = "<b>Введённые значения:</b>\n\n" + "\n".join(lines)
        await message.answer(text, parse_mode="HTML", reply_markup=kb.calculation_or_back_kb)
    else:
        await message.answer("Нет введённых данных.", reply_markup=kb.calculation_or_back_kb)


#---------------------------------------------------
# Временная функция для печати промежуточных расчётов
#---------------------------------------------------

async def print_interim_calc(message: Message, state: FSMContext):
    vypuski_value = await vypuski_calc(state)
    width_with_vypuski, length_with_vypuski = await add_vypuski_to_width_length(state)
    koef1, koef2 = await calculate_room_coefs(state)
    terrace_koef = await terrace_coef(state)
    terrace_wall_area, terrace_wall_volume = await calculate_terrace_wall_area(state, terrace_koef), 2
    first_floor_area, first_floor_volume = await calculate_first_floor_wall_volume(
        state,
        length_with_vypuski,
        width_with_vypuski,
        terrace_wall_area,
        koef1
    )
    # Расчёты по 2му этажу:
    balkony_wall_area = await calculate_balkon_wall_area(state, terrace_wall_area)
    wall_length2 = await calculate_wall_length2(state, width_with_vypuski, length_with_vypuski, koef2)
    konek_height = await calculate_konek_height(state)
    wall_area2_raw = await calculate_wall_area2_raw(state, wall_length2, konek_height)
    doors_area2, win_area2 = await calculate_openings_area2(state)
    wall_area2 = await calculate_wall_area2(wall_area2_raw, balkony_wall_area, doors_area2, win_area2)
    wall_volume2 = await calculate_wall_volume2(state, wall_area2)
    fronton_num = await calculate_fronton_num(state)
    fronton_volume = await calculate_fronton_volume(state, width_with_vypuski, konek_height, fronton_num)
    total_volume = await total_volume_calculate(first_floor_volume, wall_volume2, fronton_volume)


    await message.answer(f"""Длина выпусков: {vypuski_value} мм
Длина сруба с выпусками: {length_with_vypuski} мм
Ширина сруба с выпусками: {width_with_vypuski} мм
Коэффициент 1го этажа: {koef1}
Коэффициент 2го этажа: {koef2}
Коэффициент стен террасы: {terrace_koef}
Площадь стен террасы: {terrace_wall_area} м.кв.
Площадь стен 1го этажа: {first_floor_area} м.кв.
Объём стен 1го этажа: {first_floor_volume} м.куб.
Площадь стен балкона: {balkony_wall_area} м.кв.
Длина стен 2го этажа: {wall_length2} м.п.
Высота конька: {konek_height} мм
Плоощадь стен 2го этажа {wall_area2} м.кв.
Объём стен 2го этажа: {wall_volume2} м.куб.
Количество фронтонов: {fronton_num}
Объём фронтонов: {fronton_volume} м.куб.
Общий объём материала на сруб: {total_volume} м.куб.""")

#---------------------------------------------------
# Расчёт кубатуры сруба
#---------------------------------------------------

#Расчёт выпусков
async def vypuski_calc(state: FSMContext):
    
    data = await state.get_data()
    house_material = data.get('house_material')
    vypuski_value = 0
    
    if house_material == 'Оцилиндрованное бревно':
        log_diametr = int(data.get('log_diametr'))
        vypuski_value = log_diametr*1.5
    elif house_material == 'Профилированный, клееный брус':
        profiled_timber_width = int(data.get('profiled_timber_width'))
        vypuski_value = profiled_timber_width*1.5
    elif house_material == 'Строганный брус':
        planed_timber_width = int(data.get('planed_timber_width'))
        vypuski_value = planed_timber_width*0.5
        
    await state.update_data(vypuski=vypuski_value)    
    return vypuski_value


# Добавление выпусков к ширине и длине сруба
async def add_vypuski_to_width_length(state: FSMContext) -> tuple[int,int]:
    data = await state.get_data()
    width = int(data.get('width'))
    length = int(data.get('length'))
    vypuski = int(await vypuski_calc(state))
    
    width_with_vypuski = width + vypuski * 2
    length_with_vypuski = length + vypuski * 2
    
    await state.update_data(
        width_with_vypuski=width_with_vypuski,
        length_with_vypuski=length_with_vypuski
    )
    return width_with_vypuski, length_with_vypuski
    
# Функция для расчёта коэффицианта в зависимости от количества помещений на 1м и 2м этажах:
def get_room_coef(rooms: int, floor: int) -> float:
    
    coef_first = {
        1: 1,
        2: 1.25,
        3: 1.38,
        4: 1.55,
        5: 1.67,
        6: 1.80,
        7: 1.93,
        8: 2.05,
        9: 2.15,
        10: 2.25,
    }

    coef_second = {
        1: 1,
        2: 1.25,
        3: 1.38,
        4: 1.5,
        5: 1.62,
        6: 1.75,
        7: 1.88,
        8: 2,
        9: 2.1,
        10: 2.2,
    }

    if floor == 1:
        return coef_first.get(rooms, None)
    elif floor == 2:
        return coef_second.get(rooms, None)

# Сама фунция расчёта коэффициентов
async def calculate_room_coefs(state: FSMContext) -> tuple[float, float]:
    data = await state.get_data()

    first_floor_rooms = int(data.get("first_floor_rooms", 0))
    second_floor_rooms = int(data.get("second_floor_rooms", 0))

    koef1 = get_room_coef(first_floor_rooms, floor=1)
    koef2 = get_room_coef(second_floor_rooms, floor=2)

    # Можно сохранить в state при желании
    await state.update_data(koef1=koef1, koef2=koef2)

    return koef1, koef2

#------------------------------------------------------
#Далее идут функции для расчёта объёма стен 1го этажа:
#------------------------------------------------------


# Расчёт коэффициента площади стен террасы в зависимости от типа перил
async def terrace_coef(state: FSMContext) -> float:
    data = await state.get_data()
    house_material = data.get('house_material', '')

    if house_material == "Оцилиндрованное бревно":
        log_diametr = int(data.get('log_diametr', 0))
        terrace_koef = log_diametr * 0.001
    elif house_material == "Профилированный, клееный брус":
        timber_width = int(data.get('profiled_timber_width', 0))
        terrace_koef = timber_width * 0.001
    elif house_material == "Строганный брус":
        timber_width = int(data.get('planed_timber_width', 0))
        terrace_koef = timber_width * 0.001
    else:
        terrace_koef = 0  # На случай неизвестного материала

    # Сохраняем коэффициент в state
    await state.update_data(terrace_koef=terrace_koef)
    return terrace_koef


# Расчёт площади стен террасы:
async def calculate_terrace_wall_area(state: FSMContext, terrace_koef: float) -> float:
    data = await state.get_data()
    
    terrace_type = data.get('terrace_railings')
    terrace_width = int(data.get('terrace_width', 0))
    terrace_length = int(data.get('terrace_length', 0))

    # Если террасы нет, возвращаем 0
    if terrace_type is None or terrace_width == 0 or terrace_length == 0:
        return 0

    if terrace_type == 'Перила из материала сруба':  # "Из того же материала"
        # (ширина + длина*2) * коэф * 5
        wall_area = (terrace_width*0.001 + terrace_length*0.001*2) * terrace_koef * 5
    elif terrace_type == 'Перил террасы нет':  # "Просто столбы"
        # (длина*2 + ширина)*2*коэф + ceil(ширина/2)*коэф + ceil(длина/2)
        wall_area = ((terrace_length*0.001*2 + terrace_width*0.001)*2*terrace_koef +
                     math.ceil(terrace_width*0.001/2)*terrace_koef +
                     math.ceil(terrace_length*0.001/2)*terrace_koef)
    else:
        wall_area = 0

    # Сохраняем результат в FSM
    await state.update_data(terrace_wall_area=wall_area)
    return round(wall_area, 2)


# Расчёт объёма стен 1го этажа:
async def calculate_first_floor_wall_volume(
    state: FSMContext,
    length_with_vypuski: float,       # длина стен с учётом выпусков (в метрах)
    width_with_vypuski: float,        # ширина стены (в метрах)
    terrace_wall_area: float,
    koef1: float
    ) -> float:
    
    data = await state.get_data()
    first_floor_height = data.get('first_floor_height')
    first_floor_rooms = data.get('first_floor_rooms')
    first_floor_windows = data.get('first_floor_windows')
    
    # Получаем толщину материала
    house_material = data.get('house_material')
    if house_material == 'Оцилиндрованное бревно':
        wall_width1 = int(data.get('log_diametr')) * 0.001  # перевод в метры
    elif house_material == 'Профилированный, клееный брус':
        wall_width1 = int(data.get('profiled_timber_width')) * 0.001
    else:  # Строганный брус
        wall_width1 = int(data.get('planed_timber_width')) * 0.001


    # Площадь дверей
    doors_area = 0.8 * 2.1 * first_floor_rooms  # площадь дверей в м²

    # Площадь окон
    if first_floor_rooms == 1:
        win1_big = 2
    elif first_floor_rooms == 2:
        win1_big = 3
    else:
        win1_big = 4

    if first_floor_windows == "Окна 1го этажа большие, в пол":
        win_area = 1.8 * 2.3 * win1_big
    elif first_floor_windows == "Окна 1го этажа большие, широкие":
        win_area = 1.6 * 1.5 * win1_big
    else:  # Окна 1го этажа стандартные
        win_area = 1.4 * 1.2 * win1_big
        
    # Длина стен первого этажа (м.п.)
    wall_length1 = (width_with_vypuski + length_with_vypuski)*2*koef1*0.001

    # Площадь стен первого этажа (м²)
    wall_area = wall_length1 * ((first_floor_height + 200) * 0.001) + terrace_wall_area - doors_area - win_area

    # Объём стен первого этажа (м³) с поправкой 1.02
    wall_volume = wall_area * wall_width1 * 1.02

    # Сохраняем результаты в state
    await state.update_data(first_floor_wall_area=wall_area, first_floor_wall_volume=wall_volume)

    return round(wall_area, 2), round(wall_volume, 2)


#------------------------------------------------------
#Далее идут функции для расчёта объёма стен 2го этажа:
#------------------------------------------------------

# Расчёт площади стен балкона. По сути, если балкон есть, то площадь его стен равна площади стен террасы(для упрощения)
async def calculate_balkon_wall_area(state: FSMContext, terrace_wall_area: float) -> float:
    data = await state.get_data()
    balcony_exists = data.get("balcony_exists")  # "Балкон есть" / "Балкона нет"

    if balcony_exists == "Балкон есть":
        return round(terrace_wall_area, 2)
    return 0


#Расчёт длины стен 2го этажа
async def calculate_wall_length2(
    state: FSMContext,
    width_with_vypuski: float,
    length_with_vypuski: float,
    koef2: float
) -> float:

    data = await state.get_data()
    second_floor_exists = data.get("second_floor_exists")

    if second_floor_exists == None:
        return 0

    return round((width_with_vypuski + length_with_vypuski) * 2 * koef2 * 0.001, 2)



#Расчёт конька по углу крыши:
async def calculate_konek_height(state: FSMContext) -> float:
    data = await state.get_data()
    roof_angle = data.get("roof_angle")       # градусы
    width = data.get("width")             # мм

    angle_radian = roof_angle * math.pi / 180
    angle_tan = math.tan(angle_radian)

    konek_height = angle_tan * (width/2)
    return round(konek_height, 2)


# Расчёт площади стен 2го этажа без учёта окон, дверей:
async def calculate_wall_area2_raw(
    state: FSMContext,
    wall_length2: float,
    konek_height: float
) -> float:

    data = await state.get_data()

    second_floor_exists = data.get("second_floor_exists")
    second_floor_full_height = data.get("second_floor_full_height")
    second_floor_attik_height = data.get("second_floor_attic_height")

    if second_floor_exists == "Полноценный второй этаж":
        return wall_length2 * (second_floor_full_height + 200) * 0.001

    elif second_floor_exists == "Второй этаж мансардного типа":
        return round((wall_length2 * second_floor_attik_height * 0.001) + (wall_length2 * konek_height * 0.001 / 1.8), 2)

    return 0


# Расчёт площади окон и дверей 2го этажа:
async def calculate_openings_area2(state: FSMContext) -> tuple[float, float]:
    data = await state.get_data()

    second_floor_rooms = data.get("second_floor_rooms")
    second_floor_windows = data.get("second_floor_windows")  # строка

    # Площадь дверей
    doors_area2 = 0.8 * 2.1 * second_floor_rooms

    # Кол-во больших окон
    if second_floor_rooms == 1:
        win_big = 2
    elif second_floor_rooms == 2:
        win_big = 3
    else:
        win_big = 4

    # Площадь окон
    if second_floor_windows == "Окна 2го этажа большие, в пол":
        win_area2 = 1.8 * 2.3 * win_big
    elif second_floor_windows == "Окна 2го этажа большие, широкие":
        win_area2 = 1.6 * 1.5 * win_big
    else:
        win_area2 = 1.4 * 1.2 * win_big #Окна 2го этажа стандартные

    return doors_area2, win_area2


# Финальная площадь стен 2го этажа: 
async def calculate_wall_area2(
    wall_area2_raw: float,
    balkon_wall_area: float,
    doors_area: float,
    win_area: float
) -> float:

    return round(wall_area2_raw + balkon_wall_area - doors_area - win_area, 2)


#Расчёт объёма стен 2го этажа: 
async def calculate_wall_volume2(state: FSMContext, wall_area2: float) -> float:
    data = await state.get_data()
    material = data.get("house_material")

    if material == "Оцилиндрованное бревно":
        wall_width = int(data.get("log_diametr")) * 0.001 * 0.91
    elif material == "Профилированный, клееный брус":
        wall_width = int(data.get("profiled_timber_width")) * 0.001 * 1.09
    else:
        wall_width = int(data.get("planed_timber_width")) * 0.001
        
    wall_volume2 = wall_area2 * wall_width * 1.02

    return round(wall_volume2, 2)


# Расчёт количества фронтонов:
async def calculate_fronton_num(state: FSMContext) -> int:
    data = await state.get_data()

    roof_type = data.get("roof_type")
    second_floor_exists = data.get("second_floor_exists")
    first_floor_rooms = data.get("first_floor_rooms")
    second_floor_rooms = data.get("second_floor_rooms")

    # количество комнат
    if second_floor_exists == "Полноценный второй этаж":
        rooms = second_floor_rooms
    elif second_floor_exists == "Второго этажа нет" or second_floor_exists == None:
        rooms = first_floor_rooms
    else:
        rooms = 0

    if roof_type == "Двускатная":
        if rooms == 1:
            return 2
        elif rooms == 2:
            return 3
        elif rooms == 3:
            return 3
        elif rooms == 4:
            return 3
        elif rooms > 4:
            return 4
        return 0

    if roof_type == "Односкатная":
        if rooms == 1:
            return 2
        elif rooms == 2:
            return 3
        elif rooms == 3:
            return 3
        elif rooms == 4:
            return 3
        elif rooms > 4:
            return 4
        return 0

    return 0


# Расчёт объёма фронтонов:
async def calculate_fronton_volume(
        state: FSMContext,
        width_with_vypuski: float,
        konek_height: float,
        fronton_num: int
    ) -> float:

    data = await state.get_data()
    fronton_type = data.get("fronton_type")

    if fronton_type == "Фронтоны зашиваются доской":
        return 0

    # --- 1. Расчёт площади одного фронтона ---
    # Формула: площадь = (ширина * высота) / 2
    fronton_area = (width_with_vypuski * 0.001) * (konek_height * 0.001) / 2

    # --- 2. Определяем толщину стены  ---
    material = data.get("house_material")

    if material == "Оцилиндрованное бревно":
        wall_width = int(data.get("log_diametr")) * 0.001 * 0.91
    elif material == "Профилированный, клееный брус":
        wall_width = int(data.get("profiled_timber_width")) * 0.001 * 1.09
    else:
        wall_width = int(data.get("planed_timber_width")) * 0.001

    # --- 3. Итоговый объём ---
    fronton_volume = fronton_area * fronton_num * wall_width

    return round(fronton_volume, 2)


# Расчёт итогового объёма стен:
async def total_volume_calculate (first_floor_volume, wall_volume2, fronton_volume):
    total_volume = first_floor_volume + wall_volume2 + fronton_volume
    return round(total_volume, 2)


#--------------------------------------------------------
# Функция финальных расчётов и вывода их на печать
#--------------------------------------------------------
async def print_final_calc(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    width_with_vypuski, length_with_vypuski = await add_vypuski_to_width_length(state)
    koef1, koef2 = await calculate_room_coefs(state)
    terrace_koef = await terrace_coef(state)
    terrace_wall_area, terrace_wall_volume = await calculate_terrace_wall_area(state, terrace_koef), 2
    first_floor_area, first_floor_volume = await calculate_first_floor_wall_volume(
        state,
        length_with_vypuski,
        width_with_vypuski,
        terrace_wall_area,
        koef1
    )
    
    # Расчёт объёма фронтонов
    konek_height = await calculate_konek_height(state)
    fronton_num = await calculate_fronton_num(state)
    fronton_volume = await calculate_fronton_volume(state, width_with_vypuski, konek_height, fronton_num)
    
    # Проверяем, существует ли второй этаж
    if data.get('second_floor_exists') is None or data.get('second_floor_exists') == "Второго этажа нет":

        # Если второго этажа нет — все переменные второго этажа = 0
        balkony_wall_area = 0
        wall_length2 = 0
        konek_height = 0
        wall_area2_raw = 0
        doors_area2 = 0
        win_area2 = 0
        wall_area2 = 0
        wall_volume2 = 0
        
    else:
        # Расчёты по 2му этажу
        balkony_wall_area = await calculate_balkon_wall_area(state, terrace_wall_area)
        wall_length2 = await calculate_wall_length2(state, width_with_vypuski, length_with_vypuski, koef2)
        wall_area2_raw = await calculate_wall_area2_raw(state, wall_length2, konek_height)
        doors_area2, win_area2 = await calculate_openings_area2(state)
        wall_area2 = await calculate_wall_area2(wall_area2_raw, balkony_wall_area, doors_area2, win_area2)
        wall_volume2 = await calculate_wall_volume2(state, wall_area2)
    
    # Итоговая сумма
    total_volume = await total_volume_calculate(first_floor_volume, wall_volume2, fronton_volume)

    await callback.message.answer(
        f"""Объём стен 1го этажа: <b>{first_floor_volume}</b> м³
Объём стен 2го этажа и фронтонов: <b>{wall_volume2 + fronton_volume}</b> м³
Общий объём материала на сруб: <b>{total_volume}</b> м³

Значения расчитаны с учётом усреднённых коэффициентов. 
Они дают лишь примерную оценку объёма материала на сруб.
Для точного расчёта, необходимо сделать проект.
Обратитесь к <a href="https://t.me/AndreyCDO">проектировщику срубов</a>""",
        parse_mode="HTML",
        reply_markup=kb.finalbutton_kb
    )


