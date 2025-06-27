# main.py
import os
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.requests import Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi import HTTPException
from fastapi.staticfiles import StaticFiles
from starlette.responses import FileResponse
from api import auth, business, admin
from core.init import run_all
from core.settings import settings

# export environment variables
UVICORN_MODE = settings.UVICORN_MODE
FRONTEND_BUILD_DIR = settings.FRONTEND_BUILD_DIR
FRONTEND_ORIGIN = settings.FRONTEND_ORIGIN

app = FastAPI()

run_all()

# Mount routers first
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
# app.include_router(business.router, prefix="/api", tags=["Business APIs"])
app.include_router(admin.router, prefix="/admin", tags=["Admin APIs"])

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal Server Error"}
    )

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
