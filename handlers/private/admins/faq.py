from . import *

# Standard
from uuid import uuid4
from json import loads, dumps
from handlers.utils import CustomJSONEncoder

# __router__ !DO NOT DELETE!
faq_router = Router()


# __states__ !DO NOT DELETE!
class UpdateStates(StatesGroup):
    get_question = State()
    get_content = State()


class FaqStates(StatesGroup):
    get_question = State()
    get_content = State()


# __buttons__ !DO NOT DELETE!
async def get_faq_details_inline_keyboard(question_id: str, is_admin: bool) -> InlineKeyboardMarkup:
    button_list = []
    if is_admin:
        button_list.append(
            [InlineKeyboardButton(text='Обновить вопрос ❓', callback_data=f'update_btn question {question_id}'),
             InlineKeyboardButton(text='Обновить контент 📝', callback_data=f'update_btn content {question_id}')],
        )
        button_list.append(
            [InlineKeyboardButton(text='Удалить 🗑️', callback_data=f'remove_btn {question_id} {int(is_admin)}'),
             InlineKeyboardButton(text='Обновить 🔄', callback_data=f'question_update {question_id} {int(is_admin)}')]
        )
    button_list.append(
        [InlineKeyboardButton(text='Назад 🔙', callback_data=f'back_btn {int(is_admin)}')],
    )

    @faq_router.callback_query(F.data.startswith('question_update'))
    async def handle_question_update_button_callback(callback: CallbackQuery, state: FSMContext):
        bot_logger.info(f'Handling faq_details question update button callback from user {callback.message.chat.id}')
        data = callback.data.split()
        question_id, is_admin = data[1], bool(int(data[2]))

        question = await db.preferences.get_question_by_id(question_id=question_id)
        content = question.get('content', 'Отсутствует')

        await callback.message.delete()
        message = Message(**content)
        await message.send_copy(
            chat_id=callback.message.chat.id,
            reply_markup=await get_faq_details_inline_keyboard(
                question_id=question_id, is_admin=is_admin
            )
        ).as_(callback.bot)

        await callback.answer()

    @faq_router.callback_query(F.data.startswith('update_btn'))
    async def handle_update_button_callback(callback: CallbackQuery, state: FSMContext):
        bot_logger.info(f'Handling faq_details update button callback from user {callback.message.chat.id}')
        data = callback.data.split()
        action, question_id = data[1], data[2]

        await state.update_data({'question_id': question_id})
        if action == 'question':
            await callback.message.answer(text=strs.faq_ask_question)
            await state.set_state(UpdateStates.get_question.state)
        elif action == 'content':
            await callback.message.answer(text=strs.faq_ask_content)
            await state.set_state(UpdateStates.get_content.state)

        await callback.answer()

    @faq_router.callback_query(F.data.startswith('remove_btn'))
    async def handle_remove_button_callback(callback: CallbackQuery, state: FSMContext):
        bot_logger.info(f'Handling faq_details remove button callback from user {callback.message.chat.id}')
        data = callback.data.split()
        question_id, is_admin = data[1], bool(int(data[2]))

        faq = await db.preferences.get_by_key(key='faq')
        questions = faq.get('questions')
        remove_idx = -1
        for idx, question in enumerate(questions):
            if question.get('question_id') == question_id:
                remove_idx = idx
        if remove_idx >= 0:
            del questions[remove_idx]

        await db.preferences.update(
            key='faq',
            new_data={'questions': questions}
        )

        await callback.message.delete()
        await callback.message.answer(
            text=strs.faq_questions,
            reply_markup=await get_faq_menu_inline_keyboard(is_admin=is_admin)
        )
        await callback.answer()

    @faq_router.callback_query(F.data.startswith('back_btn'))
    async def handle_back_button_callback(callback: CallbackQuery, state: FSMContext):
        bot_logger.info(f'Handling faq_details back button callback from user {callback.message.chat.id}')
        data = callback.data.split()
        is_admin = bool(int(data[1]))

        await callback.message.delete()
        await callback.message.answer(
            text=strs.faq_questions,
            reply_markup=await get_faq_menu_inline_keyboard(is_admin=is_admin)
        )
        await callback.answer()

    return InlineKeyboardMarkup(inline_keyboard=button_list)


