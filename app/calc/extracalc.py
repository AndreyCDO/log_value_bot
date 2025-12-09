
import math
from aiogram.fsm.context import FSMContext

# Расчёт площади крыши на основе данных сруба.
async def roof_area(state: FSMContext) -> float:
    data = await state.get_data()

    # Основные размеры
    width = int(data.get("width", 0))       # ширина сруба, мм
    length = int(data.get("length", 0))     # длина сруба, мм
    roof_type = data.get("roof_type")       # тип кровли
    roof_angle = data.get("roof_angle", 0)  # угол, градусы
    roof_overhangs = int(data.get("roof_overhangs", 0))  # свесы, мм
    house_material = data.get("house_material")

    # Данные о террасе
    terrace_exists = data.get("terrace_exists")
    terrace_width = int(data.get("terrace_width", 0))
    terrace_length = int(data.get("terrace_length", 0))

    # Половина толщины материала
    if house_material == "Оцилиндрованное бревно":
        half_thickness = int(data.get("log_diametr", 0)) / 2
    elif house_material == "Профилированный, клееный брус":
        half_thickness = int(data.get("profiled_timber_width", 0)) / 2
    elif house_material == "Строганный брус":
        half_thickness = int(data.get("planed_timber_width", 0)) / 2
    else:
        half_thickness = 0

    # Полные размеры
    full_width = width + half_thickness * 2 + roof_overhangs * 2
    full_length = length + half_thickness * 2 + roof_overhangs * 2

    # В метры
    full_width_m = full_width / 1000
    full_length_m = full_length / 1000

    # Угол в радианах
    angle_rad = math.radians(roof_angle)

    # === Основная кровля ===
    if roof_type == "Односкатная":
        slope_length = full_width_m / math.cos(angle_rad)
        area = slope_length * full_length_m

    elif roof_type == "Двускатная":
        h = math.tan(angle_rad) * (full_width_m / 2)
        slope_length = math.sqrt((full_width_m / 2) ** 2 + h ** 2)
        area = slope_length * full_length_m * 2

    elif roof_type == "Вальмовая":
        h = math.tan(angle_rad) * (full_width_m / 2)

        slope_width = math.sqrt((full_width_m / 2) ** 2 + h ** 2)
        slope_length = math.sqrt((full_length_m / 2) ** 2 + h ** 2)

        ridge_length = full_length_m - full_width_m
        if ridge_length < 0:
            ridge_length = 0

        area_trapezoids = 2 * ((ridge_length + full_length_m) / 2) * slope_width
        area_triangles = 2 * (0.5 * full_width_m * slope_length)

        area = area_trapezoids + area_triangles

    else:
        area = 0

    # === Кровля над террасой (односкатная) ===
    if terrace_exists and terrace_width > 0 and terrace_length > 0:
        terrace_slope_width = (terrace_length + half_thickness * 2 + roof_overhangs * 2) / 1000
        terrace_slope_length = (terrace_width + half_thickness + roof_overhangs) / 1000 / math.cos(angle_rad)
        terrace_area = terrace_slope_width * terrace_slope_length
        area += terrace_area

    # Округлённая площадь
    area_rounded = round(area, 2)

    # === Сохраняем площадь крыши в состояния ===
    await state.update_data(roof_area=area_rounded)

    return area_rounded



