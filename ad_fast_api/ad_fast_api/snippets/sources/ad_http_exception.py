from typing import Any, Callable
from fastapi import HTTPException


def handle_operation(
    operation: Callable,
    status_code: int = 500,
    *args,
    **kwargs,
) -> Any:
    """
    비동기 작업을 실행하고 예외를 처리하는 헬퍼 함수

    Args:
        operation: 실행할 비동기 함수
        args: operation에 전달할 위치 인자
        kwargs: operation에 전달할 키워드 인자

    Returns:
        operation의 실행 결과

    Raises:
        HTTPException: HTTP 관련 예외 발생 시 그대로 전달
        HTTPException: 기타 예외 발생 시 500 에러로 변환하여 전달
    """
    try:
        return operation(*args, **kwargs)
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=status_code,
            detail=str(e),
        )


async def handle_operation_async(
    operation: Callable,
    status_code: int = 500,
    *args,
    **kwargs,
) -> Any:
    """
    비동기 작업을 실행하고 예외를 처리하는 헬퍼 함수

    Args:
        operation: 실행할 비동기 함수
        args: operation에 전달할 위치 인자
        kwargs: operation에 전달할 키워드 인자

    Returns:
        operation의 실행 결과

    Raises:
        HTTPException: HTTP 관련 예외 발생 시 그대로 전달
        HTTPException: 기타 예외 발생 시 500 에러로 변환하여 전달
    """
    try:
        return await operation(*args, **kwargs)
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=status_code,
            detail=str(e),
        )
