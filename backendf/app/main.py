from common.utils.logger_config import setup_logging

# logging 設定
setup_logging()

from contextlib import asynccontextmanager

from app.api.router import master_router  # type: ignore
from fastapi import FastAPI

# from scalar_fastapi import get_scalar_api_reference


@asynccontextmanager
async def lifespan_handler(app: FastAPI):
    # 這邊沒有await是可以的嗎?
    print("FastAPI Server Starting...")
    yield


app = FastAPI(lifespan=lifespan_handler)
app.include_router(master_router)


# Server Running Status
@app.get("/")
def read_root():
    return {"detail": "Welcome to Allpass!"}


# import logging
# import os

# # 匯入各個 router
# from app.api.health import router as health_router
# from app.api.login import router as login_router
# from app.api.register import router as register_router
# from app.api.trails import router as trails_router
# from fastapi import FastAPI
# from fastapi.middleware.cors import CORSMiddleware
# from pydantic import BaseModel

# # --- 初始化 FastAPI App ---
# app = FastAPI(
#     title="AllPass Hiking Time Prediction API",
#     description="登山時間預測系統後端 (FastAPI 版本)",
#     version="2.0.0",
# )

# # --- CORS 設定 ---
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],  # 可改成前端網域
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )


# # --- 註冊 Routers ---
# app.include_router(health_router, prefix="/health", tags=["Health"])
# app.include_router(trails_router, prefix="/api/trails", tags=["Trails"])
# app.include_router(register_router, prefix="/api/register", tags=["Register"])
# app.include_router(login_router, prefix="/api/login", tags=["Login"])


# @app.get("/")
# def read_root():
#     return {"status": "Welcome to Allpass!"}
