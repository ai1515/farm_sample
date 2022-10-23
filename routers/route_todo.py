from http.client import HTTPException
from fastapi import APIRouter
from fastapi import Response, Request, HTTPException, Depends
# JSON型から辞書型に変換する
from fastapi.encoders import jsonable_encoder
from schemas import Todo, TodoBody, SuccessMsg
from database import db_create_todo, db_get_todos, db_get_single_todo, db_update_todo, db_delete_todo
from starlette.status import HTTP_201_CREATED
from typing import List
from fastapi_csrf_protect import CsrfProtect
from auth_utils import AuthJwtCsrf

# エンドポイントの作成,データ型を指定(Todo)

router = APIRouter()
auth = AuthJwtCsrf()


@router.post("/api/todo", response_model=Todo)
# 受け取った値をdb_create_todo関数に渡す
# レスポンスのステータスをカスタマイズする
# resの値が存在したら返す、なかったら例外処理
# セキュリティ機能も実装(JWTとCSRFtoken)、生成されたJWTをセットクッキーする
async def create_todo(request: Request, response: Response, data: TodoBody, csrf_protect: CsrfProtect = Depends()):
    new_token = auth.verify_csrf_update_jwt(
        request, csrf_protect, request.headers)
    todo = jsonable_encoder(data)
    res = await db_create_todo(todo)
    response.status_code = HTTP_201_CREATED
    response.set_cookie(
        key="access_token", value=f"Bearer {new_token}", httponly=True, samesite="none", secure=True)
    if res:
        return res
    raise HTTPException(
        status_code=404, detail="Create task failed")


@router.get("/api/todo", response_model=List[Todo])
# タスクの一覧を取得するエンドポイント
# セキュリティはJWTのみ
async def get_todos(request: Request):
    auth.verify_jwt(request)
    res = await db_get_todos()
    return res


@router.get("/api/todo/{id}", response_model=Todo)
# 特定のIDに基づいて1つのタスクを取得するGETメソッド
# 変数を結合するときはfを使う
async def get_single_todo(request: Request, response: Response, id: str):
    new_token, _ = auth.verify_update_jwt(request)
    res = await db_get_single_todo(id)
    response.set_cookie(
        key="access_token", value=f"Bearer {new_token}", httponly=True, samesite="none", secure=True)
    if res:
        return res
    raise HTTPException(
        status_code=404, detail=f"Task of ID:{id} doesn't exist")


@router.put("/api/todo/{id}", response_model=Todo)
# 更新のエンドポイント
# jsonable_encoderでdict型に変換
async def update_todo(request: Request, response: Response, id: str, data: TodoBody, csrf_protect: CsrfProtect = Depends()):
    new_token = auth.verify_csrf_update_jwt(
        request, csrf_protect, request.headers)
    todo = jsonable_encoder(data)
    res = await db_update_todo(id, todo)
    response.set_cookie(
        key="access_token", value=f"Bearer {new_token}", httponly=True, samesite="none", secure=True)
    if res:
        return res
    raise HTTPException(
        status_code=404, detail="Update task failed")


@router.delete("/api/todo/{id}", response_model=SuccessMsg)
# 削除のエンドポイント
async def delete_todo(request: Request, response: Response, id: str, csrf_protect: CsrfProtect = Depends()):
    new_token = auth.verify_csrf_update_jwt(
        request, csrf_protect, request.headers)
    res = await db_delete_todo(id)
    response.set_cookie(
        key="access_token", value=f"Bearer {new_token}", httponly=True, samesite="none", secure=True)
    if res:
        return {'message': 'Successfully deleted'}
    raise HTTPException(
        status_code=404, detail="Delete task failed")
