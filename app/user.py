
import asyncio
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext

import app.keyboards as kb
from app.states import Steps
from app.calc.finalcalc import output_of_values, print_final_calc

from app.messeges import startmessage, widthmes, roomsmes

user = Router()

#------------------------------------------------------------------------------------------------------------------------------------------------------
# В этом роутере собираем все данные по срубу - размеры, высоты, терраса, балкон, количество помещений, размеры окон, кровля, фундамент, материал сруба
#------------------------------------------------------------------------------------------------------------------------------------------------------

# Команда /start
@user.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext, bot: Bot):
    await message.answer(startmessage, reply_markup=kb.startbutton)
    

# Стартовое сообщение и вывод кнопки "Далее", запрос ширины сруба   
@user.callback_query(F.data == "startbutton")
async def step_width(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await state.set_state(Steps.width)
    await callback.answer()
    await callback.message.answer(widthmes)
    
 
# Запись ширины сруба и запрос длины сруба   
@user.message(Steps.width)
async def step_length(message: Message, state: FSMContext):
    try:
        width = int(message.text)
    except ValueError:
        await message.answer('Введите число в миллиметрах:')
        return
    
    if 600 <= width <= 50000:
        await state.update_data(width = width)
        await state.set_state(Steps.length)
        await message.answer('Длина сруба в мм:')
    else:
        await message.answer('Введите корректное значение от 600 до 50.000 мм:')
    

# Запись длины сруба и запрос наличия террасы
@user.message(Steps.length)
async def step_length(message: Message, state: FSMContext):
    try:
        length = int(message.text)
    except ValueError:
        await message.answer('Введите число в миллиметрах:')
        return
    
    if 600 <= length <= 50000:
        await state.update_data(length = length)
        await state.set_state(Steps.terrace_exists)
        await message.answer('Нужна ли терраса?', reply_markup=kb.terrace_exists_kb)
    else:
        await message.answer('Введите корректное значение от 600 до 50.000 мм:')
        

# Запись наличия террасы и запрос глубины террасы, если таковая есть
@user.callback_query(F.data == 'Терраса есть')
async def step_terrace_is_exists(callback: CallbackQuery, state: FSMContext):
    await state.update_data(terrace_exists = callback.data)
    await state.set_state(Steps.terrace_width)
    
    await callback.message.answer('Глубина террасы в мм:')
    await callback.answer()
    

# Запись глубины террасы и запрос длины террасы    
@user.message(Steps.terrace_width)
async def step_terrace_width(message: Message, state: FSMContext):
    try:
        terrace_width = int(message.text)
    except ValueError:
        await message.answer('Введите число в миллиметрах:')
        return
    
    if 600 <= terrace_width <= 50000:
        await state.update_data(terrace_width = terrace_width)
        await state.set_state(Steps.terrace_length)
        await message.answer('Длина террасы?')
    else:
        await message.answer('Введите корректное значение от 600 до 50.000 мм:')
        

# Запись длины террасы и запрос из какого материала перила террасы        
@user.message(Steps.terrace_length)
async def step_terrace_length(message: Message, state: FSMContext):
    try:
        terrace_length = int(message.text)
    except ValueError:
        await message.answer('Введите число в миллиметрах:')
        return
    
    if 600 <= terrace_length <= 50000:
        await state.update_data(terrace_length = terrace_length)
        await state.set_state(Steps.terrace_railings)
        await message.answer('У террасы перила будут из того же материала что и сруб?', reply_markup=kb.terrace_railings_kb)
    else:
        await message.answer('Введите корректное значение от 600 до 50.000 мм:')
        

# Запись материала перил террасы и запрос количества помещений 1го этажа. Этот же хендлер вызывается, если террасы вообще нет.        
@user.callback_query(F.data.in_({'Перила из материала сруба',
                                'Перил террасы нет',
                                'Террасы нет'
    }))
async def step_terrace_railings_is_exist(callback: CallbackQuery, state: FSMContext):
    await state.update_data(terrace_railings = callback.data)
    await state.set_state(Steps.first_floor_rooms)
    
    await callback.message.answer(roomsmes)
    await callback.answer()
        

# Запись колличества помещений 1го этажа и запрос высоты потолков 1го этажа        
@user.message(Steps.first_floor_rooms)
async def step_first_floor_rooms(message: Message, state: FSMContext):
    try:
        first_floor_rooms = int(message.text)
    except ValueError:
        await message.answer('Введите число от 1 до 10:')
        return
    
    if 1 <= first_floor_rooms <= 10:
        await state.update_data(first_floor_rooms = first_floor_rooms)
        await state.set_state(Steps.first_floor_height)
        await message.answer('Высота потолков 1го этажа в мм?')
    else:
        await message.answer('Введите корректное значение от 1 до 10:')


# Запись высоты потолков 1го этажа и запрос размеров окон 1го этажа        
@user.message(Steps.first_floor_height)
async def step_first_floor_height(message: Message, state: FSMContext):
    try:
        first_floor_height = int(message.text)
    except ValueError:
        await message.answer('Введите число от 2000 до 5000:')
        return
    
    if 2000 <= first_floor_height <= 5000:
        await state.update_data(first_floor_height = first_floor_height)
        await state.set_state(Steps.first_floor_windows)
        await message.answer('Какие будут окна на 1м этаже?', reply_markup=kb.first_floor_windows_kb)
    else:
        await message.answer('Введите корректное значение от 2000 до 5000:')


# Запись размера окон 1го этажа и запрос наличия второго этажа        
@user.callback_query(F.data.in_({'Окна 1го этажа большие, в пол',
                                'Окна 1го этажа большие, широкие',
                                'Окна 1го этажа стандартные'
    }))
async def step_first_floor_windows(callback: CallbackQuery, state: FSMContext):
    await state.update_data(first_floor_windows = callback.data)
    
    await callback.message.answer('Будет ли второй этаж?', reply_markup=kb.second_floor_exists_kb)
    await callback.answer()        
    
    
# Запись наличия второго этажа (если он мансардный) и запрос высоты аттиковой стены       
@user.callback_query(F.data == 'Второй этаж мансардного типа')
async def step_second_floor_exists(callback: CallbackQuery, state: FSMContext):
    await state.update_data(second_floor_exists = callback.data)
    await state.set_state(Steps.second_floor_height)
    
    await callback.message.answer('Высота аттиковой стены (высота от пола до начала ската крыши)?')
    await callback.answer()        
    
    
# Запись наличия второго этажа (если он полноценный) и запрос высоты второго этажа       
@user.callback_query(F.data == 'Полноценный второй этаж')
async def step_second_floor_exists(callback: CallbackQuery, state: FSMContext):
    await state.update_data(second_floor_exists = callback.data)
    await state.set_state(Steps.second_floor_height)
    
    await callback.message.answer('Высота потолков 2го этажа?')
    await callback.answer() 


# Запись высоты 2го этажа и запрос количества помещений 2го этажа 
@user.message(Steps.second_floor_height)
async def second_floor_height(message: Message, state: FSMContext):
    data = await state.get_data()
    second_floor_exist = data.get("second_floor_exists")

    # Мансардный этаж
    if second_floor_exist == 'Второй этаж мансардного типа':
        try:
            height = int(message.text)
        except ValueError:
            await message.answer("Введите число в миллиметрах:")
            return

        if 0 <= height <= 2500:
            await state.update_data(second_floor_attic_height=height)
            await state.set_state(Steps.second_floor_rooms)
            await message.answer("Количество раздельных помещений на 2м этаже?")
        else:
            await message.answer("Введите корректное значение от 0 до 2500 мм:")
    
    # Полноценный этаж
    elif second_floor_exist == 'Полноценный второй этаж':
        try:
            height = int(message.text)
        except ValueError:
            await message.answer("Введите число в миллиметрах:")
            return

        if 2100 <= height <= 5000:
            await state.update_data(second_floor_full_height=height)
            await state.set_state(Steps.second_floor_rooms)
            await message.answer("Количество раздельных помещений на 2м этаже?")
        else:
            await message.answer("Введите корректное значение от 2100 до 5000 мм:")

            
            
# Запись колличества помещений 2го этажа и запрос размеров окон 2го этажа        
@user.message(Steps.second_floor_rooms)
async def step_second_floor_rooms(message: Message, state: FSMContext):
    try:
        second_floor_rooms = int(message.text)
    except ValueError:
        await message.answer('Введите число от 1 до 10:')
        return
    
    if 1 <= second_floor_rooms <= 10:
        await state.update_data(second_floor_rooms = second_floor_rooms)
        await state.set_state(Steps.second_floor_windows)
        await message.answer('Какие окна будут на 2м этаже?', reply_markup=kb.second_floor_windows_kb)
    else:
        await message.answer('Введите корректное значение от 1 до 10:')
        
        
# Запись размера окон 2го этажа и запрос наличия балкона во всю ширину террасы        
@user.callback_query(F.data.in_({'Окна 2го этажа большие, в пол',
                                'Окна 2го этажа большие, широкие',
                                'Окна 2го этажа стандартные'
    }))
async def step_second_floor_windows(callback: CallbackQuery, state: FSMContext):
    await state.update_data(second_floor_windows = callback.data)
    
    await callback.message.answer('Будет ли балкон на втором этаже по размеру террасы?', reply_markup=kb.balcony_exists_kb)
    await callback.answer()  
    
    
# Запись наличия балкона и запрос типа кровли. В этот же хэндлер переходим, если второго этажа вообще нет.        
@user.callback_query(F.data.in_({'Балкон есть',
                                'Балкона нет',
                                'Второго этажа нет'
    }))
async def step_balcony_exists(callback: CallbackQuery, state: FSMContext):
    await state.update_data(balcony_exists = callback.data)
    
    await callback.message.answer('Тип кровли?', reply_markup=kb.roof_type_kb)
    await callback.answer()  
    
    
# Запись типа кровли и запрос угла ската кровли        
@user.callback_query(F.data.in_({'Односкатная',
                                'Двускатная',
                                'Вальмовая'
    }))
async def step_roof_type(callback: CallbackQuery, state: FSMContext):
    await state.update_data(roof_type = callback.data)
    
    await callback.message.answer('Примерный угол ската кровли от 1 до 60 градусов?')
    await state.set_state(Steps.roof_angle)
    await callback.answer()


# Запись угла кровли и запрос длины свесов кровли    
@user.message(Steps.roof_angle)
async def step_roof_angle(message: Message, state: FSMContext):
    try:
        roof_angle = int(message.text)
    except ValueError:
        await message.answer('Введите число от 1 до 60:')
        return
    
    if 1 <= roof_angle <= 60:
        await state.update_data(roof_angle=roof_angle)

        await state.set_state(Steps.roof_overhangs)
        await message.answer('Введите длину свесов кровли от 0 до 1500мм:')
    else:
        await message.answer('Введите корректное значение от 1 до 60:')
        
        
# Запись свесов кровли и запрос типа фронтонов (если второй этаж мансардный — сразу фундамент)
@user.message(Steps.roof_overhangs)
async def step_roof_overhangs(message: Message, state: FSMContext):
    try:
        overhangs = int(message.text)
    except ValueError:
        await message.answer("Введите длину свесов в миллиметрах числом:")
        return

    # Проверка корректного диапазона
    if not (0 <= overhangs <= 1500):
        await message.answer("Длина свесов должна быть от 0 до 1500мм:")
        return

    await state.update_data(roof_overhangs=overhangs)

    # Получаем данные о втором этаже и типе кровли
    data = await state.get_data()
    second_floor = data.get("second_floor_exists")
    roof_type = data.get("roof_type")

    # Если мансарда или вальмовая кровля → сразу к фундаменту
    if second_floor == "Второй этаж мансардного типа" or roof_type == "Вальмовая":
        await state.set_state(Steps.foundation_type)
        await message.answer("Какой планируется фундамент?", reply_markup=kb.foundation_type_kb)
        return

    # Иначе спрашиваем фронтоны
    await message.answer(
        "Фронтоны будут из того же материала, что и сруб?",
        reply_markup=kb.fronton_type_kb
    )
    await state.set_state(Steps.fronton_type)
        
        
# Запись типа фронтонов и запрос типа фундамента        
@user.callback_query(F.data.in_({
    'Фронтоны полноценные',
    'Фронтоны зашиваются доской'
}))
async def step_fronton_type(callback: CallbackQuery, state: FSMContext):
    await state.update_data(fronton_type=callback.data)

    await state.set_state(Steps.foundation_type)
    await callback.message.answer(
        'Какой планируется фундамент?', 
        reply_markup=kb.foundation_type_kb
    )

    await callback.answer()
    

# Запись типа фундамента и запрос материала сруба        
@user.callback_query(F.data.in_({'Свайный',
                                'Ленточный',
                                'Монолитная плита'
    }))
async def step_foundation_type(callback: CallbackQuery, state: FSMContext):
    await state.update_data(foundation_type = callback.data)
    
    await callback.message.answer('Материал сруба?', reply_markup=kb.house_material_kb)
    await callback.answer()
    

#----------------------------------------------------------------------------------
# Если ОЦИЛИНДРОВАННОЕ БРЕВНО :Запись типа материала сруба и запрос диаметра бревна      
@user.callback_query(F.data == 'Оцилиндрованное бревно')
async def step_house_material_rounded_log(callback: CallbackQuery, state: FSMContext):
    await state.update_data(house_material = callback.data)
    
    await callback.message.answer('Диаметр бревна?')
    await state.set_state(Steps.log_diametr)
    await callback.answer()
    
    
# Запись диаметра бревна переход к выводу параметров сруба   
@user.message(Steps.log_diametr)
async def step_log_diametr(message: Message, state: FSMContext):
    try:
        log_diametr = int(message.text)
    except ValueError:
        await message.answer('Введите число в миллиметрах:')
        return
    
    if 100 <= log_diametr <= 1000:
        await state.update_data(log_diametr = log_diametr)
        await state.set_state(Steps.output_of_values)
        await output_of_values(message, state)
    else:
        await message.answer('Введите корректное значение от 100 до 1000 мм:')


#----------------------------------------------------------------------------------
# Если ПРОФИЛИРОВАННЫЙ КЛЕЕНЫЙ БРУС :Запись типа материала сруба и запрос ширины бруса      
@user.callback_query(F.data == 'Профилированный, клееный брус')
async def step_house_material_profiled_timber(callback: CallbackQuery, state: FSMContext):
    await state.update_data(house_material = callback.data)
    
    await callback.message.answer('Ширина бруса?')
    await state.set_state(Steps.profiled_timber_width)
    await callback.answer()
    
    
# Запись ширины бруса и запрос габаритной высоты бруса   
@user.message(Steps.profiled_timber_width)
async def step_profiled_timber_width(message: Message, state: FSMContext):
    try:
        profiled_timber_width = int(message.text)
    except ValueError:
        await message.answer('Введите число в миллиметрах:')
        return
    
    if 35 <= profiled_timber_width <= 500:
        await state.update_data(profiled_timber_width = profiled_timber_width)
        await state.set_state(Steps.profiled_timber_height)
        await message.answer('Габаритная высота бруса?')
    else:
        await message.answer('Введите корректное значение от 35 до 500 мм:')


# Запись габаритной высоты бруса и запрос рабочей высоты бруса   
@user.message(Steps.profiled_timber_height)
async def step_profiled_timber_height(message: Message, state: FSMContext):
    try:
        profiled_timber_height = int(message.text)
    except ValueError:
        await message.answer('Введите число в миллиметрах:')
        return
    
    if 40 <= profiled_timber_height <= 500:
        await state.update_data(profiled_timber_height = profiled_timber_height)
        await state.set_state(Steps.profiled_timber_row_height)
        await message.answer('Рабочая высота бруса\n(меньше, либо равна габаритной)?')
    else:
        await message.answer('Введите корректное значение от 40 до 500 мм:')
        
        
# Запись рабочей высоты бруса и переход к выводу параметров сруба
@user.message(Steps.profiled_timber_row_height)
async def step_profiled_timber_row_height(message: Message, state: FSMContext):
    try:
        profiled_timber_row_height = int(message.text)
    except ValueError:
        await message.answer('Введите число в миллиметрах:')
        return

    if not (35 <= profiled_timber_row_height <= 500):
        await message.answer('Введите корректное значение от 35 до 500 мм:')
        return

    # Получаем габаритную высоту бруса из state
    data = await state.get_data()
    profiled_timber_height = data.get('profiled_timber_height')

    if profiled_timber_height is not None and profiled_timber_row_height > profiled_timber_height:
        await message.answer(f'Рабочая высота бруса должна быть меньше, либо равна габаритной ({profiled_timber_height} мм).')
        return

    # Сохраняем значение и выводим параметры сруба
    await state.update_data(profiled_timber_row_height=profiled_timber_row_height)
    await state.set_state(Steps.output_of_values)
    await output_of_values(message, state)

        
        
#----------------------------------------------------------------------------------
# Если СТРОГАННЫЙ БРУС :Запись типа материала сруба и запрос ширины бруса      
@user.callback_query(F.data == 'Строганный брус')
async def step_house_material_planed_timber(callback: CallbackQuery, state: FSMContext):
    await state.update_data(house_material = callback.data)
    
    await callback.message.answer('Ширина бруса?')
    await state.set_state(Steps.planed_timber_width)
    await callback.answer()
    
    
# Запись ширины бруса и запрос высоты бруса   
@user.message(Steps.planed_timber_width)
async def step_planed_timber_width(message: Message, state: FSMContext):
    try:
        planed_timber_width = int(message.text)
    except ValueError:
        await message.answer('Введите число в миллиметрах:')
        return
    
    if 35 <= planed_timber_width <= 500:
        await state.update_data(planed_timber_width = planed_timber_width)
        await state.set_state(Steps.planed_timber_height)
        await message.answer('Высота бруса?')
    else:
        await message.answer('Введите корректное значение от 35 до 500 мм:')
        
        
# Запись высоты бруса и переход к выводу параметров сруба   
@user.message(Steps.planed_timber_height)
async def step_planed_timber_height(message: Message, state: FSMContext):
    try:
        planed_timber_height = int(message.text)
    except ValueError:
        await message.answer('Введите число в миллиметрах:')
        return
    
    if 35 <= planed_timber_height <= 500:
        await state.update_data(planed_timber_height = planed_timber_height)
        await state.set_state(Steps.output_of_values)
        await output_of_values(message, state)
    else:
        await message.answer('Введите корректное значение от 35 до 500 мм:')
        
        
# Вывод финальных расчётов
@user.callback_query(F.data == 'calculation_step')
async def final_calc_and_output(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await print_final_calc(callback, state)

    