import functools
import time
import asyncio


def measure_execution_time(func_name: str):
    def decorator(func):
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            result = await func(*args, **kwargs)
            end_time = time.time()
            execution_time = (end_time - start_time) * 1000
            print(f"\n{func_name} execution time: {execution_time:.2f} ms")
            return result

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            result = func(*args, **kwargs)
            end_time = time.time()
            execution_time = (end_time - start_time) * 1000
            print(f"\n{func_name} execution time: {execution_time:.2f} ms")
            return result

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


"""
@measure_execution_time("동기 함수")
def sync_function():
    time.sleep(1)
    return "완료"

@measure_execution_time("비동기 함수")
async def async_function():
    await asyncio.sleep(1)
    return "완료"
"""
