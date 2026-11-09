# 实例库（9 个金融案例）

来源：Lark Base `OcFPbjoVdaGhwescxD6cPWzBnrd` / table `tblmog3SbccztaSE`（平台二轮质检记录，金融 51 条中的 9 条）。
更新时间：2026-11-09T17:15:48+08:00

判据：①金融 ②材料+标准答案+考点齐 ③豆包 2.1 Pro 实测 ≤50（即难度达标）④材料体量可控、可逐条复算。

| 题目 ID | 材料 | 文件 | 体量 | 记录内实测分 | 性质 | 状态 |
|---|---|---:|---:|---|---|---|
| `7689004886126038822` | 公开文件 | 5 | 4197 KB | gpt 38.5分，豆包2.1pro自测 38分 | public | MATERIAL_INGESTED |
| `7682696962462060297` | 结构化场景 | 19 | 1127 KB | gpt6.1sol high 10分；  豆包2.1pro 13分 | synthetic | MATERIAL_INGESTED |
| `7689005308652818202` | 结构化场景 | 16 | 396 KB | seed 2.1pro 38分； gpt6.1sol high 60分 | synthetic | MATERIAL_INGESTED |
| `7682697017533435698` | 结构化场景 | 38 | 74 KB | 本地gpt得分65.5,豆包不达标 | synthetic | MATERIAL_INGESTED |
| `7689005303455141641` | 结构化场景 | 18 | 68 KB | seed 2.1pro 8分； gpt6.1sol high 60分 | synthetic | MATERIAL_INGESTED |
| `7689004928191450926` | 结构化场景 | 20 | 59 KB | 豆包2.1pro 42分。 GPT6.1sol high 58分 | synthetic | MATERIAL_INGESTED |
| `7682696205114576686` | 结构化场景 | 17 | 48 KB | seed 2.1pro 36分； gpt6.1sol high 55分 | synthetic | MATERIAL_INGESTED |
| `7699775475468144393` | 结构化场景 | 10 | 26 KB | 0/100（严格档：12 组判据 0 组整组闭合；单判点命中率 50.0%＝77/154 原子。同题面隔离盲做两卷同为  | synthetic | MATERIAL_INGESTED |
| `7689005313907642138` | 结构化场景 | 12 | 21 KB | 豆包 2.1 Pro 一次性实测卷（2026-10-28 由专家本人运行，人工计时 31 分钟，交付 13 个工作表、判 | synthetic | MATERIAL_INGESTED |

## 每个实例的内容

```text
cases/<题目 ID>/
  case.json        # 元数据（行业/技能待平台词条确认/实测分/材料清单）
  PROVENANCE.md    # 来源、下载时间、逐文件 sha256、状态
  materials/       # 原始附件（未改写）
```

## 扫描结果

`fsf scan` 逐案结果见 `out/<id>/scan-report.md`：

| 题目 ID | verdict | fails | warns |
|---|---|---:|---:|
| 7689005313907642138 | PASS | 0 | 0 |
| 7689004886126038822 | PASS | 0 | 0 |
| 7699775475468144393 | PASS | 0 | 0 |
| 7682697017533435698 | WARN | 0 | 2 |
| 其余 5 个 | WARN | 0 | 7–11 |

WARN 不是材料错误：多为 `.jsonl`/`.pfr` 等扩展名不在白名单、缺少 `checks` 断言等提示。

## 与已完成的题包的关系

- `7689005313907642138` 已有完整题包（`packs/7689005313907642138/`），但**该题包的材料是重建版**，
  原件在这里的 `materials/`。差异与待办见 `packs/7689005313907642138/04_evidence/MATERIAL-DIVERGENCE.md`。
- 其余 8 个只有材料与元数据，尚未冻结考点、未生成 GT、未判分。

## 为什么不直接 pack

`source_type: synthetic` 的案例禁止进入 `packs/`（`src/fsf/pack.py` 的硬门槛）。
这 8 个是平台上的"场景构造"任务，材料为作者构造的结构化数据；要继续推进须先按 `PIPELINE.md` G3 冻结考点，
并在题面标注合成数据后，才谈是否改判 `scenario` 并放宽闸门。
