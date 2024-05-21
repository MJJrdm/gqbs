import logging
from datetime import datetime

##### 创建logger，进行日志记录
def setup_logger():
    
    logger = logging.getLogger('my_logger')
    logger.setLevel(logging.DEBUG)


    if not logger.hasHandlers():
        # 获取当前时间，以当前时间命名日志文件
        current_time = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        log_filename = f'{current_time}.log'
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

        # 创建一个文件处理器并设置级别
        file_handler = logging.FileHandler(log_filename)
        file_handler.setLevel(logging.INFO) # file_handler接收程度 >= INFO的日志
        file_handler.setFormatter(formatter)

        # 创建并设置StreamHandler(输出到控制台)
        stream_handler = logging.StreamHandler()
        stream_handler.setLevel(logging.DEBUG)  # stream_handler接收程度 >= DEBUG的日志
        stream_handler.setFormatter(formatter)

        # DEBUG, INFO, WARNING, ERROR, CRITICAL
        # 将处理器添加到日志记录器中
        logger.addHandler(file_handler)
        logger.addHandler(stream_handler)

    return logger

logger = setup_logger()
