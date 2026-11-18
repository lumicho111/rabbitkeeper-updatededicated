# 052 小谈顶部安全区修复 · 签名更新包上传

将下面两份文件在 **同一次 GitHub 网页上传提交**中放到此文件夹：

- `rabbit-float-build15-resource-052.part01`（14,680,064 字节）
- `rabbit-float-build15-resource-052.part02`（11,938,770 字节）

在此目录 **Add file → Upload files**，一次选择两个文件，提交到 `main`。不要改名，不要解压。上传 `part02` 将自动触发 `publish-resource-052-signed.yml`，精确校验两段 SHA-256、拼接后原始完整 ZIP、原 APK RSA 公钥签名、manifest 和每个资源哈希；通过后创建正式 `resource-052` Release 并清理暂存文件。

更新包仅修复小谈 iframe 顶部工具栏安全区，已累计包含 051 和 050。不要上传任何原始私钥、p12、签名密码或 `float-android-signing-PRIVATE.zip`。
