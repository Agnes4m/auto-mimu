import asyncio
import random
from typing import Optional

from pydantic import Field

from gsuid_core.aps import scheduler
from gsuid_core.bot import Bot
from gsuid_core.gss import gss
from gsuid_core.logger import logger
from gsuid_core.models import Event
from gsuid_core.sv import SV
from gsuid_core.utils.database.base_models import Bind, User
from gsuid_core.utils.database.models import GsBind
from gsuid_core.utils.error_reply import UID_HINT

from .miuitask import main
from .utils.config import Account, Config


class MinuBind(Bind, table=True):
    uid: str = Field(default="10001", title="小米ID")


class MinuUser(User, table=True):
    uid: str = Field(default="10001", title="小米ID")
    password: str = Field(default="123456", title="密码")
    ck: str = Field(default="", title="cookie")


sv_sign = SV("小米签到")


@sv_sign.on_fullmatch("小米签到")
async def get_sign_func(bot: Bot, ev: Event):
    await bot.logger.info("[签到]QQ号: {}".format(ev.user_id))
    ex = False
    try:
        minu_uid = await MinuBind.get_uid_by_game(ev.user_id, ev.bot_id)
        minu_password = await MinuUser.get_user_stoken_by_user_id(ev.user_id, ev.bot_id)
        minu_ck = await MinuUser.get_user_cookie_by_user_id(ev.user_id, ev.bot_id)
        if minu_uid and minu_ck and minu_password:
            # 配置文件
            ex = True
            minu_config = Config(
                accounts=[
                    Account(uid=minu_uid, password=minu_password, cookies=minu_ck)
                ]
            )
        else:
            minu_config = Config()
    except Exception:
        minu_config = Config()
    finally:
        await main(minu_config, bot)
    if ex is False:
        if data is None:
            data = ConfigManager.data_obj


async def send_daily_sign():
    logger.info("开始执行[每日全部签到]")
    # 执行签到 并获得推送消息
    result = await daily_sign()
    private_msg_list = result["private_msg_list"]
    group_msg_list = result["group_msg_list"]
    logger.info("[每日全部签到]完成")

    # 执行私聊推送
    for qid in private_msg_list:
        try:
            for bot_id in gss.active_bot:
                for single in private_msg_list[qid]:
                    await gss.active_bot[bot_id].target_send(
                        single["msg"], "direct", qid, single["bot_id"], "", ""
                    )
        except Exception as e:
            logger.warning(f"[每日全部签到] QQ {qid} 私聊推送失败!错误信息:{e}")
        await asyncio.sleep(0.5)
    logger.info("[每日全部签到]私聊推送完成")

    # 执行群聊推送
    for gid in group_msg_list:
        # 根据succee数判断是否为简洁推送
        if group_msg_list[gid]["success"] >= 0:
            report = (
                "以下为签到失败报告：{}".format(group_msg_list[gid]["push_message"])
                if group_msg_list[gid]["push_message"] != ""
                else ""
            )
            msg_title = "今日自动签到已完成！\n本群共签到成功{}人，共签到失败{}人。{}".format(
                group_msg_list[gid]["success"],
                group_msg_list[gid]["failed"],
                report,
            )
        else:
            msg_title = group_msg_list[gid]["push_message"]
        # 发送群消息
        try:
            for bot_id in gss.active_bot:
                await gss.active_bot[bot_id].target_send(
                    msg_title,
                    "group",
                    gid,
                    group_msg_list[gid]["bot_id"],
                    "",
                    "",
                )
        except Exception as e:
            logger.warning(f"[每日全部签到]群 {gid} 推送失败!错误信息:{e}")
        await asyncio.sleep(0.5 + random.randint(1, 3))
    logger.info("[每日全部签到]群聊推送完成")
