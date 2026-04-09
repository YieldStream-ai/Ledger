"""AWS Lambda entry point — wraps FastAPI app with Mangum."""

from mangum import Mangum
from app.main import app

handler = Mangum(app, lifespan="off")
