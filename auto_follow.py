import asyncio
import json
import os
from typing import Any
import toml  # 导入 toml 库

from bilibili_api import Credential, user, sync
from bilibili_api.user import RelationType
from bilibili_api.exceptions import ResponseCodeException

CONFIG_FILE = "config.toml"

def load_config() -> dict[str, Any] | None:
    """加载配置文件。"""
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            config = toml.load(f)
        # 验证 auto_follow_credential 部分是否存在且包含必要项
        auto_follow_cred = config.get('auto_follow_credential', {})
        if not all(k in auto_follow_cred for k in ['sessdata', 'bili_jct', 'uid']):
            print(f"错误：配置文件 {CONFIG_FILE} 缺少 [auto_follow_credential] 部分或其必要的 sessdata, bili_jct, uid 配置项。")
            return None
        # 验证必要项的值不为空
        if not auto_follow_cred['sessdata'] or not auto_follow_cred['bili_jct'] or auto_follow_cred['uid'] == 0:
            print(f"错误：配置文件 {CONFIG_FILE} 中 [auto_follow_credential] 的 sessdata, bili_jct 或 uid 不能为空或为0。请填充有效值。")
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

def load_followings_from_json(
    filename: str = "followings.json",
) -> list[dict[str, Any]] | None:
    """从 JSON 文件加载关注列表。

    Args:
        filename (str, optional): JSON 文件名. Defaults to "followings.json".

    Returns:
        list[dict[str, Any]] | None: 包含关注用户信息的列表，如果文件不存在或解析失败则返回 None。
    """
    if not os.path.exists(filename):
        print(f"错误：文件 {filename} 不存在。请先运行 main.py 导出关注列表。")
        return None
    try:
        with open(filename, "r", encoding="utf-8") as f:
            followings = json.load(f)
        if not isinstance(followings, list):
            print(f"错误：文件 {filename} 格式不正确，应为 JSON 列表。")
            return None
        print(
            f"成功从 {os.path.abspath(filename)} 加载 {len(followings)} 个待关注用户。"
        )
        return followings
    except json.JSONDecodeError as e:
        print(f"解析 JSON 文件时出错: {e}")
        return None
    except IOError as e:
        print(f"读取文件时出错: {e}")
        return None


async def follow_user(target_uid: int, credential: Credential) -> bool:
    """关注指定 UID 的用户。

    Args:
        target_uid (int): 目标用户的 UID。
        credential (Credential): 操作用户的认证凭证。

    Returns:
        bool: 操作是否成功。
    """
    try:
        u_target = user.User(uid=target_uid, credential=credential)
        await u_target.modify_relation(relation=RelationType.SUBSCRIBE)
        print(f"成功关注用户 UID: {target_uid}")
        return True
    except ResponseCodeException as e:
        # 特殊处理 Bilibili API 可能返回的错误码
        if e.code == 22014:  # 已经关注了该用户
            print(f"用户 UID: {target_uid} 已关注，跳过。")
            return True  # 视为成功，因为目标状态已达成
        elif e.code == -404:  # 用户不存在
            print(f"用户 UID: {target_uid} 不存在，跳过。错误信息: {e}")
            return False
        else:
            print(f"关注用户 UID: {target_uid} 时发生 API 错误: {e}")
            return False
    except Exception as e:
        print(f"关注用户 UID: {target_uid} 时发生未知错误: {e}")
        return False


