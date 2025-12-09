from typing import Any
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram import F

import app.keyboards as kb
from app.calc import calculation as calc
from app.calc import extracalc as extracalc
from app.calc.foundationcalc import calculate_total_piles, calculate_strip_foundation_area, calculate_slab_foundation_area


#---------------------------------------------------
# Вывод всех введённых параметров сруба
#---------------------------------------------------
async def output_of_values(message: Message, state: FSMContext) -> None:
    
    data: dict = await state.get_data()

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
        ("roof_overhangs", "Длина свесов, мм")
    ]

    def pretty(value: Any) -> str:
        if value is None or value == "":
            return None
        if isinstance(value, bool):
            return "Да" if value else "Нет"
        return str(value)

    lines = []
    for key, label in fields:
        value = pretty(data.get(key))
        if value is not None:
            lines.append(f"{label}: <b>{value}</b>")

    if lines:
        text = "<b>Введённые значения:</b>\n\n" + "\n".join(lines)
        await message.answer(text, parse_mode="HTML", reply_markup=kb.calculation_or_back_kb)
    else:
        await message.answer("Нет введённых данных.", reply_markup=kb.calculation_or_back_kb)


#---------------------------------------------------
# Функция финальных расчётов и вывода их на печать
#---------------------------------------------------

async def print_final_calc(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()

    # ===== Расчёты стен и фронтонов =====
    width_with_vypuski, length_with_vypuski = await calc.add_vypuski_to_width_length(state)
    koef1, koef2 = await calc.calculate_room_coefs(state)
    terrace_koef = await calc.terrace_coef(state)
    terrace_wall_area, terrace_wall_volume = await calc.calculate_terrace_wall_area(state, terrace_koef), 2
    first_floor_area, first_floor_volume = await calc.calculate_first_floor_wall_volume(
        state,
        length_with_vypuski,
        width_with_vypuski,
        terrace_wall_area,
        koef1
    )

    konek_height = await calc.calculate_konek_height(state)
    fronton_num = await calc.calculate_fronton_num(state)
    fronton_volume = await calc.calculate_fronton_volume(state, width_with_vypuski, konek_height, fronton_num)

    if data.get('second_floor_exists') is None or data.get('second_floor_exists') == "Второго этажа нет":
        wall_volume2 = 0
    else:
        balkony_wall_area = await calc.calculate_balkon_wall_area(state, terrace_wall_area)
        wall_length2 = await calc.calculate_wall_length2(state, width_with_vypuski, length_with_vypuski, koef2)
        wall_area2_raw = await calc.calculate_wall_area2_raw(state, wall_length2, konek_height)
        doors_area2, win_area2 = await calc.calculate_openings_area2(state)
        wall_area2 = await calc.calculate_wall_area2(wall_area2_raw, balkony_wall_area, doors_area2, win_area2)
        wall_volume2 = await calc.calculate_wall_volume2(state, wall_area2)

    total_volume = await calc.total_volume_calculate(first_floor_volume, wall_volume2, fronton_volume)

    # ===== Дополнительные расчёты =====
    roof_area = await extracalc.roof_area(state)

    oklad_data = await extracalc.oklad_venets_volume(state)
    oklad_volume = oklad_data["volume"]
    oklad_material = oklad_data["material"]

    floor_beams_data = await extracalc.floor_beams_volume(state)
    floor_beams_volume_val = floor_beams_data["volume"]
    floor_beams_material = floor_beams_data["material"]

    ceiling_beams_data = await extracalc.ceiling_beams_volume(state)
    ceiling_beams_volume_val = ceiling_beams_data["volume"]
    ceiling_beams_material = ceiling_beams_data["material"]

    ceiling2_beams_data = await extracalc.ceiling2_beams_volume(state)
    ceiling2_beams_volume_val = ceiling2_beams_data["volume"]
    ceiling2_beams_material = ceiling2_beams_data["material"]

    # ===== СТРОПИЛА + КОНТРОБРЕШЁТКА =====
    rafters_data = await extracalc.rafters_volume(state)
    rafters_volume_val = rafters_data["rafters_volume"]
    rafters_material = rafters_data["rafters_material"]
    counter_batten_volume_val = rafters_data["counter_batten_volume"]
    counter_batten_material = rafters_data["counter_batten_material"]

    # ===== ОБРЕШЁТКА =====
    battens_data = await extracalc.battens_volume(state)
    battens_volume_val = battens_data["battens_volume"]
    battens_material = battens_data["battens_material"]

    # ===== Площадь пола =====
    interior_floor_area, exterior_floor_area = await extracalc.calculate_floor_areas(state)

    foundation_type = data.get("foundation_type", "")

    # ===== Подпись окладного венца =====
    if foundation_type in ["Свайный", "Ленточный"]:
        oklad_label = f"Окладной венец, {oklad_material}"
    elif foundation_type == "Монолитная плита":
        oklad_label = f"Подкладочная доска, {oklad_material}"
    else:
        oklad_label = f"Объём материала, {oklad_material}"

    # ===== Фундамент =====
    if foundation_type == "Свайный":
        foundation_val = await calculate_total_piles(state)
        foundation_text = f"Количество свай: <b>{foundation_val}</b>"
    elif foundation_type == "Ленточный":
        foundation_val = await calculate_strip_foundation_area(state)
        foundation_text = f"Площадь поверхности ленточного фундамента: <b>{foundation_val} м²</b>"
    elif foundation_type == "Монолитная плита":
        foundation_val = await calculate_slab_foundation_area(state)
        foundation_text = f"Площадь монолитной плиты: <b>{foundation_val} м²</b>"
    else:
        foundation_text = ""

    # ===== Формируем финальный вывод =====
    message_text = f"""Объём материала на сруб: <b>{total_volume}</b> м³

Площадь внутреннего пола: <b>{interior_floor_area}</b> м²"""

    # Площадь наружного пола только если > 0
    if exterior_floor_area > 0:
        message_text += f"\n\nПлощадь наружного пола: <b>{exterior_floor_area}</b> м²"

    message_text += f"""

Площадь кровли: <b>{roof_area}</b> м²

{oklad_label}: <b>{oklad_volume}</b> м³"""

    if floor_beams_volume_val > 0:
        message_text += f"\n\nБалки пола, {floor_beams_material}: <b>{floor_beams_volume_val}</b> м³"
    if ceiling_beams_volume_val > 0:
        message_text += f"\n\nБалки перекрытия 1 этажа,\n{ceiling_beams_material}: <b>{ceiling_beams_volume_val}</b> м³"
    if ceiling2_beams_volume_val > 0:
        message_text += f"\n\nБалки перекрытия 2 этажа,\n{ceiling2_beams_material}: <b>{ceiling2_beams_volume_val}</b> м³"

    message_text += f"""

Стропила, {rafters_material}: <b>{rafters_volume_val}</b> м³

Контробрешётка, {counter_batten_material}: <b>{counter_batten_volume_val}</b> м³

Обрешётка, {battens_material}: <b>{battens_volume_val}</b> м³"""

    if foundation_text:
        message_text += f"\n\n{foundation_text}"

    message_text += """\n
Значения рассчитаны с учётом усреднённых коэффициентов. 

Для точного расчёта необходимо сделать проект. 

Обратитесь к <a href="https://t.me/AndreyCDO">проектировщику срубов</a>"""

    await callback.message.answer(message_text, parse_mode="HTML", reply_markup=kb.finalbutton_kb)
