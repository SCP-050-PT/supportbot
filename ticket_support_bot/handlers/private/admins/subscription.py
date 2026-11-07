from . import *

# __router__ !DO NOT DELETE!
subs_router = Router()


# __states__ !DO NOT DELETE!
class ChangeChannelInfoStates(StatesGroup):
    get_url = State()
    get_id = State()


class ChangeButtonNameStates(StatesGroup):
    get_button_name = State()


# __buttons__ !DO NOT DELETE!
async def get_sub_menu_inline_keyboard(is_on: bool) -> InlineKeyboardMarkup:
    button_list = [
        [InlineKeyboardButton(text='Изменить данные канала 🔄', callback_data='channel_change_btn')],
        [InlineKeyboardButton(text='Изменить название кнопки пользователей 🖲️', callback_data='chnl_cng_btn_name_btn')]
    ]

    if not is_on:
        button_list.append(
            [InlineKeyboardButton(text='Сделать подписку обязательной 🔔', callback_data='channel_turn_btn on')],
        )
    else:
        button_list.append(
            [InlineKeyboardButton(text='Сделать подписку необязательной 🔕', callback_data='channel_turn_btn off')],
        )

    button_list.append([InlineKeyboardButton(text='Убрать меню 🚫', callback_data='delete_btn')])

    @subs_router.callback_query(F.data.startswith('channel_change_btn'))
    async def handle_change_button_callback(callback: CallbackQuery, state: FSMContext):
        bot_logger.info(f'Handling sub_menu change button callback from user {callback.message.chat.id}')
        from . import get_decline_reply_keyboard
        await callback.message.answer(text=strs.admin_channel_ask_channel_url,
                                      reply_markup=await get_decline_reply_keyboard())
        await state.set_state(ChangeChannelInfoStates.get_url.state)
        await callback.answer()

    @subs_router.callback_query(F.data.startswith('chnl_cng_btn_name_btn'))
    async def handle_change_channel_button_name_button_callback(callback: CallbackQuery, state: FSMContext):
        bot_logger.info(f'Handling sub_menu change channel button name callback from user {callback.message.chat.id}')
        from . import get_decline_reply_keyboard
        await callback.message.answer(
            text=strs.admin_channel_ask_button_name,
            reply_markup=await get_decline_reply_keyboard()
        )
        await state.set_state(ChangeButtonNameStates.get_button_name.state)
        await callback.answer()

    @subs_router.callback_query(F.data.startswith('channel_turn_btn'))
    async def handle_turn_button_callback(callback: CallbackQuery, state: FSMContext):
        bot_logger.info(f'Handling sub_menu turn_btn button callback from user {callback.message.chat.id}')
        data = callback.data.split()
        action = data[1]
        is_on = True if action == 'on' else False

        await db.preferences.update(
            key='channel_info',
            new_data={
                'is_on': is_on
            }
        )

        channel_info = await db.preferences.get_by_key('channel_info')
        id_, url = channel_info.get('id'), channel_info.get('url')
        button_name = channel_info.get('button_name')
        await callback.message.edit_text(
            text=strs.admin_channel_channel_info(id_=id_, url=url, button_name=button_name),
            reply_markup=await get_sub_menu_inline_keyboard(
                is_on=is_on
            )
        )

        text = strs.admin_channel_on if is_on else strs.admin_channel_off
        await callback.answer(text=text, show_alert=True)

    return InlineKeyboardMarkup(inline_keyboard=button_list)


# __chat__ !DO NOT DELETE!
@general_router.message(
    filters.Private(), filters.IsAdmin(),
    ((F.text == '/change_channel') | (F.text == 'Изменить канал подписки 🌐'))
)
async def handle_change_channel_command(message: Message, state: FSMContext):
    bot_logger.info(f'Handling command /change_channel from user {message.chat.id}')
    channel_info = await db.preferences.get_by_key('channel_info')
    id_, url = channel_info.get('id'), channel_info.get('url')
    is_on = channel_info.get('is_on', True)
    button_name = channel_info.get('button_name')
    await message.answer(
        text=strs.admin_channel_channel_info(id_=id_, url=url, button_name=button_name),
        reply_markup=await get_sub_menu_inline_keyboard(
            is_on=is_on
        )
    )


@general_router.message(ChangeChannelInfoStates.get_url)
async def handle_get_channel_state(message: Message, state: FSMContext):
    bot_logger.info(f'Handling states ChangeChannelInfo.get_channel from user {message.chat.id}')
    url = message.text
    if url:
        entities = message.entities
        if entities:
            for entity in message.entities:
                if (entity.type == 'url' or entity.type == 'text_link') and len(url.strip().split(' ')) == 1:
                    await message.answer(text=strs.admin_channel_ask_channel_id)
                    await state.update_data({'url': message.text})
                    await state.set_state(ChangeChannelInfoStates.get_id.state)
                    return
    await message.answer(text=strs.admin_channel_ask_channel_url_error)


@general_router.message(ChangeChannelInfoStates.get_id)
async def handle_get_channel_state(message: Message, state: FSMContext):
    bot_logger.info(f'Handling states ChangeChannelInfo.get_channel from user {message.chat.id}')
    from_chat = message.forward_from_chat or message.forward_from
    if from_chat:
        channel_id = from_chat.id
        data = await state.get_data()
        url = data['url']

        await db.preferences.update(
            key='channel_info',
            new_data={
                'id': channel_id,
                'url': url
            }
        )

        channel_info = await db.preferences.get_by_key('channel_info')
        id_, url = channel_info.get('id'), channel_info.get('url')
        is_on = channel_info.get('is_on', True)
        button_name = channel_info.get('button_name')
        await message.answer(
            text=strs.admin_channel_channel_info(id_=id_, url=url, button_name=button_name),
            reply_markup=await get_sub_menu_inline_keyboard(
                is_on=is_on
            )
        )

        users = await db.users.get_all()
        if users:
            for user in users:
                user_id = user.get('user_id')
                if user_id != message.chat.id:
                    await message.bot.send_message(
                        chat_id=user_id,
                        text=strs.admin_channel_channel_updated_info(url=url)
                    )

        await state.clear()
    else:
        await message.answer(text=strs.admin_channel_ask_channel_id_error)


@general_router.message(ChangeButtonNameStates.get_button_name)
async def handle_get_channel_state(message: Message, state: FSMContext):
    bot_logger.info(f'Handling states ChangeChannelInfo.get_channel from user {message.chat.id}')
    button_name = message.text
    if button_name:
        await db.preferences.update(
            key='channel_info',
            new_data={
                'button_name': button_name
            }
        )
        channel_info = await db.preferences.get_by_key('channel_info')
        id_, url = channel_info.get('id'), channel_info.get('url')
        is_on = channel_info.get('is_on', True)
        button_name = channel_info.get('button_name')
        await message.answer(
            text=strs.admin_channel_channel_info(id_=id_, url=url, button_name=button_name),
            reply_markup=await get_sub_menu_inline_keyboard(
                is_on=is_on
            )
        )
        await state.clear()
    else:
        await message.answer(text=strs.admin_channel_ask_button_name_error)
