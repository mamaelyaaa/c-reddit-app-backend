import logging
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, Request, status
from fastapi.responses import ORJSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy import text

from api import router as main_router
from core import AppException, settings, db_helper, broker
from core.dependencies import SessionDep
from core.logger import setup_logging
from schemas import BaseResponseSchema

setup_logging()
logger = logging.getLogger("main")


@asynccontextmanager
async def lifespan(_: FastAPI):
    # Startup
    if not broker.is_worker_process:
        await broker.startup()

    yield
    # Shutdown

    if not broker.is_worker_process:
        await broker.shutdown()

    await db_helper.dispose()


app = FastAPI(
    title=settings.api.title,
    version=settings.api.version,
    lifespan=lifespan,
    default_response_class=ORJSONResponse,
)

app.include_router(main_router)


@app.get("/", response_model=BaseResponseSchema)
def get_root():
    return BaseResponseSchema(detail="Api is working!")


@app.get("/health-check", response_model=BaseResponseSchema)
async def get_db_connection(session: SessionDep):
    pg_version = await session.scalar(text("SELECT VERSION()"))
    return BaseResponseSchema(detail=str(pg_version))


@app.exception_handler(AppException)
async def handle_app_exception(request: Request, exc: AppException):
    return ORJSONResponse(status_code=exc.status_code, content={"detail": exc.message})


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = []
    for error in exc.errors():
        errors.append(
            {
                "field": ".".join(str(loc) for loc in error["loc"]),
                "message": error["msg"],
                "type": error["type"],
            }
        )

    return ORJSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": "Ошибка валидации данных", "errors": errors},
    )


# @app.middleware("http")
# async def http_middleware(request: Request, call_next):
#     request_msg = f"{request.method} {request.url.path}"
#
#     start_time = time.perf_counter()
#     response = await call_next(request)
#     process_time = time.perf_counter() - start_time
#     response.headers["X-Process-Time"] = f"{process_time * 1000:.4f}ms"
#
#     logger.info(f"{request_msg} {response.status_code}")
#     return response


if __name__ == "__main__":
    # logger.info(f"Приложение {settings.api.title} v{settings.api.version} стартовало")
    # logger.info(f"Запущено на {settings.run.url}")

    uvicorn.run(
        app="src.main:app",
        reload=True,
        host=settings.run.host,
        port=settings.run.port,
    )

    # logger.warning(f"Приложение {settings.api.title} остановлено")
