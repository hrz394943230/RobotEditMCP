这个项目的目标是为 AI Agent 产出几个工具，用于使用 AI 操作 Robot 的草稿和生产配置，最终目标是得到一个 mcp 服务，用户从环境变量获取admin_token 和 base_url来请求robotserver 暴露出来的接口
接口的代码实现在/Users/huruize/PycharmProjects/TFRobotServer/tfrobotserver/api/v1/robot_factory/文件夹内
注意我的目标是让大模型能够操作配置的生成和修改，但是由于配置十分复杂，schema 等内容数据量也很大，所以需要保障 **渐进式的披露**
针对草稿配置和生产配置：
1.能够获取整体配置和局部的配置信息
2.能够创建新的配置信息
3.能够修改配置信息
4.能够删除配置信息

/Users/huruize/PycharmProjects/RobotEditMCP/机器人配置json.txt 这是一个示例配置
