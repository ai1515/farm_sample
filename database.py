# mongoDBと連携するための処理

from email.policy import HTTP
from http.client import HTTPException
from decouple import config
from fastapi import HTTPException
from typing import Union
import motor.motor_asyncio
from bson import ObjectId
import certifi
from auth_utils import AuthJwtCsrf
import asyncio

# configを使い、.envで設定した環境変数を読み込んで格納
MONGO_API_KEY = config('MONGO_API_KEY')

# client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_API_KEY)
client = motor.motor_asyncio.AsyncIOMotorClient(
    MONGO_API_KEY, tlsCAFile=certifi.where())
client.get_io_loop = asyncio.get_event_loop
# MongoDBのデータベース名を指定して格納、データベースの中身も格納する、データベースとコレクションを使えるようにする
database = client.API_DB
collection_todo = database.todo
collection_user = database.user
auth = AuthJwtCsrf()


def todo_serializer(todo) -> dict:
    # 変換処理をして格納
    return {
        "id": str(todo["_id"]),
        "title": todo["title"],
        "description": todo["description"]
    }


def user_serializer(user) -> dict:
    # ユーザー情報の変換処理をして格納
    return {
        "id": str(user["_id"]),
        "email": user["email"],
    }


async def db_create_todo(data: dict) -> Union[dict, bool]:
    # FastAPIからMongoDBに対して新しくタスクを作る、create関数の作成
    # 戻り値と返り値を辞書型にする
    # 返り値を使うため、awaitを使い同期化して待つ、返ってきたらtodoに格納
    todo = await collection_todo.insert_one(data)
    # タスクをmongoDBから取得する
    new_todo = await collection_todo.find_one({"_id": todo.inserted_id})
    # あれば返す(変換処理のメソッドを実行)
    if new_todo:
        return todo_serializer(new_todo)
    return False

# Motorを使い、MongoDBからリストの形のタスクの一覧を取得


async def db_get_todos() -> list:
    todos = []
    for todo in await collection_todo.find().to_list(length=100):
        todos.append(todo_serializer(todo))
    return todos


# IDを指定してDBからデータを取得する,str型のIDをObjectIdに変換
# 引数の指定、返り値の型の指定
async def db_get_single_todo(id: str) -> Union[dict, bool]:
    todo = await collection_todo.find_one({"_id": ObjectId(id)})
    if todo:
        return todo_serializer(todo)
    return False


async def db_update_todo(id: str, data: dict) -> Union[dict, bool]:
    # UPDATE関数(IDの変換),UPDATE対象のものがあるかfind_oneで検索、あれば更新
    todo = await collection_todo.find_one({"_id": ObjectId(id)})
    if todo:
        updated_todo = await collection_todo.update_one(
            {"_id": ObjectId(id)}, {"$set": data}
        )
        # 更新されたデータがあったら返す
        if (updated_todo.modified_count > 0):
            new_todo = await collection_todo.find_one({"_id": ObjectId(id)})
            return todo_serializer(new_todo)
    return False


async def db_delete_todo(id: str) -> bool:
    # DELETE関数，DELETE対象のものがあるかfind_oneで検索、あれば削除
    todo = await collection_todo.find_one({"_id": ObjectId(id)})
    if todo:
        deleted_todo = await collection_todo.delete_one({"_id": ObjectId(id)})
        # 削除されたデータがあったらTrueを返す
        if (deleted_todo.deleted_count > 0):
            return True
        return False


# 入力されて新しく生成されたユーザーの情報をdict型で返す
async def db_signup(data: dict) -> dict:
    email = data.get("email")
    password = data.get("password")
    # 該当するユーザーが存在すれば変数に入る
    overlap_user = await collection_user.find_one({"email": email})
    # 重複エラー
    if overlap_user:
        raise HTTPException(status_code=400, detail='Email is already taken')
    # パスワードバリデーションエラー
    if not password or len(password) < 6:
        raise HTTPException(status_code=400, detail='Password too short')
    # DBに登録
    user = await collection_user.insert_one({"email": email, "password": auth.generate_hashed_pw(password)})
    new_user = await collection_user.find_one({"_id": user.inserted_id})
    return user_serializer(new_user)


async def db_login(data: dict) -> str:
    email = data.get("email")
    password = data.get("password")
    user = await collection_user.find_one({"email": email})
    if not user or not auth.verify_pw(password, user["password"]):
        raise HTTPException(
            status_code=401, detail='Invalid email or password'
        )
    # 問題ない場合の処理：JWTの生成
    token = auth.encode_jwt(user['email'])
    return token