# Расчёт объёма окладного венца или подкладочной доски.
async def oklad_venets_volume(state: FSMContext) -> dict:
    data = await state.get_data()

    # Длина всех стен 1го этажа в метрах (периметр)
    wall_length1 = data.get("first_floor_wall_length", 0)  # проверяем, что это поле есть
    if wall_length1 == 0:
        # Если нет, считаем через ширину/длину
        width = int(data.get("width", 0))
        length = int(data.get("length", 0))
        koef1 = data.get("koef1", 1)
        wall_length1 = (width + length) * 2 * koef1 / 1000  # в метрах

    # Учёт террасы
    terrace_exists = data.get("terrace_exists", False)
    terrace_length = int(data.get("terrace_length", 0))
    terrace_width = int(data.get("terrace_width", 0))
    if terrace_exists and terrace_length > 0 and terrace_width > 0:
        # Добавляем длину террасы и по две ширины террасы
        wall_length1 += (terrace_length + 2 * terrace_width) / 1000  # переводим в метры

    # Тип фундамента
    foundation_type = data.get("foundation_type", "")
    
    # Ширина материала (мм)
    house_material = data.get("house_material")
    if house_material == "Оцилиндрованное бревно":
        material_width = int(data.get("log_diametr", 0))
    elif house_material == "Профилированный, клееный брус":
        material_width = int(data.get("profiled_timber_width", 0))
    else:  # строганный брус
        material_width = int(data.get("planed_timber_width", 0))
    
    # Определяем размеры окладного венца или подкладочной доски
    if foundation_type in ["Свайный", "Ленточный"]:
        # Окладной венец
        if material_width <= 100:
            w, h = 0.1, 0.15
            mat_name = "брус 100x150мм"
        elif 100 < material_width <= 180:
            w, h = 0.15, 0.15
            mat_name = "брус 150x150мм"
        else:
            w, h = 0.2, 0.2
            mat_name = "брус 200x200мм"
    elif foundation_type == "Монолитная плита":
        # Подкладочная доска
        if material_width <= 100:
            w, h = 0.1, 0.05
            mat_name = "50x100мм"
        elif 100 < material_width <= 180:
            w, h = 0.05, 0.15
            mat_name = "50x150мм"
        else:
            w, h = 0.05, 0.2
            mat_name = "50x200мм"
    else:
        # неизвестный фундамент
        return {"volume": 0, "material": "неизвестно"}

    # Расчёт объёма: длина всех стен * ширина * высота
    volume = wall_length1 * w * h

    return {"volume": round(volume, 2), "material": mat_name}


# Расчёт балок пола
async def floor_beams_volume(state: FSMContext) -> dict:
    data = await state.get_data()

    foundation_type = data.get("foundation_type", "")
    if foundation_type not in ["Свайный", "Ленточный"]:
        # Балки пола не нужны для монолитной плиты или неизвестного фундамента
        return {"volume": 0, "material": ""}

    # Размеры сруба и террасы (мм)
    width = int(data.get("width", 0))
    length = int(data.get("length", 0))
    terrace_width = int(data.get("terrace_width", 0))
    terrace_length = int(data.get("terrace_length", 0))

    # Ширина материала сруба (мм)
    house_material = data.get("house_material", "")
    if house_material == "Оцилиндрованное бревно":
        material_width = int(data.get("log_diametr", 0))
    elif house_material == "Профилированный, клееный брус":
        material_width = int(data.get("profiled_timber_width", 0))
    else:  # строганный брус
        material_width = int(data.get("planed_timber_width", 0))

    # Определяем высоту балки
    if material_width <= 180:
        beam_height_mm = 150
    else:
        beam_height_mm = 200
    beam_width_mm = 100  # фиксированная ширина балки

    step_mm = 690  # шаг между балками

    # === Балки на сруб ===
    num_beams_main = math.ceil(width / step_mm) + 1 
    total_length_main = num_beams_main * length
    volume_main_m3 = (total_length_main / 1000) * (beam_width_mm / 1000) * (beam_height_mm / 1000)

    # === Балки на террасу ===
    if terrace_width > 0 and terrace_length > 0:
        num_beams_terrace = math.ceil(terrace_width / step_mm) + 1 
        total_length_terrace = num_beams_terrace * terrace_length
        volume_terrace_m3 = (total_length_terrace / 1000) * (beam_width_mm / 1000) * (beam_height_mm / 1000)
    else:
        volume_terrace_m3 = 0

    # Общий объём
    total_volume_m3 = volume_main_m3 + volume_terrace_m3

    material_label = f"брус {beam_width_mm}x{beam_height_mm} мм"

    return {"volume": round(total_volume_m3, 2), "material": material_label}


