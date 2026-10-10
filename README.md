# FedGuide research page

一版英文的学术项目主页。暖白背景、深蓝强调色，以真实的策略录像与实验结果组织内容。独立于训练代码，纯 HTML / CSS / JavaScript，无构建依赖。

## 本地预览

在本仓库目录运行：

```bash
npm run dev
```

浏览器打开 <http://127.0.0.1:4173>。必须通过 HTTP 访问，直接双击 HTML 无法加载 JSON。默认监听本机回环地址；端口可用 `PORT=4174 npm run dev` 修改。

## 页面内容

- 论文标题、作者、CoRL 2026 Spotlight 信息、论文与代码入口。
- 五种环境的 FedGuide 视频预览。
- 研究动机、可缩放的 SVG 方法示意图及三步方法解释。
- 5 个主环境 + 4 个 hard 环境 × 3 个变体 × 8 / 10 个客户端，共 222 段实际策略录像。hard 环境包括 Reacher-Hard、Hopper-Hard、Walker2D-Hard 和 HalfCheetah-Hard。
- 当前环境的所有 8 / 10 个客户端直接展开，每行三个方法；无需选择客户端。支持逐行播放、滚动时播放可见行、暂停全部、重新开始、0.5× / 1× / 2× 速度。各片段独立循环，不保证长期严格帧同步。
- 九组学习曲线的图例放在坐标区域下方。主环境与 hard 环境分别列出；七种方法的完整结果表支持最终回报与最差种子回报切换。
- 组件消融对照、BibTeX 复制。
- 手机布局、键盘焦点、减少动态效果偏好、离屏预览暂停。

## 编辑与部署

- `dist/index.html`：文案、页面结构、方法图、引用。
- `dist/styles.css`：视觉系统、响应式规则。
- `dist/app.js`：演示与结果交互。
- `dist/demo-data.json`：录像清单、客户端、任务及随机种子。
- `dist/results-data.json`：实验统计数据与计算定义。
- `dist/assets/`：已复制的实际录像、从录像提取的 JPEG 封面、实验曲线。
- `server.mjs`：支持视频 Range 请求的本地静态服务。

静态主机直接托管 `dist/` 即可。内部资源均为相对路径，支持子路径部署。不需要运行 Python 训练环境。录像与封面随静态网页一同发布，录像不预加载，开启滚动播放后仅播放可见行；所有客户端封面始终展示。字体使用 Google Fonts，无法联网时回退系统字体。

`.github/workflows/pages.yml` 在 `main` 分支更新后检查页面资源并发布 `dist/` 到 GitHub Pages。网站地址：<https://hhhhzl.github.io/fedguide-page/>。

## 数据依据与统计口径

作者、题目、会议、链接来自根目录 `README.md` 和 `latex/latex_fedguide/main.tex`。此次没有改动论文或训练文件。

主环境录像采用 `assets/video_selection.json` 的选取结果；hard 环境按同一规则从对应实验的训练记录和录像重新选择，全部为第 100 轮。Reacher-Hard 来自 `reacher/ablation/C`，其余来自对应的 `*_hard` 目录。每个环境、每个方法按最后 10 轮的环境平均评估回报选择最佳种子。它们是定性展示，不代表跨种子均值，也不是所播放单个 episode 的回报。MetaWorld 的客户端任务名称来自现有环境素材。当前 HalfCheetah 元数据有 64 个客户端，而所保存的演示只有 8 个；页面沿用录像清单，不把当前配置套到旧录像上。

实验数字由现有 `metrics/*/training_history.pkl` 重新计算，和论文 `tex/results_table.tex` 的四舍五入值一致：5 个主环境 + 4 个 hard 环境 × 7 个方法，每种组合均有 5 个种子、100 轮。

- **Final return**：先对每个种子的最后 10 轮 client-average return 求均值，再报告 5 个种子的均值 ± 样本标准差（SD）。
- **Worst-seed return**：上述 5 个种子结果中的最小值。
- **曲线**：通过 `scripts/export_curves.py` 从原始实验记录重新导出，复用研究代码的五种子聚合、平滑及标准误计算，仅改变图例位置和版式。均值 ± 1 标准误（SE）；平滑方式见 JSON 的 `metadata.curveDefinition`。
- 主实验及 hard 实验每环境 8 个客户端，MetaWorld10 为 10 个。所有环境 8 个专家。
- FedGuide 在 5 个主任务中的 4 个取得最高平均最终回报；Reacher 上 FedGuide-P 略高。HalfCheetah 的 2.10× 对比是 FedGuide 与最强外部基线 FedKL，不是与 FedGuide-P 的比较。

Hard 环境中，FedGuide 在 Walker2D-Hard 和 HalfCheetah-Hard 的平均最终回报最高；Reacher-Hard 由 FedGuide-P 领先，Hopper-Hard 由 FedRL 领先。Reacher-Hard 曲线采用对称对数纵轴，以容纳包括负值在内的大幅回报跨度。

原论文表注将 W 写为 worst-round，但计算脚本取 worst-seed；曲线图注将误差写为 SD，但绘图脚本计算 SE。网页按实际计算方式标注，未修改源论文。

重新生成曲线需要原始 FedGuide 研究仓库、实验记录、NumPy 和 Matplotlib。若本网页仓库不在研究仓库内，可指定来源目录：

```bash
FEDGUIDE_SOURCE_ROOT=/path/to/fedguide python3 scripts/export_curves.py --update-results
```

Hard 录像与封面的可复现导出需要 ffmpeg：

```bash
FEDGUIDE_SOURCE_ROOT=/path/to/fedguide FFMPEG=/path/to/ffmpeg python3 scripts/export_hard_demos.py
```

## 验证

- `node --check dist/app.js` 与 `node --check server.mjs`。
- 所有 222 段录像和对应封面、9 张环境封面、9 组学习曲线均存在；主环境源路径与种子符合原始清单，hard 环境对应其原始训练记录与录像。
- 本地页面返回 HTTP 200；浏览器实际播放三路 H.264 视频，均达到可播放状态。
- `python3 scripts/check_site.py` 检查本地页面资源和所有客户端媒体。
- 浏览器验证 8 / 10 行客户端全部展开、逐行播放及倍速切换、完整结果表及统计口径切换、BibTeX 复制。
- 390 px 手机宽度无页面横向溢出；横向环境条、方法图和宽表格保留各自滚动区域。
- 检查到的浏览器控制台错误 / 警告为 0。

发布配置为 GitHub Pages，使用 GitHub Actions 自动部署。
