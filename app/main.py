import logging
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from app.routers import reviews, auth, webhooks
from fastapi.middleware.cors import CORSMiddleware

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("codesage")
# GIVING FastAPI() to app
app = FastAPI(title="CodeSage")
app.add_middleware( #a method used to register code that runs for every single HTTP request and response
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(reviews.router)
app.include_router(webhooks.router)

@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception(f"Unhandled error on {request.method} {request.url.path}")
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})

@app.get("/health")
def health():
    return {"status": "ok"}
