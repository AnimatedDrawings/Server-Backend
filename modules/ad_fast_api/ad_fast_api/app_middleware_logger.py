# @app.middleware("http")
# async def add_process_time_header(request: Request, call_next):
#     start_time = time.time()
#     request_body = await request.body()

#     print()
#     print("-------------------------------------")
#     print(f"REQUEST_URL : {request.url}")
#     # print(f"REQUEST_BODY : {request_body}")
#     print(f"REQUEST_HEADERS : {request.headers}")

#     response = await call_next(request)

#     process_time = time.time() - start_time
#     print(f"PROCESS_TIME : {process_time}")
#     response_body = b""
#     async for chunk in response.body_iterator:
#         response_body += chunk

#     # 만약 HTTPException으로 인해 리턴된 JSON에 detail이 있다면
#     # try:
#     #     decoded_response = response_body.decode("utf-8")
#     #     print(f"RESPONSE_BODY : {decoded_response}")
#     # except UnicodeDecodeError:
#     #     pass

#     print("-------------------------------------")
#     return Response(
#         content=response_body,
#         status_code=response.status_code,
#         headers=dict(response.headers),
#         media_type=response.media_type,
#     )


# @app.exception_handler(HTTPException)
# async def http_exception_handler(request: Request, exc: HTTPException):
#     print()
#     print("#####################################")
#     print("######### HTTPException 발생 #########")
#     print(f"REQUEST_URL : {request.url}")
#     # print(f"REQUEST_BODY : {await request.json()}")
#     print(f"REQUEST_HEADERS : {request.headers}")
#     print(f"detail: {exc.detail}")
#     print(f"status_code: {exc.status_code}")
#     print("#####################################")
#     print()
#     return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})
