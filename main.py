import json

import pymongo.results
from loguru import logger
from fastapi import FastAPI, Query, Body
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, FileResponse
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, HttpUrl
from fastapi.middleware.cors import CORSMiddleware

import config
from bilibili_spider import bv_probe

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# @app.middleware("http")
# async def format_response(request, call_next):
#     response = await call_next(request)
#     print(type(response), response)
#
#     data = response.body
#     status_code = response.status_code
#
#     # 将响应统一格式化
#     formatted_response = {
#         "code": 0,
#         "msg": "ok",
#         "data": data,
#     }
#     return JSONResponse(content=formatted_response, status_code=status_code)


@app.on_event("startup")
async def startup():
    global client
    client = AsyncIOMotorClient(config.MONGO_URI)
    app.db = client[config.MONGO_DB][config.MONGO_COLLECTION]


@app.on_event("shutdown")
async def shutdown():
    client.close()


@app.get("/")
async def root():
    return FileResponse("static/index.html")

@app.get("/conversations")
async def get_conversation_list(page: int = Query(1, ge=1), size: int = Query(10, ge=1)):
    skip = (page - 1) * size
    cursor = app.db.find().skip(skip).limit(size)
    results = []
    async for item in cursor:
        item["id"] = str(item.pop("_id"))
        results.append(item)
    return results


class ConversationRequest(BaseModel):
    url: HttpUrl


@app.put("/conversation")
async def update_conversation(request: ConversationRequest = Body(...)):
    url = request.url

    probe = await bv_probe(url)
    # new_record: pymongo.results.InsertOneResult = await app.db.insert_one(probe)
    # return str(new_record.inserted_id)
    # with open("video_info_example.json", "w") as f:
    #     json.dump(probe, f, ensure_ascii=False, indent=4)
    return probe
