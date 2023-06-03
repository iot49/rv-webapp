import asyncio
from pyscript import version_info
from js import console

from gateway import gateway_task
from dom_manipulations import message

GATEWAY = 'ws://10.0.0.8/ws'       # pros3
GATEWAY = 'ws://10.0.0.105/ws'     # s3 (development)
GATEWAY = 'ws://192.168.10.161/ws' # s3_prod on GL.iNet R
GATEWAY = 'ws://10.0.0.176/ws'     # s3_prod


async def main_task():
    console.log(f"gateway {GATEWAY}, pyscript {version_info}")
    message(f"PYSCRIPT version {version_info}")

    # start communication with gateway to get config and state updates
    asyncio.create_task(gateway_task(GATEWAY))


def global_exception_handler(loop, context):
    from io import StringIO
    import sys
    s = StringIO()
    s.write("***** global asyncio exception:")
    sys.print_exception(context["exception"], file=s)
    console.log(s.getvalue())


def main():
    try:
        console.log("webapp.main starting ...")
        # set exception handler
        loop = asyncio.get_event_loop()
        loop.set_exception_handler(global_exception_handler)
        asyncio.ensure_future(main_task())
    except Exception as e:
        console.log("***** FATAL - error starting app: {e}")