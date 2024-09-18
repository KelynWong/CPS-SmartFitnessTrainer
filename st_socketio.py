import gc
from typing import Optional, Callable
from socketio import AsyncServer
from streamlit.runtime.scriptrunner import add_script_run_ctx
from streamlit.web.server.websocket_headers import get_websocket_headers

sio = AsyncServer(async_mode='asgi', cors_allowed_origins='*')

class SocketioRegister:
    @classmethod
    def instance(cls, path: str) -> 'SocketioRegister':
        inst = cls()
        print(f' Mounting Socket.IO on {path}')
        return inst

def st_socketio(path: str):
    def wrap(f: Callable):
        SocketioRegister.instance(path)
        return f
    return wrap

@sio.on('connect')
async def connect(sid, environ):
    print('connect ', sid)
    ctx = get_websocket_headers()
    add_script_run_ctx(ctx)

@sio.on('disconnect')
def disconnect(sid):
    print('disconnect ', sid)

def get_sio_asgi_app():
    return sio.asgi_app

# This function should be called from your main Streamlit app
def init_socketio():
    gc.collect()  # Force garbage collection