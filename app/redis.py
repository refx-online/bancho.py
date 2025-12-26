from __future__ import annotations

import asyncio
from collections.abc import Callable

from redis.asyncio.client import PubSub

import app
from app.constants.redis import PUBSUB_HANDLER
from app.constants.redis import Message
from app.logging import Ansi
from app.logging import log
from app.objects.player import Player
from app.objects.score import Score


def register_pubsub(channel: str) -> Callable[[PUBSUB_HANDLER], PUBSUB_HANDLER]:
    def decorator(handler: PUBSUB_HANDLER) -> PUBSUB_HANDLER:
        app.state.pubsubs[channel] = handler

        return handler

    return decorator


@register_pubsub("refx:refresh_stats")
async def refresh_stats(payload: str) -> None:
    user_id = int(payload)
    player: Player = app.state.sessions.players.get(id=user_id)
    await player.stats_from_sql_full()

    if not player.restricted:
        app.state.sessions.players.enqueue(app.packets.user_stats(player))

    log("served refresh_stats!", Ansi.GREEN)


@register_pubsub("refx:announce")
async def announce(payload: str) -> None:
    score_id = int(payload)
    score = await Score.from_sql(score_id)
    announce_chan = app.state.sessions.channels.get_by_name("#announce")

    ann = [
        f"\x01ACTION achieved #1 on {score.bmap.embed}",
        f"with {score.acc:.2f}% for {score.pp}pp.",
    ]

    if score.mods:
        ann.insert(1, f"+{score.mods!r}")

    if announce_chan:
        announce_chan.send(" ".join(ann), sender=score.player, to_self=True)

    log("served announce!", Ansi.GREEN)


@register_pubsub("refx:restrict")
async def restrict(payload: str) -> None:
    user_id, reason = payload.split("|")
    player = await app.state.sessions.players.from_cache_or_sql(int(user_id))

    player.restrict(app.state.sessions.bot, str(reason))

    log("served restrict!", Ansi.GREEN)


@register_pubsub("refx:notify")
async def notify(payload: str) -> None:
    user_id, message = payload.split("|")
    player: Player = app.state.sessions.players.get(id=int(user_id))

    player.enqueue(app.packets.notification(str(message)))


async def loop_pubsubs(pubsub: PubSub) -> None:
    while True:
        try:
            message: Message | None = await pubsub.get_message(
                ignore_subscribe_messages=True,
                timeout=1.0,
            )
            if message is not None:
                channel = message["channel"].decode()
                payload = message["data"].decode()

                handler = app.state.pubsubs.get(channel)
                if handler is not None:
                    try:
                        await handler(payload)
                    except:
                        ...

            await asyncio.sleep(0.01)
        except TimeoutError:
            continue


async def initialize_pubsubs() -> None:
    pubsub: PubSub = app.state.services.redis.pubsub()
    await pubsub.subscribe(*app.state.pubsubs.keys())

    pubsub_loop = asyncio.create_task(loop_pubsubs(pubsub))
    app.state.sessions.housekeeping_tasks.add(pubsub_loop)
