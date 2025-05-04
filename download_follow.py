import asyncio
import json
import os
from typing import Any
import toml  # 导入 toml 库

from bilibili_api import Credential, user, sync

CONFIG_FILE = "config.toml"

def load_config() -> dict[str, Any] | None:
    """加载配置文件。"""
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            config = toml.load(f)
        # 验证 download_credential 部分是否存在且包含必要项
        download_cred = config.get('download_credential', {})
        if not all(k in download_cred for k in ['sessdata', 'bili_jct', 'uid']):
            print(f"错误：配置文件 {CONFIG_FILE} 缺少 [download_credential] 部分或其必要的 sessdata, bili_jct, uid 配置项。")
            return None
        # 验证必要项的值不为空
        if not download_cred['sessdata'] or not download_cred['bili_jct'] or download_cred['uid'] == 0:
            print(f"错误：配置文件 {CONFIG_FILE} 中 [download_credential] 的 sessdata, bili_jct 或 uid 不能为空或为0。请填充有效值。")
            return None
        print(f"成功从 {os.path.abspath(CONFIG_FILE)} 加载配置。")
        return config
    except FileNotFoundError:
        print(f"错误：配置文件 {CONFIG_FILE} 未找到。请确保配置文件存在于脚本同级目录。")
        return None
    except toml.TomlDecodeError as e:
        print(f"错误：解析配置文件 {CONFIG_FILE} 失败: {e}")
        return None
    except Exception as e:
        print(f"加载配置文件时发生未知错误: {e}")
        return None


async def get_all_followings(
    uid: str | int, credential: Credential
) -> list[dict[str, Any]]:
    """获取用户的所有关注列表。

    Args:
        credential (Credential): 用户的认证凭证。

    Returns:
        List[Dict[str, Any]]: 包含所有关注用户信息的列表。
    """

    # 重新实例化 User 以获取关注列表
    u = user.User(uid=int(uid), credential=credential)
    followings: list[dict[str, Any]] = []
    page_num = 1
    while True:
        try:
            res = await u.get_followings(pn=page_num)
            if not res or not res.get("list"):
                break
            followings.extend(res["list"])
            print(f"已获取第 {page_num} 页关注列表，共 {len(res['list'])} 个用户...")
            if len(followings) >= res.get("total", 0):
                break
            page_num += 1
            await asyncio.sleep(1)  # 避免请求过快
        except Exception as e:
            print(f"获取关注列表时出错: {e}")
            break
    return followings


def save_followings_to_json(
    followings: list[dict[str, Any]], filename: str = "followings.json"
) -> None:
    """将关注列表保存到 JSON 文件。

    Args:
        followings (List[Dict[str, Any]]): 关注列表数据。
        filename (str, optional): 保存的文件名. Defaults to "followings.json".
    """
    try:
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(followings, f, ensure_ascii=False, indent=4)
        print(f"关注列表已成功导出到 {os.path.abspath(filename)}")
    except IOError as e:
        print(f"保存文件时出错: {e}")


async def main() -> None:
    """主函数，执行获取和导出关注列表的流程。"""
    print("欢迎使用 Bilibili 关注列表导出工具！")

    # 加载配置
    config = load_config()
    if not config:
        return

    # 从 [download_credential] 读取配置
    credential_config: dict[str, str | int] = config.get('download_credential', {})

    sessdata = credential_config.get('sessdata')
    bili_jct = credential_config.get('bili_jct')
    # buvid3 是可选的，如果配置文件中没有，则为 None
    buvid3 = credential_config.get('buvid3')
    uid = credential_config.get('uid') # UID 现在也在 credential 部分

    # 检查必要的配置是否已加载 (load_config 已处理空值和0值检查)
    if not sessdata or not bili_jct or not uid:
        # load_config 内部已经打印了错误信息，这里直接返回
        return

    # 实例化 Credential
    credential = Credential(sessdata=sessdata, bili_jct=bili_jct, buvid3=buvid3)

    print("正在验证凭证并获取用户信息...")
    try:
        # 尝试获取用户信息以验证凭证有效性
        u_self = user.User(uid=int(uid), credential=credential)
        user_info = await u_self.get_user_info()
        print(f"凭证有效，当前用户: {user_info.get('name', '未知')}")
    except Exception as e:
        print(f"凭证无效或获取用户信息失败: {e}")
        print("请检查您的 SESSDATA 和 bili_jct 是否正确且未过期。")
        return

    print("开始获取关注列表...")
    followings_list = await get_all_followings(uid, credential)

    if followings_list:
        print(f"共获取到 {len(followings_list)} 个关注用户。")
        save_followings_to_json(followings_list)
    else:
        print("未能获取到关注列表，或关注列表为空。")


if __name__ == "__main__":
    # 使用 sync() 来运行异步的 main 函数
    # 如果在不支持 top-level await 的环境或者需要兼容旧代码，可以使用 asyncio.run()
    # 但 bilibili-api 推荐使用 sync()
    sync(main())
