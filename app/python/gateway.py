import asyncio
import json
from js import console, document

from wasm_websocket import connect
from dom_manipulations import message, create_views, show_page
from dom_events import add_nav_events
from utilities import config, ids


_REPORT_TRANSACTIONS = False


class _Gateway:
    """Websocket communication with gateway (ESP32)"""

    def __init__(self, url):
        self._url = url
        self._ws = None
        self._ping_interval = 5
        self._splash_msg = None


    def splash_msg(self, msg, clear=False):
        if self._splash_msg == None:
            self._splash_msg = document.getElementById("splash")
        splash = self._splash_msg
        if clear:
            # remove all children
            while splash.firstChild:
                splash.removeChild(splash.firstChild)
        div = document.createElement('div')
        div.innerText = msg
        splash.appendChild(div)


    async def _send(self, msg):
        assert isinstance(msg, dict)
        assert 'tag' in msg
        if _REPORT_TRANSACTIONS: console.log(f"send {msg}")
        return await asyncio.wait_for(self._ws.send(json.dumps({ 'data': msg })), 10) 


    async def _ping_pong_task(self):
        """Send pings at reglar intervals:
        Gateway disconnects if no messages received for too long.
        Webapp reconnects if connection dead.
        """
        while True:
            if self._ws != None:
                try:
                    await asyncio.wait_for(self._send({ "tag": "ping" }), self._ping_interval)
                    await asyncio.sleep(self._ping_interval)
                except asyncio.TimeoutError:
                    console.log(f"***** ping_pong_task: timeout - disconnected?")
            


    async def run(self):
        # get this going and never stop
        asyncio.create_task(self._ping_pong_task())

        startup = True

        # connect / reconnect loop
        while True:
            # try connecting until successful
            self.splash_msg(f"Attempting connection to {self._url}")
            while True:
                try:
                    self._ws = await connect(self._url)
                    await asyncio.wait_for(self._send({ "tag": "ping" }), 240) 
                    break
                except asyncio.TimeoutError as e:
                    console.log(f"***** gateway.run timeout: {e}")
                except Exception as e:
                    console.log(f"***** gateway.run connecting: {e}")
                self.splash_msg(f"Is the gateway up?")
                try:
                    await self._ws.close()
                except Exception as e:
                    console.log(f"***** gateway.run close: {e}")

            try:
                if startup:
                    # wait for config_put to get the configuration & show the app screen
                    await self._send({ 'tag': 'config_get' })
                    startup = False
                else:
                    # make sure state is up-to-date after a possibily long disconnect
                    await self._send({ 'tag': 'state_get_all' })
                    show_page(last_page)

                # receive messages until disconnect detected        
                await self._recv()
                console.log(f"***** Gateway disconnected")
                last_page = show_page('splashscreen')
                self.splash_msg(f"Gateway disconnected", True)
            except Exception as e:
                console.log(f"***** gateway.run finishing: {e}")


    async def _recv(self):
        # perpetually receive messages - until connection breaks
        while True:
            try:
                msg = await asyncio.wait_for(self._ws.recv(), timeout=self._ping_interval)
                if _REPORT_TRANSACTIONS: console.log(f"recv {msg}")
            except asyncio.TimeoutError:
                console.log(f"GATEWAY TIMEOUT: lost connection, ping interval = {self._ping_interval}")
                try:
                    await self._ws.close()
                except Exception:
                    pass
                return
            except Exception as e:
                console.log(f"***** gateway recv: {e}")
                continue

            msg = json.loads(msg)
            # console.log("GATEWAY got", str(msg))
            try:
                tag = msg["tag"] 
                method = getattr(self, f"_handle_{tag}")
            except KeyError:
                console.log(f"***** Message has no tag attribute: {msg}")
                continue
            except AttributeError:
                console.log(f"***** No handler for {tag}: {msg}")
                continue
            try:
                del msg["tag"]
                # console.log(f"CALL {method}")
                await method(**msg)
            except Exception as e:
                console.log(f"***** gateway - error handling: {msg}", str(e))


    async def _handle_config_put(self, value, path=[]):
        # accept only full configuration
        assert len(path) == 0

        # notify user that we are updating the app
        self.splash_msg(f"Configuration received")
        last_page = show_page('splashscreen')
        
        config.set(value)
        self._ping_interval = float(config.get('app', 'ping-interval')) or 8

        # update view to match new config
        self.splash_msg(f"Create views")
        create_views()
        self.splash_msg(f"Attach event handlers")
        add_nav_events()
        self.splash_msg(f"Setup Complete")

        # show the last selected page (defaults to view-1 on app startup)
        show_page(last_page)

        # get current state
        await self._send({ "tag": "state_get_all" })


    async def _handle_state_update(self, eid, value, all=False):
        for entity in document.getElementsByClassName(ids.css(eid)):
            if isinstance(value, float):
                value = f"{value:.1f}"
            entity.querySelector('.entity-value').innerText = value


    async def _handle_info(self, category, msg):
        message(f"{category}: {msg}")


    async def _handle_discovered(self, device):
        message(f"discovered: {device}")


    async def _handle_ping(self):
        await self._send({ "tag": "pong" })


    async def _handle_pong(self):
        # nothing to do - recv task already took note
        pass


async def gateway_task(url='ws://10.0.0.8/ws'):
    """Communicate with gateway. Automatic reconnects. This never returns."""
    gateway = _Gateway(url)
    await gateway.run()