# Расчёт балок перекрытия между 1м и 2 этажом
async def ceiling_beams_volume(state: FSMContext) -> dict:
    data = await state.get_data()
    
    # Проверяем наличие второго этажа
    second_floor_exists = data.get("second_floor_exists", "Второго этажа нет")
    balkony_exists = data.get("balkony_exists", "Балкона нет")
    
    # Размеры сруба и террасы
    width = int(data.get("width", 0))
    length = int(data.get("length", 0))
    terrace_width = int(data.get("terrace_width", 0))
    terrace_length = int(data.get("terrace_length", 0))
    
    if second_floor_exists != "Второго этажа нет":
        # Брус 100мм шириной
        beam_width_mm = 100
        step_mm = 690
    else:
        # Доска 50мм шириной
        beam_width_mm = 50
        step_mm = 640
    
    # Высота балки фиксируем в зависимости от ширины материала
    house_material = data.get("house_material")
    if house_material == "Оцилиндрованное бревно":
        material_width = int(data.get("log_diametr", 0))
    elif house_material == "Профилированный, клееный брус":
        material_width = int(data.get("profiled_timber_width", 0))
    else:  # строганный брус
        material_width = int(data.get("planed_timber_width", 0))
    
    if material_width <= 180:
        beam_height_mm = 150
    else:
        beam_height_mm = 200
    
    # === Балки над срубом ===
    num_beams_srub = math.ceil(width / step_mm) + 1 
    total_length_srub_mm = num_beams_srub * length
    volume_srub_m3 = total_length_srub_mm / 1000 * beam_width_mm / 1000 * beam_height_mm / 1000

    # === Балки над террасой ===
    volume_terrace_m3 = 0
    if balkony_exists == "Балкон есть":
        num_beams_terrace = math.ceil(terrace_width / step_mm) + 1
        total_length_terrace_mm = num_beams_terrace * terrace_length
        volume_terrace_m3 = total_length_terrace_mm / 1000 * beam_width_mm / 1000 * beam_height_mm / 1000

    total_volume = volume_srub_m3 + volume_terrace_m3
    
    material_label = f"брус {beam_width_mm}x{beam_height_mm} мм" if second_floor_exists != "Второго этажа нет" else f"доска {beam_width_mm}x{beam_height_mm} мм"
    
    return {"volume": round(total_volume, 2), "material": material_label}


# Расчёт балок перекрытия между 2м этажом и чердаком
async def ceiling2_beams_volume(state: FSMContext) -> dict:
    data = await state.get_data()

    # Проверяем наличие полноценного второго этажа
    second_floor_exists = data.get("second_floor_exists", "Второго этажа нет")
    balcony_exists = data.get("balkony_exists", "Балкона нет")

    if second_floor_exists != "Полноценный второй этаж":
        # Если второго этажа нет, балки не считаем
        return {"volume": 0, "material": ""}

    # Размеры сруба и балкона
    width = int(data.get("width", 0))
    length = int(data.get("length", 0))
    terrace_width = int(data.get("terrace_width", 0))
    terrace_length = int(data.get("terrace_length", 0))

    # Параметры балок
    beam_width_mm = 50
    step_mm = 640

    # Высота балки по ширине материала сруба
    house_material = data.get("house_material")
    if house_material == "Оцилиндрованное бревно":
        material_width = int(data.get("log_diametr", 0))
    elif house_material == "Профилированный, клееный брус":
        material_width = int(data.get("profiled_timber_width", 0))
    else:  # строганный брус
        material_width = int(data.get("planed_timber_width", 0))

    beam_height_mm = 150 if material_width <= 180 else 200

    # === Балки над срубом ===
    num_beams_srub = math.ceil(width / step_mm) + 1
    total_length_srub_mm = num_beams_srub * length
    volume_srub_m3 = total_length_srub_mm / 1000 * beam_width_mm / 1000 * beam_height_mm / 1000

    # === Балки над балконом ===
    volume_balcony_m3 = 0
    if second_floor_exists == "Полноценный второй этаж" and balcony_exists == "Балкон есть":
        num_beams_balcony = math.ceil(terrace_width / step_mm) + 1
        total_length_balcony_mm = num_beams_balcony * terrace_length
        volume_balcony_m3 = total_length_balcony_mm / 1000 * beam_width_mm / 1000 * beam_height_mm / 1000

    total_volume = volume_srub_m3 + volume_balcony_m3
    material_label = f"доска {beam_width_mm}x{beam_height_mm} мм"

    return {"volume": round(total_volume, 2), "material": material_label}


