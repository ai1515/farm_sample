# クライアント側からエンドポイントに渡すデータ型、レスポンスのデータ型を定義

from pydantic import BaseModel
from typing import Optional
from decouple import config

# fastapi-csrf-protectライブラリの機能
CSRF_KEY = config('CSRF_KEY')


class CsrfSettings(BaseModel):
    secret_key: str = CSRF_KEY


class Todo(BaseModel):
    id: str
    title: str
    description: str


class TodoBody(BaseModel):
    title: str
    description: str


class SuccessMsg(BaseModel):
    message: str


class UserBody(BaseModel):
    email: str
    password: str


class UserInfo(BaseModel):
    # 使い回すクラスのため、IDを任意の値にできる形で、デフォルトをNoneに設定
    id: Optional[str] = None
    email: str


class Csrf(BaseModel):
    csrf_token: str
