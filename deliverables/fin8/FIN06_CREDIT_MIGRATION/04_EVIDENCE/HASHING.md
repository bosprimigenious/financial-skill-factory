# HASHING

- 每个文件计算 SHA-256，写入同目录 `MANIFEST.sha256`（格式：`hash  relative/path`）。
- 校验：`cd <包目录> && shasum -a 256 -c MANIFEST.sha256`
- `MANIFEST.sha256` 自身不入清单（避免自引用）。
- 材料被替换即整包失效，必须重算并留痕。
