# https://github.com/SubstructureOne/wasmsockets/tree/main

import sys
from asyncio import Queue, Event
from typing import Any, Callable, Optional
from dataclasses import dataclass

BytesLike = bytes, bytearray, memoryview


def iswasm():
    return sys.platform == 'emscripten'


if iswasm():
    # These packages are only available in a Pyodide environment. They never
    # need to be installed separately. We will only reference them when we
    # detect we are running in WebAssembly.
    import js
    import pyodide.ffi
else:
    import websockets


async def connect(uri):
    socket = _WasmSocket(uri)
    await socket.connect()


    return socket


@dataclass
class SabProxy:
    send: Callable[[Any], None]
    recv: Callable[[], Any]

SAB_PROXY: Optional[SabProxy] = None

def use_sab_proxy(send, recv):
    global SAB_PROXY
    SAB_PROXY = SabProxy(send, recv)


class _WasmSocket:
    def __init__(self, uri):
        from js import console
        self._uri = uri
        # _jssocket or _pysockets only gets initialized when calling connect().
        # _jssocket will be initialized in a WebAssembly environment; _pysocket
        # will be initialized in a native environment.
        self._jssocket = None
        self._pysocket = None
        self._message_handlers = list()
        if iswasm():
            self._incoming = Queue()
            self._isopen = Event()
        else:
            self._incoming = None
            self._isopen = None

    @property
    def connected(self):
        return self._isopen.is_set()

    async def connect(self):
        if iswasm():
            js.console.log(f"WS: connect to {self._uri} ...")
            try:
                socket = js.WebSocket.new(self._uri)
                js.console.log(f"WS: socket created {socket}")
            except Exception as e:
                js.console.log(f"WS: connect - exception {e}")
            socket.binaryType = "arraybuffer"
            socket.addEventListener(
                'open',
                pyodide.ffi.create_proxy(self._open_handler)
            )
            socket.addEventListener(
                'close',
                pyodide.ffi.create_proxy(self._close_handler)
            )
            socket.addEventListener(
                'message',
                pyodide.ffi.create_proxy(self._message_handler)
            )
            socket.addEventListener(
                'error',
                pyodide.ffi.create_proxy(self._error_handler)
            )
            self._jssocket = socket
        else:
            self._pysocket = await websockets.connect(self._uri)
 
    async def send(self, message):
        """Sends a message over the WebSocket.

        Sends a Binary frame if message is bytes-like; sends as a Text frame
        if message is a str.

        NOTE: while the native websockets library supports fragmentation via
        sending in an iterable, the WebAssembly version currently does not.
        Only pass in a str or a bytes-like object.
        """
        if iswasm():
            # js.console.log(f"Sending message: {message}; checking for socket open {self._isopen.is_set()}")
            if not self._isopen.is_set():
                js.console.log(f"WS waiting for connection to send: {message}")
            await self._isopen.wait()
            # js.console.log(f"Socket now open; sending")
            if isinstance(message, BytesLike):
                data = pyodide.ffi.to_js(message)
            else:
                data = message
            self._jssocket.send(data)
        else:
            await self._pysocket.send(message)

    def send_sync(self, message):
        if SAB_PROXY is None:
            raise NotImplementedError("Sync methods only supported when using the SharedArrayBuffer proxy")
        if isinstance(message, BytesLike):
            data = pyodide.ffi.to_js(message)
        else:
            data = message
            SAB_PROXY.send(data)

    async def recv(self):
        if iswasm():
            # js.console.log(f"Receiving message; checking for socket open")
            await self._isopen.wait()
            # js.console.log(f"Waiting to receive message...")
            result = await self._incoming.get()
            # js.console.log(f"Message received: {result}")
        else:
            result = await self._pysocket.recv()
        return result

    def recv_sync(self):
        if SAB_PROXY is None:
            raise NotImplementedError("Sync methods only supported when using the SharedArrayBuffer proxy")
        return SAB_PROXY.recv()

    async def close(self):
        if iswasm():
            self._isopen.clear()
            self._jssocket.close()
        else:
            await self._pysocket.close()

    def add_handlers(self, message_handler, wait_handler):
        # When running in a WASM environment, we may want/need to synchronously
        # wait for a message to be received. This is complicated because if we
        # block the main thread of execution, we can't receive any messsages,
        # so we'll never unblock. Therefore we need to pass off the handling of
        # receiving message to another worker.
        pass

    # JS callback handlers

    async def _open_handler(self, event):
        js.console.log(f"WS: connected to {self._uri}", event)
        self._isopen.set()

    async def _close_handler(self, event):
        js.console.log(f"WS: Close event:", event)
        self._isopen.clear()

    async def _message_handler(self, event):
        # js.console.log(f"WS: Message event:", event)
        await self._incoming.put(event.data)

    async def _error_handler(self, event):
        js.console.log(f"WS: Error event:", event)
 