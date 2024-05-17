# from loguru import logger

# # Configure Loguru to write logs to a file
# logger.add("app.log", rotation="500 MB")

# # Log messages at different levels
# logger.debug("This is a debug message")
# logger.info("This is an info message")
# logger.warning("This is a warning message")
# logger.error("This is an error message")
# logger.critical("This is a critical message")


from loguru import logger
# Log an informational message
logger.info("Hello, Loguru!")
# Log a warning message
logger.warning("This is a warning")
# Log an error message
logger.error("Oops! Something went wrong")



# from loguru import logger
# # Configure Loguru to write logs to a file
# logger.add("app.log")
# # Log messages
# logger.info("Hello, Loguru!")
# logger.warning("This is a warning")
# logger.error("Oops! Something went wrong")



# from loguru import logger
# # Customize log message format
# logger.add("app.log", format="{time} - {level} - {message}")
# # Log messages
# logger.info("Hello, Loguru!")
# logger.warning("This is a warning")
# logger.error("Oops! Something went wrong")



# from loguru import logger
# # Rotate log files when they reach 100 MB
# logger.add("app.log", rotation="100 MB")
# # Log messages
# logger.info("Hello, Loguru!")
# logger.warning("This is a warning")
# logger.error("Oops! Something went wrong")




# from loguru import logger
# logger.debug("This is a debug message")
# logger.info("This is an info message")
# logger.warning("This is a warning message")
# logger.error("This is an error message")
# logger.critical("This is a critical message")




from loguru import logger

def main():
    # Configure Loguru to write logs to a file
    logger.add("app.log")

    # Create the logger instance
    main_logger = logger.bind(context="main")

if __name__ == "__main__":
    main()


# # # # # import logging

# # # # # # 创建一个日志记录器
# # # # # logger = logging.getLogger('my_logger')

# # # # # logger.setLevel(logging.DEBUG)


# # # # # # 创建一个文件处理器

# # # # # file_handler = logging.FileHandler('my_logs.log')
# # # # # file_handler.setLevel(logging.INFO)


# # # # # # 创建一个格式化程序
# # # # # formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
# # # # # file_handler.setFormatter(formatter)

# # # # # # 将处理器添加到日志记录器中
# # # # # logger.addHandler(file_handler)
# # # # # # 记录一些消息
# # # # # logger.debug('这是一个调试消息')
# # # # # logger.info('这是一个信息消息')
# # # # # logger.warning('这是一个警告消息')
# # # # # logger.error('这是一个错误消息')
# # # # # logger.critical('这是一个严重错误消息')
# # # # # # 在这个示例中:

# # # # # # 我们创建了一个名为 'my_logger' 的日志记录器。
# # # # # # 我们将日志记录器级别设置为 DEBUG。
# # # # # # 我们创建了一个文件处理器，并将其级别设置为 INFO。
# # # # # # 我们创建了一个指定日志消息格式的格式化程序。
# # # # # # 我们将格式化程序添加到文件处理器中。
# # # # # # 最后，我们记录了不同级别的消息。
# # # # # # 此设置将会将级别为 INFO、WARNING、ERROR 和 CRITICAL 的消息记录到文件 'my_logs.log' 中
# # # # # # Loggers提供程序直接使用的接口
# # # # # # Handlers将记录的日志发送到指定位置
# # # # # # Filters用于过滤特定的日志记录
# # # # # # Formatters用于控制日志信息的输出格式

# # # # # import logging

# # # # # # 创建一个logger（日志记录器）对象；
# # # # # my_logger = logging.Logger("first_logger")
# # # # # my_logger = logging.Logger('logger1')

# # # # # # 第一个日志处理器
# # # # # my_handler = logging.FileHandler('test.log')
# # # # # my_handler = logging.FileHandler('test.log')

# # # # # my_handler.setLevel(logging.INFO)
# # # # # my_handler.setLevel(logging.INFO)
# # # # # my_format = logging.Formatter("时间:%(asctime)s 日志信息：%(message)s 行号:%(lineno)d")
# # # # # my_format = logging.Formatter("时间:%(asctime)s 日志信息: %(message)s 行号:%(lineno)d")
# # # # # my_handler.setFormatter(my_format)
# # # # # my_handler.setFormatter(my_format)
# # # # # my_logger.addHandler(my_handler)
# # # # # my_logger.addHandler(my_handler)


# # # # # # 第二个日志处理器
# # # # # you_handler = logging.StreamHandler()

# # # # # you_handler.setLevel(logging.DEBUG)

# # # # # you_format = logging.Formatter("时间:%(asctime)s 日志信息：%(message)s 行号:%(lineno)d 这是StreamHandler")

# # # # # you_handler.setFormatter(you_format)

# # # # # my_logger.addHandler(you_handler)



# # # # # # 使用：
# # # # # my_logger.info("我是日志组件")
# # # # # my_logger.info("我是日志组件")




# # import logging

# # logger = logging.Logger('name')
# # logger.setLevel(logging)

# # handler = logging.FileHandler('plan.log')

import logging

# 自定义过滤器类
class MyFilter(logging.Filter):
    def filter(self, record):
        # 只记录指定级别的日志消息
        return record.levelno >= logging.WARNING
    
class Filter2(logging.Filter):
    def filter(self, record):
        return record.levelno == logging.ERROR
    
class Filter3(logging.Filter):
    def filter(self, log_record):
        return log_record.levelno >= logging.WARNING


# 配置日志记录器
logger = logging.getLogger('my_logger')
logger.setLevel(logging.DEBUG)

# 创建一个文件处理器并设置级别
file_handler = logging.FileHandler('my_logshh1.log')
file_handler.setLevel(logging.DEBUG)

# 创建一个格式化程序并设置给处理器
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)

# 创建一个过滤器对象并添加到处理器中
filter = MyFilter()
filter3 = Filter3()
file_handler.addFilter(filter3)

stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.ERROR)
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)


# 将处理器添加到日志记录器中
logger.addHandler(file_handler)

# 记录一些日志消息
logger.debug('This is a debug message')
logger.info('This is an info message')
logger.warning('This is a warning message')
logger.error('This is an error message')
logger.critical('This is a critical message')



# Logger, Handler, Formatter, Filter
logger = logging.Logger()
file_handler = logging.FileHandler('log_file.log')
stream_handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s  %(name)s  %(levelname)s ')



# 5 levels of logging message: DEBUG, INFO, WARNING, ERROR, CRITICAL
import logging
logging.basicConfig(level = 'DEBUG')
logging.debug('This is a bug')
logging.info('This is an info')
logging.warning('This is a warning')
logging.error('This is an error')
# logging.critical('This is critical!')