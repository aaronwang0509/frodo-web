# main.py
import os
import uuid
import logging
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.requests import Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi import HTTPException
from fastapi.staticfiles import StaticFiles
from starlette.responses import FileResponse
from api import auth, admin, env, token, paic, esv
from core.init import run_all
from core.settings import settings
from core.logger import request_id_ctx_var

# export environment variables
UVICORN_MODE = settings.UVICORN_MODE
FRONTEND_BUILD_DIR = settings.FRONTEND_BUILD_DIR
FRONTEND_ORIGIN = settings.FRONTEND_ORIGIN

run_all()

app = FastAPI()

# Mount routers first
app.include_router(auth.router, prefix="/auth", tags=["Authentication APIs"])
app.include_router(admin.router, prefix="/admin", tags=["Admin APIs"])
app.include_router(env.router, prefix="/env", tags=["Environment APIs"])
app.include_router(token.router, prefix="/token", tags=["Token APIs"])
app.include_router(paic.router, prefix="/paic", tags=["PAIC APIs"])
app.include_router(esv.router, prefix="/esv", tags=["ESV APIs"])

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal Server Error"}
    )

@app.middleware("http")
async def add_request_id(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    request_id_ctx_var.set(request_id)
    request.state.request_id = request_id

    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response

# Check environment mode
# if UVICORN_MODE == "production":
#     # Serve static frontend files in production
#     app.mount("/static", StaticFiles(directory=FRONTEND_BUILD_DIR + "/static"), name="static")

#     @app.get("/{full_path:path}")
#     async def serve_react_app(full_path: str):
#         return FileResponse(FRONTEND_BUILD_DIR + "/index.html")
# else:
#     # Enable CORS in development mode
#     app.add_middleware(
#         CORSMiddleware,
#         allow_origins=[FRONTEND_ORIGIN],
#         allow_credentials=True,
#         allow_methods=["*"], 
#         allow_headers=["*"],
#     )
