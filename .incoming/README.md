# 051 已签名更新包上传区（每文件 25 MB 限制）

请将下列两份文件**在同一次 GitHub 网页上传提交中**放入本文件夹：

- `rabbit-float-build15-resource-051.part01`（14,680,064 字节）
- `rabbit-float-build15-resource-051.part02`（11,938,327 字节）

在本文件夹点击 **Add file → Upload files**，一次选择上述两个文件，点击 **Commit changes** 提交到 `main`。不得重命名、改内容或者直接解压。

上传 part02 的提交会触发 `publish-resource-051-signed.yml`：严格验证两段原始 SHA-256 和字节数，合并为原来的 `rabbit-float-build15-resource-051.zip`，核验原 APK 公钥的 RSA 签名、manifest、每个资源哈希、Build 15 基线及 051 序号，再作为 `resource-051` Release 发布。成功后自动清理暂存段。

绝不要上传 `float-release.p12`、`signing.properties` 或 `float-android-signing-PRIVATE.zip` 等私钥材料。
