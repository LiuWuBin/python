import logging
import traceback


class LoggerFactory:
    def __init__(self, log_dir='logs', log_filename='app.log', log_level=logging.DEBUG):
        self.logger = None
        self.log_dir = log_dir
        self.log_filename = log_filename
        self.log_level = log_level

        self.logger = logging.getLogger(str(id(self)))
        self.logger.setLevel(log_level)
        handler = logging.FileHandler(f'{log_dir}/{log_filename}.log')
        formatter = logging.Formatter('%(asctime)s - %(message)s')
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)

    async def log_info(self, message):
        self.logger.info(message)
