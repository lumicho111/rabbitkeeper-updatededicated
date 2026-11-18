# 053 累计资源更新 · 签名包上传

请在本文件夹使用 **Add file → Upload files**，把以下两份原始文件**在同一次提交**中上传到 `main`：

- `rabbit-float-build15-resource-053.part01`（14,680,064 字节）
- `rabbit-float-build15-resource-053.part02`（11,945,059 字节）

不得改名、解压、重新压缩。上传 `part02` 后将触发 `publish-resource-053-signed.yml`，先校验两个分片哈希，再无损合并，核验原 APK RSA 签名和 Build 15 基线、版本 053、125 个变更资源及所有哈希；校验通过后发布 `resource-053` Release 并清理暂存文件。

**绝不要上传**私钥 `float-release.p12`、签名密码、`signing.properties` 或 `float-android-signing-PRIVATE.zip`。
