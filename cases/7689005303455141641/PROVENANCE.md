# 来源与验收 · 7689005303455141641

- 题目：# 龙鳞券款失败归因与续办引擎
- 来源：Lark Base `OcFPbjoVdaGhwescxD6cPWzBnrd` / table `tblmog3SbccztaSE`（二轮质检记录）
- 下载时间：2026-11-09T17:14:09+08:00
- 记录内实测分：seed 2.1pro 8分； gpt6.1sol high 60分
- 考点字数：3310；题面字数：543
- 材料：18 个文件 / 70013 字节；性质：作者构造的结构化场景数据（须在题面标注合成）

## 文件与 sha256

| 文件 | 字节 | sha256 |
|---|---:|---|
| `00_业务委托.md` | 1465 | `bd87d6747c5dfe8cab64a27fcfb0ec3a89a7a96053d3ab7a1ed517c31c2d6000` |
| `01_归因与续办规程.md` | 8702 | `92fdbfebbf43c800fe257fc69fcb92cf8fefe0814ddaffdeac63c73a2ef434c2` |
| `02_字段协议.json` | 740 | `e1f318e7124c26ff70e396bfbf542a248658c1654c118b86a7470929517241a7` |
| `03_批次与时钟.jsonl` | 2492 | `85b5e27d80d20de3620806c4de32a97bb1109338aaed26a3b0afc554e3150139` |
| `04_成交与分配.jsonl` | 5907 | `54790e072d21799a8a0808e559cc94e66905fe7f143efa4d6fe8d84fb9025bda` |
| `05_指令与生命周期.jsonl` | 4545 | `fc0494f85a2f8936eb4122eefede053bfeadda53921fa0d2a1498bd3ff46ae4b` |
| `06_账户与交收路径.jsonl` | 5215 | `43ca4280d4562823ba00f557170abb2f7948aa86f72c4541a6991ebeec7931d1` |
| `07_库存与资金.jsonl` | 2812 | `9eb202d0a14e1d04957948e0420dfa5f74b0ca1a8085cd735d80a468f5203310` |
| `08_托管与银行回报.jsonl` | 2661 | `683e38dbc6f1316cfd2fe2c4c347391389f93d122b740c84c4c7e73056f7e9b4` |
| `09_关系与依赖.jsonl` | 675 | `918f0ee25760ed9aec38fa1ffcb5edd2d73bba7b0ea475fe64544a3ac0f91567` |
| `10_切点.csv` | 105 | `7091889ecff8aaf144557f4a607e98e55470c69e5637c675d016cf5030f96d26` |
| `11_交付接口.md` | 2803 | `f476d97ce7c8c0746f4701815dc0b476991f90fd45072906f94327b217c719eb` |
| `12_现行引擎.py` | 2367 | `b55d8457802c5dc799f502dd4f465c630473e6662890cbf5fe5bf076b9eafcaa` |
| `13_命令入口.py` | 3097 | `c841aa237852418e0af7439ea694505598ef64eeb4f40e2e3b8430b038da4891` |
| `14_公开检查.py` | 801 | `57f1b71fe97b18be596a8fd39672b2964d039c8292aef02fd6a96ebb55ec9f56` |
| `15_批处理融资与估值.jsonl` | 8500 | `52ed16d93b731ea9559064abdaea499dca9080807aa6a70998ee21d8f1cc79fa` |
| `16_营业日历.csv` | 301 | `8df9144ba72b9e95ee29926df0a66c19921e41fa9e01b324d4ef8bf57bde730a` |
| `作答材料.zip` | 16825 | `a9fc3970283c3cc799e2b44a98b093157455cfccc372e567554aacdfc17a5b83` |

## 状态

- 材料已落盘、可独立支撑任务；尚未产出标准答案与冻结考点的本地产线版本。
- 下一步：按 `PIPELINE.md` G3–G5 冻结考点、生成 GT、逐条判分。
