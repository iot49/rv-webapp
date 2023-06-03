import asyncio
from pyscript import version_info
from js import console

from gateway import gateway_task
from dom_manipulations import message

GATEWAY = 'ws://10.0.0.176/ws'     # s3_prod @ 440 Davis Router (TPA - reliable)

"""
GL.iNet R
- "works"
- esp32 takes VERY long to connect - minutes
  - ignore internal wifi error, it keeps trying and eventually succeeds (?)
  - signal strength is not the issue
  - once connected, it seems reliable
- MDNS works!
  - http://rv-logger
  - http://rv-logger/config
- there is a new 4.x beta software for the GL.iNet
  - https://forum.gl-inet.com/t/wifi-constantly-disconnects-and-reconnects-on-gl-inet-gl-mt1300-beryl/26476/3
  - Others report it solving similar issues
  - I have not managed to install it
"""

GATEWAY = 'ws://rv-logger/ws'      # s3_prod on 


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