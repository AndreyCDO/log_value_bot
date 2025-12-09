import math
from aiogram.fsm.context import FSMContext


#Расчёт количества свай

async def calculate_total_piles(state: FSMContext) -> int:
    data = await state.get_data()

    # ===== Дом =====
    width = (data.get("width") or 0) / 1000
    length = (data.get("length") or 0) / 1000

    piles_per_row = math.ceil(width / 2) + 1
    rows = math.ceil(length / 2) + 1
    house_piles = piles_per_row * rows

    # ===== Терраса =====
    terrace_exists = data.get("terrace_exists")
    terrace_piles = 0
    if terrace_exists and terrace_exists != "Террасы нет":
        terrace_width = (data.get("terrace_width") or 0) / 1000
        terrace_length = (data.get("terrace_length") or 0) / 1000

        piles_per_row_terrace = math.ceil(terrace_width / 2) + 1
        rows_terrace = math.ceil(terrace_length / 2) + 1

        # Убираем один ряд свай вдоль примыкания к дому
        rows_terrace = max(rows_terrace - 1, 0)

        terrace_piles = piles_per_row_terrace * rows_terrace

    total_piles = house_piles + terrace_piles
    return total_piles


# Расчёт площади ленточного фундамента:
async def calculate_strip_foundation_area(state: FSMContext) -> float:
    data = await state.get_data()

    # ===== Общая длина стен первого этажа =====
    wall_length1 = data.get("first_floor_wall_length", 0)
    if wall_length1 == 0:
        width = int(data.get("width", 0))
        length = int(data.get("length", 0))
        koef1 = data.get("koef1", 1)
        wall_length1 = (width + length) * 2 * koef1 / 1000  # метры

    # ===== Учёт террасы =====
    terrace_exists = data.get("terrace_exists")
    terrace_length = int(data.get("terrace_length", 0))
    terrace_width = int(data.get("terrace_width", 0))

    if terrace_exists and terrace_length > 0 and terrace_width > 0:
        # Терраса примыкает к дому по длине, поэтому убираем одну примыкающую стену
        # Добавляем оставшиеся 3 стороны террасы: длина + 2 ширины
        wall_length1 += (terrace_length + 2 * terrace_width) / 1000  # метры

    # ===== Ширина ленточного фундамента =====
    strip_width = 0.3  # по умолчанию 300 мм
    strip_area = wall_length1 * strip_width  # площадь поверхности ленточного фундамента в м²

    return round(strip_area, 2)


# Расчёт площади монолитной плиты фундамента:
from aiogram.fsm.context import FSMContext

async def calculate_slab_foundation_area(state: FSMContext) -> float:
    data = await state.get_data()

    # ===== Толщина материала сруба =====
    log_thickness = data.get("log_diametr") or data.get("profiled_timber_width") or data.get("planed_timber_width") or 0
    log_thickness_m = log_thickness / 1000  # переводим в метры

    # ===== Площадь плиты под дом =====
    width = (data.get("width") or 0) / 1000
    length = (data.get("length") or 0) / 1000
    slab_width = width + log_thickness_m
    slab_length = length + log_thickness_m
    house_slab_area = slab_width * slab_length

    # ===== Площадь плиты под террасу =====
    terrace_area = 0
    terrace_exists = data.get("terrace_exists")
    if terrace_exists and terrace_exists != "Террасы нет":
        terrace_width = (data.get("terrace_width") or 0) / 1000
        terrace_length = (data.get("terrace_length") or 0) / 1000
        terrace_slab_width = terrace_width + log_thickness_m
        terrace_slab_length = terrace_length + log_thickness_m
        terrace_area = terrace_slab_width * terrace_slab_length

    total_slab_area = house_slab_area + terrace_area
    return round(total_slab_area, 2)
