import json
import sys

import websockets
import asyncio
from ._transport import Transport

if sys.version_info[0] < 3:
    from urlparse import urlparse, urlunparse
else:
    from urllib.parse import urlparse, urlunparse


class WebSocketsTransport(Transport):
    def __init__(self, session, connection):
        Transport.__init__(self, session, connection)
        self.ws = None
        self.__requests = {}

    def _get_name(self):
        return 'webSockets'

    @staticmethod
    def __get_ws_url_from(url):
        parsed = urlparse(url)
        scheme = 'wss' if parsed.scheme == 'https' else 'ws'
        url_data = (scheme, parsed.netloc, parsed.path, parsed.params, parsed.query, parsed.fragment)

        return urlunparse(url_data)

    async def start(self):
        ws_url = self.__get_ws_url_from(self._get_url('connect'))
        self._session.get(self._get_url('start'))
        self.ws = await websockets.connect(ws_url, extra_headers=self.__get_headers())
        asyncio.gather(self.loop(), return_exceptions=True)

    async def loop(self):
        while True:
            try:
                message = await self.ws.recv()
                self._handle_notification(message)
            except websockets.ConnectionClosed:
                print("bittrex connection closed")
                break

    async def send(self, data):
        await self.ws.send(json.dumps(data))

    def close(self):
        self.ws.close()

    def accept(self, negotiate_data):
        return bool(negotiate_data['TryWebSockets'])

    class HeadersLoader(object):
        def __init__(self, headers):
            self.headers = headers

    def __get_headers(self):
        headers = self._session.headers
        if len(self.__get_cookie_str()) > 0:
            headers['cookie'] = self.__get_cookie_str()
        loader = WebSocketsTransport.HeadersLoader(headers)

        if self._session.auth:
            self._session.auth(loader)

        return headers

    def __get_cookie_str(self):
        return '; '.join([
                             '%s=%s' % (name, value)
                             for name, value in self._session.cookies.items()
                             ])
