from fastapi import FastAPI
import uvicorn
from version import __version__

from interfaces.api import weather_router
from utils.configs import NSFWSetting

basic_settings = NSFWSetting()
app = FastAPI(
    title=basic_settings.APP_NAME,
    description="NotSoFancyWeather(NSFW) API",
    version=__version__
)

app.include_router(weather_router, prefix="/api")


@app.get(path="/")
def get_root():
    return {"Hello": "World"}


if __name__ == "__main__":
    uvicorn.run(
        app="main:app",
        host=basic_settings.HOST,
        port=basic_settings.PORT,
        reload=basic_settings.RELOAD
    )    
