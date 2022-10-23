from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from routers import route_todo, route_auth
from schemas import SuccessMsg, CsrfSettings
from fastapi_csrf_protect import CsrfProtect
from fastapi_csrf_protect.exceptions import CsrfProtectError

# FastAPIを実行してインスタンスを生成
# route_todo.pyで作成したインスタンスを呼び出し
app = FastAPI()
app.include_router(route_todo.router)
app.include_router(route_auth.router)
# ホワイトリストの設定
origins = ['http://localhost:3000', 'https://fastapi-1436a.web.app']
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@CsrfProtect.load_config
def get_csrf_config():
    return CsrfSettings()


@app.exception_handler(CsrfProtectError)
def csrf_protect_exception_handler(request: Request, exc: CsrfProtectError):
    return JSONResponse(
        status_code=exc.status_code,
        content={'detail':  exc.message}
    )


# このパスにアクセスがあったときに実行される
# SuccessMsgの型を定義
@app.get("/", response_model=SuccessMsg)
def root():
    return {"message": "Welcome to Fast API"}
