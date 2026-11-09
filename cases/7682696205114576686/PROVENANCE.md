# 来源与验收 · 7682696205114576686

- 题目：龙鳞经纪运营部需要恢复一段停用的客户收费引擎，在 OPEN、MID、CLOSE 三个知识切点重建订单接收时点、账户权限、
- 来源：Lark Base `OcFPbjoVdaGhwescxD6cPWzBnrd` / table `tblmog3SbccztaSE`（二轮质检记录）
- 下载时间：2026-11-09T17:14:09+08:00
- 记录内实测分：seed 2.1pro 36分； gpt6.1sol high 55分
- 考点字数：3741；题面字数：457
- 材料：17 个文件 / 50017 字节；性质：作者构造的结构化场景数据（须在题面标注合成）

## 文件与 sha256

| 文件 | 字节 | sha256 |
|---|---:|---|
| `00_业务委托.md` | 1809 | `7f79d535d1e86884ec5c04ea4b42896fb804bf915dad0a7b58d2b6817df5a39d` |
| `01_费用与事件规程.md` | 7148 | `0d934e5b58a6f31582375c5e3a1bbe19fa94379eb1dc6fa199126ad9baf3dddc` |
| `02_字段协议.json` | 613 | `81cad114fae8fe28fd4f635770ee75037a67fd609ab5db39aa407d80baaf3464` |
| `03_知识切点.csv` | 178 | `10c6e7ca2cf5356b683ab7d813b886e6733602630ad2fd86873adc76c876b82f` |
| `04_来源时钟.csv` | 678 | `75821f224410923f5b317d3cef91a6b67166570ace1383f179c4f811ed95e757` |
| `05_批次账本.jsonl` | 1768 | `fe9d4bf925c3d607baaac593675d126dd73b4a6ea873e272d98ebdbf89c5919e` |
| `06_账户权限.jsonl` | 2017 | `22e6d5a69abe60ed4f60c0ac8ecaa9042a3ac48d73648b872978dc1f0ccf2980` |
| `07_订单事件.jsonl` | 4233 | `0d26b75527f8ad18683a92b5f82d0d05db3e76ca0e8efd8b20f393ab9c0c2c94` |
| `08_成交事件.jsonl` | 4590 | `d7485f025604215e434b5fc3dbb82077ea3ba2b3c97c0e5196305c1b73aad2e4` |
| `09_分配事件.jsonl` | 4386 | `680642aec80d39a1871a7e5c172627e610509d940577ee1faf2b8bbc2a6955f8` |
| `10_费率与汇率.jsonl` | 1832 | `0fb5b3bd32f7dfeb0aad5a9f767b8e77ff4b54366d6d33507c16ffb1700c2d9e` |
| `11_费用账本与差错.jsonl` | 2766 | `6d71ae41da093b07ee8b68f77182a1f3239ab19a5e193ecb9e9735f126918d48` |
| `12_现行引擎.py` | 335 | `5a28c3c3e8d29204fd6afee2200126cdca3ec74935dc465cc5487707c0bf1a1a` |
| `13_公开检查.py` | 1724 | `97e1a99d75a7c87df62234da402eba35ad16bf1fd82c367a6376c91deea548a0` |
| `14_交付接口.md` | 1741 | `810252178491785136fc06bd216a42a0802bb32828a9ed841181f08cbe06de23` |
| `15_命令入口.py` | 849 | `f02a9c2d282b16e1bd8ce0f08f5b20d88ac03ba22da803b996e3f7aaf9f55617` |
| `作答材料.zip` | 13350 | `69c8fca2da4a9a6dc806a96c5197ce67b09fe6b50d69eac3bb8415628633d922` |

## 状态

- 材料已落盘、可独立支撑任务；尚未产出标准答案与冻结考点的本地产线版本。
- 下一步：按 `PIPELINE.md` G3–G5 冻结考点、生成 GT、逐条判分。
