from ad_fast_api.snippets.sources.ad_http_exception import HTTPExceptionABC


class UPLOADED_FILE_EMPTY_OR_INVALID(HTTPExceptionABC):
    @classmethod
    def status_code(cls) -> int:
        return 400

    @classmethod
    def detail(cls) -> str:
        return "Uploaded file is empty or invalid."


class IMAGE_IS_NOT_RGB(HTTPExceptionABC):
    @classmethod
    def status_code(cls) -> int:
        return 401

    @classmethod
    def detail(cls) -> str:
        return "Image is not RGB."
