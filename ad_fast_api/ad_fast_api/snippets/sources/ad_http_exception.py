from abc import ABC, abstractmethod


class HTTPExceptionABC(ABC):
    @classmethod
    @abstractmethod
    def status_code(cls) -> int:
        """반환할 HTTP status code를 정의합니다."""
        pass

    @classmethod
    @abstractmethod
    def detail(cls) -> str:
        """반환할 상세 메시지를 정의합니다."""
        pass
