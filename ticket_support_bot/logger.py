# Standard
import logging
import os

# Project
import config as cf


class Logger:
    def __init__(self, name, logging_path: str):
        self.__logging_path = logging_path
        self.log = logging.getLogger(name)  # Unique logger per instance
        self.log.setLevel(logging.INFO)

        # Create file handler which logs messages to the specified file
        file_handler = logging.FileHandler(logging_path)
        file_handler.setLevel(logging.INFO)

        # Create formatter and add it to the handlers
        formatter = logging.Formatter('%(asctime)s,%(msecs)d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
                                      datefmt='%Y-%m-%d:%H:%M:%S')
        file_handler.setFormatter(formatter)

        # Add the handlers to the logger
        self.log.addHandler(file_handler)

    def clear_log_file(self):
        if self.__logging_path:
            with open(self.__logging_path, "w") as f:
                f.write("")
            return ""

    def info(self, msg: str):
        print(msg)  # Show in console
        self.log.info(msg)

    def warning(self, msg: str):
        print(msg)  # Show in console
        self.log.warning(msg)

    def error(self, msg: str):
        print(msg)  # Show in console
        self.log.error(msg)


logging_folder = cf.BASE + '/logs'
if not os.path.exists(logging_folder):
    os.makedirs(logging_folder, exist_ok=True)

bot_logger = Logger(name='bot', logging_path=os.path.join(logging_folder, 'bot_log.log'))
bot_logger.clear_log_file()
database_logger = Logger(name='database', logging_path=os.path.join(logging_folder, 'database_log.log'))
database_logger.clear_log_file()
background_logger = Logger(name='background', logging_path=os.path.join(logging_folder, 'background_log.log'))
background_logger.clear_log_file()
