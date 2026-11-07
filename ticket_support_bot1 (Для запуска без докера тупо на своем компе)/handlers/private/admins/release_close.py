from . import *

# __router__ !DO NOT DELETE!
release_close_router = Router()


# __states__ !DO NOT DELETE!
class ChangeTimeStates(StatesGroup):
    get_time = State()


# __buttons__ !DO NOT DELETE!


# __chat__ !DO NOT DELETE!
@release_close_router.message(
    filters.Private(), filters.IsAdmin(),
    ((F.text == '/change_release_close_time') |
     (F.text == 'Изменить время авто осовобождения/закрытия 🕒'))
)
async def handle_change_release_close_time_command(message: Message, state: FSMContext):
    bot_logger.info(f'Handling command //change_release_close_time from user {message.chat.id}')
    release = await db.preferences.get_by_key('release_hours')
    release_hours = release.get('value')
    close = await db.preferences.get_by_key('close_hours')
    close_hours = close.get('value')

    text = f'<b>Беседа освобождается от менеджера</b>, если последние действие было более {release_hours} ч. назад \n\n'
    text += f'<b>Беседа закрывается</b>, если последние действие было более {close_hours} ч. назад\n\n'

    from . import get_decline_reply_keyboard
    await message.answer(text=text)
    await message.answer(text=strs.admin_release_close_ask_time, reply_markup=await get_decline_reply_keyboard())
    await state.set_state(state=ChangeTimeStates.get_time.state)


@release_close_router.message(ChangeTimeStates.get_time)
async def handle_get_time_state(message: Message, state: FSMContext):
    bot_logger.info(f'Handling states ChangeTimeStates.get_time from user {message.chat.id}')
    import re

    text = message.text
    match = re.match('^(\w+) +(\d+)$', text)
    if text and match:
        action, hours = match.groups()
        action = action.lower()
        if action in ['закрытие', 'освобождение']:
            from .general import get_menu_reply_keyboard

            if action == 'закрытие':
                await db.preferences.update(
                    key='close_hours',
                    new_data={
                        'value': int(hours)
                    }
                )
                await message.answer(text=strs.admin_close_updated, reply_markup=await get_menu_reply_keyboard())
            elif action == 'освобождение':
                await db.preferences.update(
                    key='release_hours',
                    new_data={
                        'value': int(hours)
                    }
                )
                await message.answer(text=strs.admin_release_updated, reply_markup=await get_menu_reply_keyboard())
            await state.clear()
            return

    await message.answer(text=strs.admin_release_close_ask_time_error)