async def get_faq_menu_inline_keyboard(is_admin: bool = False) -> InlineKeyboardMarkup:
    button_list = []

    faqs = await db.preferences.get_by_key('faq')
    questions = faqs.get('questions')
    if questions:
        for question in questions:
            question_id = question.get('question_id')
            question = question.get('question')
            button_list.append(
                [InlineKeyboardButton(text=question, callback_data=f'faq {question_id} {int(is_admin)}')]
            )

    if is_admin:
        button_list.append(
            [InlineKeyboardButton(text='Добавить ➕', callback_data='add_btn')]
        )

    @faq_router.callback_query(F.data.startswith('faq'))
    async def handle_faq_button_callback(callback: CallbackQuery, state: FSMContext):
        bot_logger.info(f'Handling question faq button callback from user {callback.message.chat.id}')
        data = callback.data.split()
        question_id, is_admin = data[1], bool(int(data[2]))

        question = await db.preferences.get_question_by_id(question_id=question_id)
        content = question.get('content', 'Отсутствует')

        await callback.message.delete()
        message = Message(**content)
        await message.send_copy(
            chat_id=callback.message.chat.id,
            reply_markup=await get_faq_details_inline_keyboard(
                question_id=question_id, is_admin=is_admin
            )
        ).as_(callback.bot)
        await callback.answer()

    @faq_router.callback_query(F.data.startswith('add_btn'))
    async def handle_add_button_callback(callback: CallbackQuery, state: FSMContext):
        bot_logger.info(f'Handling question add button callback from user {callback.message.chat.id}')
        from . import get_decline_reply_keyboard

        await callback.message.answer(text=strs.faq_ask_question, reply_markup=await get_decline_reply_keyboard())

        await state.set_state(FaqStates.get_question.state)
        await callback.answer()

    return InlineKeyboardMarkup(inline_keyboard=button_list)


# __chat__ !DO NOT DELETE!
@general_router.message(
    filters.Private(),
    ((F.text == '/change_faq') | (F.text == 'Изменить FAQ ❓') | (F.text == 'FAQ ❓') | (F.text == '/faq'))
)
async def handle_faq_command(message: Message, state: FSMContext):
    bot_logger.info(f'Handling command /faq from user {message.chat.id}')
    user = await db.users.get_by_id(user_id=message.chat.id)
    status = user.get('status')
    is_admin = status == 'admin'
    await message.answer(text=strs.faq_questions, reply_markup=await get_faq_menu_inline_keyboard(is_admin=is_admin))


@faq_router.message(FaqStates.get_question)
async def handle_get_question_state(message: Message, state: FSMContext):
    bot_logger.info(f'Handling states FaqStates.get_question from user {message.chat.id}')
    question = message.text
    if question:
        await state.update_data({'question': question})
        await message.answer(text=strs.faq_ask_content)
        await state.set_state(FaqStates.get_content.state)
    else:
        await message.answer(text=strs.faq_ask_question_error)


@faq_router.message(FaqStates.get_content)
async def handle_get_content_state(message: Message, state: FSMContext):
    bot_logger.info(f'Handling states FaqStates.get_content from user {message.chat.id}')
    question_id = str(uuid4())[:10]

    message_info = loads(dumps(message.model_dump(), cls=CustomJSONEncoder))
    data = await state.get_data()
    question = data['question']

    faq = await db.preferences.get_by_key('faq')
    questions = faq.get('questions', [])
    questions.append({
        'question_id': question_id,
        'question': question,
        'content': message_info
    })

    await db.preferences.update(
        key='faq',
        new_data={
            'questions': questions
        }
    )

    from .general import get_menu_reply_keyboard

    await message.answer(text=strs.faq_added, reply_markup=await get_menu_reply_keyboard())
    await state.clear()


@faq_router.message(UpdateStates.get_question)
async def handle_get_update_question_state(message: Message, state: FSMContext):
    bot_logger.info(f'Handling states UpdateStates.get_question from user {message.chat.id}')
    data = await state.get_data()
    question_id = data['question_id']

    question = message.text
    if question:
        db_question = await db.preferences.get_question_by_id(question_id=question_id)
        await db.preferences.update_question_by_id(
            question_id=question_id,
            new_data={
                'question_id': question_id,
                'question': question,
                'content': db_question.get('content')
            }
        )

        from .general import get_menu_reply_keyboard
        await message.answer(text=strs.data_update, reply_markup=await get_menu_reply_keyboard())
        await state.clear()
    else:
        await message.answer(text=strs.faq_ask_question_error)


@faq_router.message(UpdateStates.get_content)
async def handle_get_update_content_state(message: Message, state: FSMContext):
    bot_logger.info(f'Handling states UpdateStates.get_content from user {message.chat.id}')
    data = await state.get_data()
    question_id = data['question_id']

    message_info = loads(dumps(message.model_dump(), cls=CustomJSONEncoder))
    db_question = await db.preferences.get_question_by_id(question_id=question_id)
    await db.preferences.update_question_by_id(
        question_id=question_id,
        new_data={
            'question_id': question_id,
            'question': db_question.get('question'),
            'content': message_info
        }
    )

    from .general import get_menu_reply_keyboard
    await message.answer(text=strs.data_update, reply_markup=await get_menu_reply_keyboard())
    await state.clear()