async def main() -> None:
    """主函数，执行获取凭证、读取列表并自动关注的流程。"""
    print("欢迎使用 Bilibili 自动关注工具！")
    print("将根据 followings.json 文件中的列表进行关注操作。")

    # 加载配置
    config = load_config()
    if not config:
        return

    # 从 [auto_follow_credential] 读取配置
    credential_config: dict[str, str | int] = config.get('auto_follow_credential', {})

    sessdata = credential_config.get('sessdata')
    bili_jct = credential_config.get('bili_jct')
    # buvid3 是可选的，如果配置文件中没有，则为 None
    buvid3 = credential_config.get('buvid3')
    # 自己的 UID 用于验证凭证，而非关注目标
    my_uid = credential_config.get('uid') # UID 现在也在 credential 部分

    # 检查必要的配置是否已加载 (load_config 已处理空值和0值检查)
    if not sessdata or not bili_jct or not my_uid:
        # load_config 内部已经打印了错误信息，这里直接返回
        return

    # 实例化 Credential
    credential = Credential(sessdata=sessdata, bili_jct=bili_jct, buvid3=buvid3)

    print("正在验证凭证并获取用户信息...")
    try:
        # 尝试获取用户信息以验证凭证有效性
        u_self = user.User(uid=int(my_uid), credential=credential)
        user_info = await u_self.get_user_info()
        print(f"凭证有效，当前操作用户: {user_info.get('name', '未知')}")
    except Exception as e:
        print(f"凭证无效或获取用户信息失败: {e}")
        print("请检查您的 SESSDATA、bili_jct、buvid3 和 UID 是否正确且未过期。")
        return

    # 加载关注列表
    followings_to_add = load_followings_from_json()
    if not followings_to_add:
        print("无法加载关注列表，程序退出。")
        return

    # 提取需要关注的 UID 列表
    uids_to_follow: list[int] = []
    for item in followings_to_add:
        if isinstance(item, dict) and "mid" in item:
            try:
                uids_to_follow.append(int(item["mid"]))
            except (ValueError, TypeError):
                print(f"警告：跳过无效的 UID 数据: {item}")
        else:
            print(f"警告：跳过格式不正确的条目: {item}")

    if not uids_to_follow:
        print("没有有效的 UID 需要关注。")
        return

    print(f"准备开始关注 {len(uids_to_follow)} 个用户...")
    successful_follows = 0
    failed_follows = 0
    # 设置关注间隔和重试参数
    follow_interval: int = 3  # 每次关注后的常规等待时间（秒）
    max_retries: int = 10  # 单个用户最大重试次数
    retry_interval: int = 10  # 失败后重试的等待时间（秒）

    for target_uid in uids_to_follow:
        try:
            # 预检查是否已关注
            u_target_check = user.User(uid=target_uid, credential=credential)
            relation_info = await u_target_check.get_relation()
            # attribute=2 表示已关注, attribute=6 表示互相关注
            if relation_info.get("relation").get("attribute") in [2, 6]:
                print(f"用户 UID: {target_uid} 已关注，跳过。")
                successful_follows += 1  # 视为成功
                await asyncio.sleep(0.5)  # 短暂等待避免日志刷屏
                continue  # 处理下一个 UID
        except ResponseCodeException as e:
            if e.code == -404:  # 用户不存在
                print(
                    f"检查关系时发现用户 UID: {target_uid} 不存在，跳过。错误信息: {e}"
                )
                failed_follows += 1
                await asyncio.sleep(0.5)
                continue
            else:
                print(
                    f"检查用户 UID: {target_uid} 关系时发生 API 错误: {e}，将尝试直接关注。"
                )
        except Exception as e:
            print(
                f"检查用户 UID: {target_uid} 关系时发生未知错误: {e}，将尝试直接关注。"
            )

        # 如果未关注或检查出错，则尝试关注和重试
        retries = 0
        while retries <= max_retries:
            print(
                f"尝试关注 UID: {target_uid} (尝试次数: {retries + 1}/{max_retries + 1})..."
            )
            # 注意：follow_user 内部也处理了已关注的情况，但预检查可以减少不必要的调用
            success = await follow_user(target_uid, credential)
            if success:
                # 如果 follow_user 返回 True 但之前检查未发现已关注，则计入成功
                # 如果 follow_user 返回 True 因为内部判断已关注，这里不会重复计数（因为预检查continue了）
                if relation_info.get("attribute") not in [2, 6]:
                    successful_follows += 1
                print(f"等待 {follow_interval} 秒后继续下一个用户...")
                await asyncio.sleep(follow_interval)
                break  # 成功则跳出重试循环，处理下一个UID
            else:
                # follow_user 返回 False 的情况 (非已关注导致的成功)
                retries += 1
                if retries <= max_retries:
                    print(f"关注失败，将在 {retry_interval} 秒后重试...")
                    await asyncio.sleep(retry_interval)
                else:
                    print(
                        f"尝试 {max_retries + 1} 次后关注 UID: {target_uid} 仍然失败，跳过此用户。"
                    )
                    failed_follows += 1
                    # 即使重试失败，也等待常规间隔再处理下一个用户，避免对API造成连续压力
                    print(f"等待 {follow_interval} 秒后继续下一个用户...")
                    await asyncio.sleep(follow_interval)
                    break  # 达到最大重试次数，跳出重试循环

    print("\n关注操作完成！")
    print(f"成功关注: {successful_follows} 个用户")
    print(f"失败或跳过: {failed_follows} 个用户")


if __name__ == "__main__":
    sync(main())