# Расчёт объёма стропил и контробрешётки
async def rafters_volume(state: FSMContext) -> dict:
    data = await state.get_data()

    # Берём площадь кровли
    roof_area = data.get("roof_area")
    rafters_area = roof_area * 0.09
    rafters_volume_m3 = rafters_area * 0.2

    # === Контробрешётка ===
    counter_batten_volume_m3 = rafters_volume_m3 / 4

    return {
        "rafters_volume": round(rafters_volume_m3, 2),
        "rafters_material": "доска 50x200 мм",
        "counter_batten_volume": round(counter_batten_volume_m3, 2),
        "counter_batten_material": "брусок 50x50 мм"
    }


#---------------------------------------------------
# Расчёт объёма обрешётки
#---------------------------------------------------
async def battens_volume(state: FSMContext) -> dict:
    data = await state.get_data()

    roof_area_val = data.get("roof_area", 0)
    battens_area = roof_area_val * 0.33  # 33% от площади кровли
    board_thickness_m = 0.025  # м
    battens_volume_m3 = battens_area * board_thickness_m

    return {
        "battens_volume": round(battens_volume_m3, 2),
        "battens_material": "доска 25x100 мм"
    }


#---------------------------------------------------
# Расчёт площади пола
#---------------------------------------------------

async def calculate_floor_areas(state: FSMContext) -> tuple[float, float]:
    data = await state.get_data()

    # ===== Определяем толщину материала сруба =====
    log_thickness = data.get("log_diametr") or data.get("profiled_timber_width") or data.get("planed_timber_width") or 0
    log_thickness_m = log_thickness / 1000  # переводим в метры

    # ===== Внутренние размеры дома =====
    width = (data.get("width") or 0) / 1000
    length = (data.get("length") or 0) / 1000
    inner_width = max(width - log_thickness_m, 0)
    inner_length = max(length - log_thickness_m, 0)
    house_floor_area = inner_width * inner_length

    # ===== Проверка второго этажа =====
    second_floor_exists = data.get("second_floor_exists")
    if second_floor_exists and second_floor_exists != "Второго этажа нет":
        house_floor_area *= 2  # площадь внутреннего пола дома

    interior_floor_area = house_floor_area

    # ===== Площадь террасы =====
    exterior_floor_area = 0
    terrace_exists = data.get("terrace_exists")
    if terrace_exists and terrace_exists != "Террасы нет":
        terrace_width = (data.get("terrace_width") or 0) / 1000
        terrace_length = (data.get("terrace_length") or 0) / 1000
        inner_terrace_width = max(terrace_width - log_thickness_m, 0)
        inner_terrace_length = max(terrace_length - log_thickness_m, 0)
        terrace_area = inner_terrace_width * inner_terrace_length

        # Проверка балкона
        balcony_exists = data.get("balcony_exists")
        if balcony_exists and balcony_exists != "Балкона нет":
            terrace_area *= 2

        exterior_floor_area = terrace_area

    return round(interior_floor_area, 2), round(exterior_floor_area, 2)
