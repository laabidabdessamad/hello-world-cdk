from fastapi import FastAPI
from mangum import Mangum

app = FastAPI()


@app.get("/")
def read_root():
    return {"message": "hello world"}


# Mangum adapts the ASGI app (FastAPI) to the Lambda handler interface.
handler = Mangum(app)
