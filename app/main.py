from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy import select
from app.middleware import CorrelationIdMiddleware
from app.logging_config import setup_logging, logger
from app.database import engine
from app.auth import AuthError
from app.api.task_manager import router as task_manager_router
from app.task_manager.service import TaskServiceError
from app.api.auth import router as auth_router


setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Application startup...")
    try:
        async with engine.connect() as conn:
            await conn.scalar(select(1))
        logger.info("Database connection established successfully")
    except Exception as e:
        logger.critical(
            "Failed to connect to database on startup: %s", str(e), exc_info=True
        )
        raise
    yield
    logger.info("Application shutdown...")
    await engine.dispose()


app = FastAPI(title="Task Manager API", version="1.0.0", lifespan=lifespan)
app.add_middleware(CorrelationIdMiddleware)


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.error(
        "Unhandled exception during %s %s",
        request.method,
        request.url.path,
        extra={"client_host": request.client.host, "headers": dict(request.headers)},
        exc_info=True,
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An internal server error occurred."},
    )


@app.exception_handler(TaskServiceError)
async def task_service_exception_handler(request: Request, exc: TaskServiceError):
    logger.error(
        "Task service error during %s %s: %s",
        request.method,
        request.url.path,
        str(exc),
        extra={"client_host": request.client.host},
        exc_info=True,
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An internal error occurred in the task service."},
    )


@app.exception_handler(AuthError)
async def auth_exception_handler(request: Request, exc: AuthError):
    logger.error(
        "Auth error during %s %s: %s",
        request.method,
        request.url.path,
        str(exc),
        extra={"client_host": request.client.host},
        exc_info=True,
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An authentication error occurred."},
    )


app.include_router(task_manager_router)
app.include_router(auth_router)


@app.get("/", tags=["Root"])
def read_root():
    return {"message": "Welcome to Task Manager API"}
