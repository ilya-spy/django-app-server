
from functools import wraps
import logging
from time import sleep
import os, sys

logger = logging.getLogger(__name__)



def backoff(start_sleep_time=0.1, factor=2, border_sleep_time=20):
    """
    Функция для повторного выполнения функции через некоторое время, если возникла ошибка.
    Использует наивный экспоненциальный рост времени
    повтора (factor) до граничного времени ожидания (border_sleep_time)

    Формула:
        t = start_sleep_time * 2^(n) if t < border_sleep_time
        t = border_sleep_time if t >= border_sleep_time
    :param start_sleep_time: начальное время повтора
    :param factor: во сколько раз нужно увеличить время ожидания
    :param border_sleep_time: граничное время ожидания
    :return: результат выполнения функции
    """

    def func_wrapper(func):
        @wraps(func)
        def inner(*args, **kwargs):
            time_sleep, n = 0, 0
            while True:
                try:
                    logger.info("### Backoff: attempt to run #" + str(n+1) )
                    sleep(time_sleep)
                    func(*args, **kwargs)
                except KeyboardInterrupt:
                    logger.error("### Backoff: procedure terminated forcebly")
                    break
                except Exception as ex:
                    exc_type, exc_obj, exc_tb = sys.exc_info()
                    fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                    print(exc_type, fname, exc_tb.tb_lineno)
                    logger.error(f"### Backoff: exception retrying:\n{func.__name__}\n{ex}")

                else:
                    # completed correctly, no need to repeat
                    return
                time_sleep = (
                    start_sleep_time * factor ** n
                    if time_sleep < border_sleep_time
                    else border_sleep_time
                )
                n += 1
                if n > 9:
                    logger.info("### Backoff: retry limit reached. Bail out...")
                    return
        return inner

    return func_wrapper