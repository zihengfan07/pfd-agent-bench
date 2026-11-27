# PFD-Agent & PFD-Bench

**[Project website](https://zihengfan07.github.io/pfd-agent-bench/)** · **[中文](https://zihengfan07.github.io/pfd-agent-bench/?lang=zh)**

From Process Graphs to Multi-Sheet CAD: Generation and Structural Assessment of Process Flow Diagrams.

Ziheng Fan · Ziyang Fan · Xiaohuai Cao · [Qibing Ren](https://renqibing.github.io/)  
School of Artificial Intelligence, Shanghai Jiao Tong University

## What is included

- Bilingual project homepage with language switching and interactive CAD navigation.
- A 75-second, 1080p CAD-led walkthrough with English / Chinese narration, chapter navigation, transcript and downloadable case evidence.
- Three source-grounded challenge figures, each in English and Chinese.
- Five complete supplied review cases: 111 individual CAD sheets plus five package masters, XML inputs, DWG / DXF / PDF files, previews, metadata, and an offline review application.
- Nine-configuration benchmark summary on 50 tasks per configuration (450 scored artifacts). The frozen evaluation corpus and newer review gallery are versioned separately.
- The original five-case archive in `resources/PFD-five-case-review.zip`.

The paper and supplementary manuscript are not included in this release.

## Preview locally

Run `python -m http.server 8879` in this directory, then open `http://127.0.0.1:8879/`.
The site has no backend, build step, external font dependency, tracking, or API key.
The supplied complete review workspace is currently Chinese-language; the project homepage and challenge figures support both languages.
Review notes stay in the visitor's browser until exported; the website does not send expert opinions to the authors.

## Challenge-figure provenance

`assets/challenges/provenance.json` records source hashes and the exact case, streams, and ports.
Original previews are embedded unchanged inside SVG viewports. Graph layouts and circles are explanatory annotations derived from supplied source/layout metadata, not independent Bench detections.
Install `tools/requirements.txt`, then run `python tools/build_challenges.py` to regenerate the figures from the included review data.

## Interpreting the benchmark

All displayed dimensions are on a 0–100 scale. Each score includes its valid case count. The average uses cases with all four dimensions available. It is not the arithmetic average of the displayed column means.
Scores describe the frozen CAD evaluation protocol, not engineering certification or an expert acceptance rate.

## Sources and licenses

The website/reviewer code uses Apache-2.0; see `LICENSE` and `NOTICE`. Case data retain their original source conditions; the code license does not relicense XML models, drawings, or derived case assets. See `review/DATA_SOURCES.md` and `resources/CASE_SOURCES.txt` for the per-case records. In particular, HARD_A07 carries a non-commercial condition.

Required HARD_A07 source citation: James Scott and Thomas A. Adams II, “Biomass-Gas-and-Nuclear-To-Liquids (BGNTL) Processes Part I: Model Development and Simulation,” The Canadian Journal of Chemical Engineering, 2018, as identified by the [source distribution page](https://psecommunity.org/materials/calculationfiles). Preserve this attribution when reusing the case.

## 发布内容

本仓库公开中英文项目网页、难点图、全部五案例审阅资料及结果汇总。原始案例文件保持不变，原许可和来源记录随包保留。论文 PDF 暂不公开。
首页可切换中文与英文；完整离线审阅器目前为中文。五案例展示版本与冻结评分数据版本不同，网页不将历史分数直接赋予某一展示图纸，也不把评分解释为工程验收。

## Workflow demo

[Watch the demo](https://zihengfan07.github.io/pfd-agent-bench/#demo). The video replays saved artifacts and illustrates the method stages; it is not a live execution recording. It follows the historical 33-sheet HARD_A06 package, whose XML and master DXF hashes match the frozen r010 receipt p0119. Four case scores are 98.99 / 88.28 / 72.24 / 98.27. The source was a saved-evidence recovery marked `draft_with_issues`. The newer 34-sheet review gallery remains a separate artifact version.

The redesigned video follows native CAD geometry from a mapped input connection through layered drawing assembly, a cross-sheet stream, recorded Bench objects and four case scores. It includes English / Chinese synthesized narration and bilingual short captions. Changing narration preserves the playback position. Optional full WebVTT transcripts, case evidence and file hashes are under `assets/demo/`. Reproduction instructions are in `assets/demo/README.txt`; the renderer is `tools/build_demo_v2.py`. No model API call is made to render this presentation. The first video remains archived as `pfd-workflow-demo.mp4`.
