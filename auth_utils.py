import jwt
from fastapi import HTTPException
from passlib.context import CryptContext
from datetime import datetime, timedelta
from decouple import config

# ユーザー関係のエンドポイント作成
# ・トークンの作成
# ・パスワードのハッシュ化
# →処理をまとめたクラスを作成

JWT_KEY = config('JWT_KEY')


class AuthJwtCsrf():
    # パスワードのハッシュ化などは提供されたライブラリの機能
    pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")
    secret_key = JWT_KEY

    # ユーザーがフォームに入力したパスワードを受け取ってハッシュ化したものをreturn
    def generate_hashed_pw(self, password) -> str:
        return self.pwd_ctx.hash(password)

    # ハッシュ化されたものと入力したパスワードが一致しているかを検証する
    def verify_pw(self, plain_pw, hashed_pw) -> bool:
        return self.pwd_ctx.verify(plain_pw, hashed_pw)

    # JWTを生成する
    # ユーザーのemailを受け取り、生成されたJWTをstr型で返す
    # payload:exp→JWTの有効期限の設定、iat→JWTが生成された日時、sub→ユーザーを一意に識別する情報
    def encode_jwt(self, email) -> str:
        payload = {
            'exp': datetime.utcnow() + timedelta(days=0, minutes=5),
            'iat': datetime.utcnow(),
            'sub': email
        }
        # 以下3つを使ってJWTを生成してくれる
        return jwt.encode(
            payload,
            self.secret_key,
            algorithm='HS256'
        )

    # JWTで変換された値の中身を解析して確認してくれるメソッド
    # 引数でJWTトークンを受け取り、それに対してデコードをかけていく
    def decode_jwt(self, token) -> str:
        # エラーの種類別に例外を分ける
        # 引数の値をデコードにかけて、subの値をリターン
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=['HS256'])
            return payload['sub']
        except jwt.ExpiredSignatureError:
            # 失効エラー
            raise HTTPException(
                status_code=401, detail='The JWT has expired')
        except jwt.InvalidTokenError as e:
            # トークンが空などのエラー
            raise HTTPException(status_code=401, detail='JWT is not valid')


def verify_jwt(self, request) -> str:
    # JWTトークンを取得
    token = request.cookies.get("access_token")
    # JWTトークンが存在しなかったら例外処理
    if not token:
        raise HTTPException(
            status_code=401, detail='No JWT exist: may not set yet or deleted')
    _, _, value = token.partition(" ")
    subject = self.decode_jwt(value)
    return subject


def verify_update_jwt(self, request) -> tuple[str, str]:
    subject = self.verify_jwt(request)
    new_token = self.encode_jwt(subject)
    return new_token, subject


def verify_csrf_update_jwt(self, request, csrf_protect, headers) -> str:
    # ライブラリの機能であるバリデーションを使う
    csrf_token = csrf_protect.get_csrf_from_headers(headers)
    csrf_protect.validate_csrf(csrf_token)
    subject = self.verify_jwt(request)
    new_token = self.encode_jwt(subject)
    return new_token
