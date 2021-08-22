import logging

errorLogger = logging.getLogger(__name__)
errorLogger.setLevel(logging.ERROR)

formatter = logging.Formatter('%(levelname)s:%(name)s:%(message)s')

file_handler = logging.FileHandler('session.log')
file_handler.setFormatter(formatter)

errorLogger.addHandler(file_handler)

# info logger to log create and update
infoLogger = logging.getLogger(__name__)
infoLogger.setLevel(logging.INFO)

formatter = logging.Formatter('%(levelname)s:%(name)s:%(message)s')

file_handler = logging.FileHandler('session.log')
file_handler.setFormatter(formatter)

infoLogger.addHandler(file_handler)
