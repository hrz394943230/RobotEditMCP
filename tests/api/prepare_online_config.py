"""测试数据准备脚本 - 创建线上配置

这个脚本用于准备测试用的线上配置数据。
需要在有完整环境的系统中运行（支持 BRAIN、DRIVE、CHAIN 等场景）。

使用方法:
    python tests/api/prepare_online_config.py

注意:
    - 需要设置正确的环境变量 (.env 文件)
    - 将创建多个草稿配置并发布到线上环境
    - 测试完成后可以手动清理或保留供后续测试使用
"""

import os
import sys

# 添加项目根目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

import logging

from roboteditmcp.client import RobotClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_online_config():
    """创建一个完整的 ROBOT 配置并发布到线上环境。

    Returns:
        int: 创建的线上配置 ID，如果失败则返回 None
    """
    client = RobotClient()

    # 1. 创建 DOC_STORE (drive)
    logger.info("创建 DOC_STORE (drive)...")
    try:
        doc_store_response = client.draft.create_draft(
            scene="DOC_STORE",
            name="PostgresDocStoreDraft",
            setting_name="test_online_doc_store",
            config={
                "name": "TestOnlineDocStore",
                "description": "Test document store for online config testing"
            }
        )
        doc_store_id = doc_store_response.get("settingId")
        logger.info(f"  DOC_STORE created: ID={doc_store_id}")
    except Exception as e:
        logger.error(f"  DOC_STORE 创建失败: {e}")
        return None

    # 2. 创建 LLM provider
    logger.info("创建 LLM provider...")
    try:
        llm_response = client.draft.create_draft(
            scene="LLM",
            name="GPT草稿",
            setting_name="test_online_llm",
            config={
                "input_price": 0,
                "output_price": 0,
                "name": "test-gpt-model",
                "context_window": 4096,
                "system_msg_prompt": [],
                "before_input_msg_prompt": [],
                "after_input_msg_prompt": [],
                "after_intermediate_msg_prompt": [],
                "tool_filter": None,
                "frequency_penalty": 0,
                "max_tokens": 1024,
                "top_p": 1,
                "n": 1,
                "presence_penalty": 0,
                "temperature": 0.7,
                "openai_api_key": "test-key-not-used",
                "proxy_host": None,
                "proxy_port": None,
                "response_format": {"type": "text"},
                "stream": False
            }
        )
        llm_id = llm_response.get("settingId")
        logger.info(f"  LLM created: ID={llm_id}")
    except Exception as e:
        logger.error(f"  LLM 创建失败: {e}")
        return None

    # 3. 创建 CHAIN (for BRAIN)
    logger.info("创建 CHAIN...")
    try:
        chain_response = client.draft.create_draft(
            scene="CHAIN",
            name="ChainDraft",
            setting_name="test_online_chain",
            config={
                "llm": {
                    "setting_id": llm_id,
                    "category": "Draft"
                },
                "max_iterations": 5,
                "max_tokens": 4096,
                "tool_response_instructions": "Stop when done.",
                "enable_thinking": False,
                "enable_test_mode": True
            }
        )
        chain_id = chain_response.get("settingId")
        logger.info(f"  CHAIN created: ID={chain_id}")
    except Exception as e:
        logger.error(f"  CHAIN 创建失败: {e}")
        logger.info("  注意: CHAIN 场景可能在此环境中不可用，尝试使用 PROMPT_TEMPLATE 作为 brain")
        # 使用 LLM 直接作为 brain
        chain_id = llm_id

    # 4. 创建 BRAIN
    logger.info("创建 BRAIN...")
    try:
        brain_response = client.draft.create_draft(
            scene="BRAIN",
            name="RobotBrainDraftSetting",
            setting_name="test_online_brain",
            config={
                "chain": {
                    "setting_id": chain_id,
                    "category": "Draft"
                },
                "memory": None,
                "memory_chunk_size": 2048
            }
        )
        brain_id = brain_response.get("settingId")
        logger.info(f"  BRAIN created: ID={brain_id}")
    except Exception as e:
        logger.error(f"  BRAIN 创建失败: {e}")
        logger.info("  尝试使用 LLM 直接作为 brain")
        # 使用 LLM 直接作为 brain
        brain_id = llm_id

    # 5. 创建 ROBOT
    logger.info("创建 ROBOT...")
    try:
        robot_response = client.draft.create_draft(
            scene="ROBOT",
            name="RobotDraftSetting",
            setting_name="test_online_robot",
            config={
                "nick_name": "TestOnlineRobot",
                "brain": {
                    "setting_id": brain_id,
                    "category": "Draft"
                },
                "drive": {
                    "setting_id": doc_store_id,
                    "category": "Draft"
                },
                "lock_timeout": 1800,
                "wait_processing_timeout": 20
            }
        )
        robot_id = robot_response.get("settingId")
        logger.info(f"  ROBOT created: ID={robot_id}")
    except Exception as e:
        logger.error(f"  ROBOT 创建失败: {e}")
        return None

    # 6. 发布到线上环境
    logger.info("发布 ROBOT 到线上环境...")
    try:
        release_response = client.draft.release_draft()
        logger.info(f"  Release response: {release_response}")
    except Exception as e:
        logger.error(f"  发布失败: {e}")
        logger.info("  清理已创建的草稿...")
        # Cleanup created drafts
        try:
            if robot_id:
                client.draft.delete_draft(robot_id)
            if brain_id:
                client.draft.delete_draft(brain_id)
            if chain_id and chain_id != llm_id:
                client.draft.delete_draft(chain_id)
            if llm_id:
                client.draft.delete_draft(llm_id)
            if doc_store_id:
                client.draft.delete_draft(doc_store_id)
            logger.info("  清理完成")
        except Exception:
            pass
        return None

    # 7. 获取线上配置
    logger.info("获取线上配置...")
    try:
        online_configs = client.online.list_online_configs()
        logger.info(f"  找到 {len(online_configs)} 个线上配置")

        # 找到我们刚创建的配置
        for config in online_configs:
            if "test_online" in config.get("settingName", ""):
                config_id = config.get("settingId")
                logger.info(f"  找到测试线上配置: ID={config_id}, Name={config.get('settingName')}")
                return config_id
    except Exception as e:
        logger.error(f"  获取线上配置失败: {e}")

    return None


if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("测试数据准备 - 创建线上配置")
    logger.info("=" * 60)

    config_id = create_online_config()

    if config_id:
        logger.info("=" * 60)
        logger.info(f"✅ 成功! 线上配置 ID: {config_id}")
        logger.info("=" * 60)
        logger.info("现在可以运行 test_get_online_config 测试了")
    else:
        logger.error("=" * 60)
        logger.error("❌ 失败! 无法创建线上配置")
        logger.error("=" * 60)
        logger.error("可能的原因:")
        logger.error("  1. 环境不支持所需的场景类型 (BRAIN, CHAIN, DRIVE 等)")
        logger.error("  2. 环境变量配置不正确")
        logger.error("  3. API 权限不足")
        logger.error("")
        logger.error("建议:")
        logger.error("  1. 在支持完整场景的环境中运行此脚本")
        logger.error("  2. 或者使用现有线上配置进行测试")
        logger.error("  3. 或者跳过需要线上配置的测试")
