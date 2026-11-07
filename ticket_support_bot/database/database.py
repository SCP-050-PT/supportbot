# Third-party
from datetime import datetime, timezone, timedelta
# Standard
from time import sleep

import motor.motor_asyncio

# Project
import config as cf
from logger import database_logger


# Async MongoDB connection setup
class MongoDatabase:
    def __init__(self):
        while True:
            database_logger.warning('Connecting to database...')
            try:
                uri = f"mongodb://{cf.database['user']}:{cf.database['password']}@" \
                      f"{cf.database['host']}:{cf.database['port']}"
                self.client = motor.motor_asyncio.AsyncIOMotorClient(uri)
                self.db = self.client.get_database(name='local')
                self.users = self.User(collection=self.db.get_collection('users'))
                self.tickets = self.Ticket(collection=self.db.get_collection('tickets'))
                self.preferences = self.Preference(collection=self.db.get_collection('preferences'))

                database_logger.info('Connected to database')
                break
            except Exception as e:
                database_logger.error(e)
                database_logger.warning('Database connection error!')
                sleep(5)

    class User:
        def __init__(self, collection):
            self.collection = collection

        async def insert(self, user_data: dict):
            if 'user_id' in user_data:
                existing_user = await self.collection.find_one({"user_id": int(user_data['user_id'])})
                if not existing_user:
                    await self.collection.insert_one(user_data)
                    database_logger.info('New user inserted in database')
                else:
                    database_logger.info('There is user in database already')
            else:
                database_logger.error('No user_id in user_data provided!')

        async def get_all(self):
            users = [user async for user in self.collection.find()]
            if users:
                database_logger.info('Fetched all users from database')
                return users
            else:
                database_logger.info('There are no users in database')
                return None

        async def get_all_muted(self):
            users = [user async for user in self.collection.find({"mute_time": {"$ne": None}})]
            if users:
                database_logger.info('Fetched all muted users from database')
                return users
            else:
                database_logger.info('There are no muted users in database')
                return None

        async def get_all_managers(self):
            managers = [user async for user in self.collection.find({"status": "manager"})]
            if managers:
                database_logger.info('Fetched all manager users from the database')
                return managers
            else:
                database_logger.info('There are no manager users in the database')
                return None

        async def get_by_id(self, user_id: str | int):
            user_data = await self.collection.find_one({"user_id": int(user_id)})
            if user_data:
                database_logger.info(f'User recording with id {user_id} is retrieved')
                return user_data
            else:
                database_logger.info(f'User recording with id {user_id} is not found')
                return None

        async def get_by_name(self, user_name: str):
            import re
            case_insensitive_pattern = re.compile(f'^{re.escape(user_name)}$', re.IGNORECASE)
            user_data = await self.collection.find_one({"user_name": case_insensitive_pattern})
            if user_data:
                database_logger.info(f'User recording with name {user_name} is retrieved')
                return user_data
            else:
                database_logger.info(f'User recording with name {user_name} is not found')
                return None

        async def get_by_url_name(self, url_name: str):
            import re
            case_insensitive_pattern = re.compile(f'^{re.escape(url_name)}$', re.IGNORECASE)
            user_data = await self.collection.find_one({"url_name": case_insensitive_pattern})
            if user_data:
                database_logger.info(f'User recording with url name {url_name} is retrieved')
                return user_data
            else:
                database_logger.info(f'User recording with url name {url_name} is not found')
                return None

        async def delete_by_id(self, user_id: str | int):
            await self.collection.find_one_and_delete({"user_id": int(user_id)})
            database_logger.info(f'User with id {user_id} is deleted from database')

        async def update(self, user_id: str | int, new_data: dict):
            await self.collection.update_one(
                {"user_id": int(user_id)},
                {"$set": new_data}
            )
            database_logger.info(f'Modified user with id {user_id} is updated')

    class Ticket:
        def __init__(self, collection):
            self.collection = collection

        async def insert(self, ticket_data: dict):
            if 'ticket_id' in ticket_data:
                existing_ticket = await self.collection.find_one({"ticket_id": ticket_data['ticket_id']})
                if not existing_ticket:
                    await self.collection.insert_one(ticket_data)
                    database_logger.info('New ticket inserted in database')
                else:
                    database_logger.info('There is ticket in database already')
            else:
                database_logger.error('No ticket_id in ticket_data provided!')

        async def get_all(self):
            tickets = [ticket async for ticket in self.collection.find()]
            if tickets:
                database_logger.info('Fetched all tickets from database')
                return tickets
            else:
                database_logger.info('There are no tickets in database')
                return None

        async def get_all_opened(self):
            tickets = [ticket async for ticket in self.collection.find(
                {
                    'close_date': None,
                    'manager_id': None,
                }
            )]
            if tickets:
                database_logger.info('Fetched all tickets from database')
                return tickets
            else:
                database_logger.info('There are no tickets in database')
                return None

        async def get_all_by_id(self, user_id: int | str, is_manager: bool):
            if is_manager:
                tickets = [ticket async for ticket in self.collection.find({'manager_id': user_id})]
            else:
                tickets = [ticket async for ticket in self.collection.find({'user_id': int(user_id)})]
            if tickets:
                database_logger.info(f'Fetched all tickets for user_id {user_id} from database')
                return tickets
            else:
                database_logger.info(f'There are no tickets in the database for user_id {user_id}')
                return None

        async def get_by_id(self, ticket_id: str):
            ticket_data = await self.collection.find_one({"ticket_id": ticket_id})
            if ticket_data:
                database_logger.info(f'Ticket recording with id {ticket_id} is retrieved')
                return ticket_data
            else:
                database_logger.info(f'Ticket recording with id {ticket_id} is not found')
                return None

        async def get_tickets_last_modified_ago(self, hours_ago: int):
            tickets = [ticket async for ticket in self.collection.find()]
            if tickets:
                current_time = datetime.now(timezone(timedelta(hours=3)))

                result = []
                for ticket in tickets:
                    last_modified = str(ticket.get('last_modified')).split('.')[0]
                    last_modified_date = datetime.strptime(last_modified, '%Y-%m-%d %H:%M:%S')
                    last_modified_date = last_modified_date.replace(tzinfo=timezone(timedelta(hours=3)))
                    delta = timedelta(hours=hours_ago if hours_ago else 1)
                    if (last_modified_date + delta) <= current_time:
                        is_closed = ticket.get('close_date')
                        if not is_closed or is_closed == 'None':
                            result.append(ticket)

                database_logger.info(f'Fetched all tickets modified before {hours_ago} hours from database')
                return result
            else:
                database_logger.info('There are no tickets modified before the time frame')
                return None

        async def get_tickets_last_modified_month_ago(self, month_ago: int):
            tickets = [ticket async for ticket in self.collection.find()]
            if tickets:
                current_time = datetime.now(timezone(timedelta(hours=3)))

                result = []
                for ticket in tickets:
                    last_modified = str(ticket.get('last_modified')).split('.')[0]
                    last_modified_date = datetime.strptime(last_modified, '%Y-%m-%d %H:%M:%S')
                    last_modified_date = last_modified_date.replace(tzinfo=timezone(timedelta(hours=3)))
                    days = 30 * month_ago
                    delta = timedelta(days=days)
                    if (last_modified_date + delta) <= current_time:
                        result.append(ticket)

                database_logger.info(f'Fetched all tickets modified before {month_ago} months from database')
                return result
            else:
                database_logger.info('There are no tickets modified before the time frame')
                return None

        async def update(self, ticket_id: str, new_data: dict):
            await self.collection.update_one(
                {"ticket_id": ticket_id},
                {"$set": new_data}
            )
            database_logger.info(f'Modified ticket with id {ticket_id} is updated')

        async def delete_by_id(self, ticket_id: str):
            import os
            import shutil
            destination = cf.project['storage'] + f'/{ticket_id}'
            if os.path.exists(destination):
                shutil.rmtree(destination)
            await self.collection.find_one_and_delete({"ticket_id": ticket_id})
            database_logger.info(f'Ticket with id {ticket_id} is deleted from database')

    class Preference:
        def __init__(self, collection):
            self.collection = collection

        async def insert(self, variable_data: dict):
            if 'key' in variable_data:
                existing_variable = await self.collection.find_one({"key": variable_data['key']})
                if not existing_variable:
                    await self.collection.insert_one(variable_data)
                    database_logger.info('New preference variable inserted in database')
                else:
                    database_logger.info('There is preference variable in database already')
            else:
                database_logger.error('No key in variable_data provided!')

        async def get_by_key(self, key: str):
            variable_data = await self.collection.find_one({"key": key})
            if variable_data:
                database_logger.info(f'Preference variable recording with key {key} is retrieved')
                return variable_data
            else:
                database_logger.info(f'Preference variable recording with key {key} is not found')
                return None

        async def get_question_by_id(self, question_id: str):
            variable_data = await self.collection.find_one({"key": 'faq'})
            if variable_data:
                questions = variable_data.get('questions', [])
                if questions:
                    for question in questions:
                        faq_question_id = question.get('question_id')
                        if faq_question_id == question_id:
                            database_logger.info(
                                f'Question faq variable recording with id {faq_question_id} is retrieved')
                            return question

            database_logger.info(f'Question faq variable recording with id {question_id} is not found')
            return None

        async def update_question_by_id(self, question_id: str, new_data: dict):
            # The positional $ operator will identify the correct element in the array to update.
            result = await self.collection.update_one(
                {'key': 'faq', 'questions.question_id': question_id},
                {'$set': {'questions.$': new_data}}
            )

            if result.modified_count:
                database_logger.info(f'Question with faq_id {question_id} is updated')
            else:
                database_logger.error(f'Question with faq_id {question_id} was not found or not updated')

        async def update(self, key: str, new_data: dict):
            await self.collection.update_one(
                {"key": key},
                {"$set": new_data}
            )
            database_logger.info(f'Preference variable with key {key} is updated')

        async def delete_by_key(self, key: str):
            await self.collection.find_one_and_delete({"key": key})
            database_logger.info(f'Preference with key {key} is deleted from database')


db = MongoDatabase()


async def generate_start_data():
    from resources import strings as strs
    faq = {'key': 'faq', 'questions': []}
    channel_info = {
        'key': 'channel_info',
        'id': cf.DEFAULT_CHANNEL_ID,
        'url': cf.DEFAULT_CHANNEL_URL,
        'is_on': True,
        'button_name': 'Ссылка'
    }
    start_info = {'key': 'start_message', 'value': strs.general_start}
    auto_release = {'key': 'release_hours', 'value': 1}
    auto_close = {'key': 'close_hours', 'value': 36}

    faq_data = await db.preferences.get_by_key(key='faq')
    if not faq_data:
        await db.preferences.insert(variable_data=faq)

    channel_data = await db.preferences.get_by_key('channel_info')
    if not channel_data:
        await db.preferences.insert(variable_data=channel_info)

    start_data = await db.preferences.get_by_key('start_message')
    if not start_data:
        await db.preferences.insert(variable_data=start_info)

    release_info = await db.preferences.get_by_key('release_hours')
    if not release_info:
        await db.preferences.insert(variable_data=auto_release)

    close_data = await db.preferences.get_by_key('close_hours')
    if not close_data:
        await db.preferences.insert(variable_data=auto_close)
