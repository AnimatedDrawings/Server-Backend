import logging
import time


def record_time(task_func):
    def wrapper(*args, **kwargs):
        start_time = time.time()
        logging.info(
            "작업 시작 시간: "
            + time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(start_time))
        )
        result = task_func(*args, **kwargs)
        end_time = time.time()
        logging.info(
            "작업 종료 시간: "
            + time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(end_time))
        )
        return result

    return wrapper
