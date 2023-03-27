    from __future__ import annotations
    
    from maubot import Plugin
    from maubot.handlers import event
    from mautrix.types import EventType, RoomID, StateEvent, MessageType, TextMessageEventContent, MediaMessageEventContent, \
        ImageInfo
    import datetime
    import asyncio
    from typing import TYPE_CHECKING
    from asyncio import AbstractEventLoop
    from aiohttp import ClientSession
    from sqlalchemy.engine.base import Engine
    from mautrix.util.config import BaseProxyConfig
    from mautrix.util.logging import TraceLogger
    
    if TYPE_CHECKING:
        from .client import MaubotMatrixClient
        from .loader import BasePluginLoader
        from .plugin_server import PluginWebApp
    
    ROOM_ID = RoomID("") # format is !<random_chars>:beeper.local  locate in beeper by right-clicking a chat -> view source
    RETRIEVE_URL = "" # I spun up an endpoint that retrieves a random fam photo on my behalf. omitting for obvious reasons
    
    class FamPhotoBot(Plugin):
        def __init__(
                self,
                client: MaubotMatrixClient,
                loop: AbstractEventLoop,
                http: ClientSession,
                instance_id: str,
                log: TraceLogger,
                config: BaseProxyConfig | None,
                database: Engine | None,
                webapp: PluginWebApp | None,
                webapp_url: str | None,
                loader: BasePluginLoader,
        ):
            super().__init__(client, loop, http, instance_id, log, config, database, webapp, webapp_url, loader)
            self.is_loop_scheduled = None
    
        @event.on(EventType.ROOM_MESSAGE)
        async def send_message(self, evt: StateEvent) -> None:
            if evt.content.body == "!photo":
                if str(evt.room_id) == str(ROOM_ID):
                    await self.send_photo()
                    if self.is_loop_scheduled is not True:
                        self.is_loop_scheduled = True
                        await self.start_schedule_loop()
                else:
                    self.log.debug("mismatching room id")
    
        async def send_photo(self) -> None:
            self.log.debug("sending photo")
            resp = await self.http.get(RETRIEVE_URL)
            if resp.status == 200:
                data = await resp.read()
                uri = await self.client.upload_media(data)
    
                d = TextMessageEventContent(body="image.jpg", msgtype=MessageType.IMAGE)
                await self.client.send_message_event(ROOM_ID, EventType.ROOM_MESSAGE, d)
    
                content = MediaMessageEventContent(body="image.jpg",
                                                   url=uri,
                                                   msgtype=MessageType.IMAGE,
                                                   info=ImageInfo(
                                                       mimetype="image/jpeg",
                                                       size=43839,
                                                   ), )
                await self.client.send_message(ROOM_ID, content)
    
            else:
                d = TextMessageEventContent(body="fail: " + str(resp.status), msgtype=MessageType.TEXT)
                await self.client.send_message_event(ROOM_ID, EventType.ROOM_MESSAGE, d)
                
        async def start_schedule_loop(self):
            self.log.debug("\n\nstarting schedule for first time\n\n")
            while True:
                await asyncio.sleep(self.seconds_until_noon())
                self.log.debug("woke up from sleep")
                await self.send_photo()
    
        def seconds_until_noon(self):
            now = datetime.datetime.now() + datetime.timedelta(minutes=1)
            noon_today = now.replace(hour=20, minute=0, second=0, microsecond=0)
    
            if now < noon_today:
                time_until_noon = (noon_today - now).total_seconds()
            else:
                tomorrow = now + datetime.timedelta(days=1)
                noon_tomorrow = tomorrow.replace(hour=20, minute=0, second=0, microsecond=0)
                time_until_noon = (noon_tomorrow - now).total_seconds()
            self.log.debug(datetime.datetime.now())
            self.log.debug(time_until_noon)
            return time_until_noon