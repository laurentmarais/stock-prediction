from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.chart import router as chart_router
from app.api.routes.forecast import router as forecast_router
from app.api.routes.health import router as health_router
from app.api.routes.providers import router as providers_router
from app.api.routes.symbols import router as symbols_router
from app.api.routes.value_line import router as value_line_router


app = FastAPI(title="Stock Prediction API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(providers_router, prefix="/api")
app.include_router(symbols_router, prefix="/api")
app.include_router(value_line_router, prefix="/api")
app.include_router(chart_router, prefix="/api")
app.include_router(forecast_router, prefix="/api")
