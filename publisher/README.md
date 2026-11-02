# 兔版float 自动更新发布

本仓库只用于发布程序资源，不存放聊天、角色资料、API 密钥或 APK 签名私钥。

## 发布流程

维护者在本地完成代码修改、构建和检查，用原 APK 私有密钥生成匹配基线的签名资源 ZIP。把 ZIP 分为 base64 文本块，连同更新说明和 `publisher/request.json` 一次性提交到 main。仓库工作流会还原文件、检查哈希与 APK 公钥签名、核对文件名和签名清单的 build/sequence，然后先创建草稿、上传附件、确认上传哈希，最后才公开发布。

正式请求使用 `resource-003` 这样的递增标签，并设 `release.draft=false`。原生版本不变时持续生成 build6 的资源包；若修改原生能力需另发 APK 与新基线。正式资源包不可反复换同名文件。已存在且哈希一致的发布可重试，哈希不同则停止，避免覆盖。

`publisher/public-key.pem` 只是公开验签公钥，可以公开。私钥、signing.properties、个人备份永远不要提交。工作流使用 GitHub 为当前仓库任务提供的临时凭证，不需要单独保存个人 Token。

## 当前连接验证

初始请求为 `publisher-check-20261102`，始终保持草稿，复用已发布的 002 验证包，仅验证创建草稿与上传附件，不作为新更新推送。

## 文件约定

- `.github/workflows/publish-updates.yml`：只在 main 的发布文件变化时运行，单队列，不取消正在上传的版本。
- `publisher/publish.py`：固定仓库的发布逻辑，不执行请求数据中的代码。
- `publisher/request.json`：标题、说明、草稿标记、附件大小/哈希与有序分块路径。
- `publisher/payloads/<发布标识>/<块编号>.b64`：签名 ZIP 的分块文本，建议每个解码后最多 384 KiB。

应用检查的是公开 Releases，草稿和预发布不会出现。停止自动发布可禁用该工作流；不要通过变更小手机内数据来关闭发布流程。
