# FedGuide Research Page

The academic project website for **FedGuide: Diffusion Prior Alignment and Value Baseline Guidance for Heterogeneous Federated Reinforcement Learning**, featuring recorded policy demonstrations, learning curves, and experimental results.

Built with plain HTML, CSS, and JavaScript, independently of the training code. No build step is required.

**[Live website](https://hhhhzl.github.io/fedguide-page/)** · **[Research code](https://github.com/hhhhzl/fedguide)** · **[Paper](https://arxiv.org/abs/2609.18964)**

## Local Preview

From this repository, run:

```bash
npm run dev
```

Open [http://127.0.0.1:4173](http://127.0.0.1:4173). Serve the page over HTTP; opening the HTML file directly will prevent the JSON data from loading. The server listens on the local loopback interface by default. To use another port, run `PORT=4174 npm run dev`.

## Website Contents

- Paper title, authors, CoRL 2026 Spotlight information, and links to the paper and research code.
- FedGuide video previews across five main environments.
- Research motivation, an SVG framework diagram, and a three-step explanation of the method.
- **222 recorded policy demonstrations** across five main environments and four hard environments, with three method variants and eight clients per environment (ten for MetaWorld10). The hard suite includes Reacher-Hard, Hopper-Hard, Walker2D-Hard, and HalfCheetah-Hard.
- All clients in the selected environment are expanded, with three methods per row. Controls support row playback, playback of visible rows while scrolling, pause all, restart, and 0.5× / 1× / 2× speed. Clips loop independently and are not guaranteed to remain frame-synchronized.
- Nine sets of learning curves with legends below the plot area. Main and hard environments are grouped separately. The complete seven-method results table supports final-return and worst-seed-return views.
- A component ablation comparison and a copyable BibTeX citation.
- Mobile layouts, visible keyboard focus, reduced-motion support, and automatic pausing of offscreen previews.

## Editing and Deployment

| Path | Purpose |
| --- | --- |
| `dist/index.html` | Page structure, text, framework diagram, and citation |
| `dist/styles.css` | Visual styling and responsive layouts |
| `dist/app.js` | Demonstration controls and results interactions |
| `dist/demo-data.json` | Video manifest, clients, tasks, and selected seeds |
| `dist/results-data.json` | Experimental statistics and metric definitions |
| `dist/assets/` | Recorded videos, extracted JPEG posters, and learning curves |
| `server.mjs` | Local static server with support for video Range requests |

Any static host can serve `dist/` directly. Internal asset URLs are relative, so the site supports deployment under a subpath. The Python training environment is not required to serve the website.

Videos and posters are published with the static site. Demonstration videos are not preloaded; scroll playback only plays visible rows, while every client's poster remains available. Fonts are loaded from Google Fonts with system-font fallbacks.

The workflow in `.github/workflows/pages.yml` checks site assets and deploys `dist/` to GitHub Pages whenever `main` is updated. The published URL is [https://hhhhzl.github.io/fedguide-page/](https://hhhhzl.github.io/fedguide-page/).

## Data Sources and Metric Definitions

Source paths in this section refer to the original [FedGuide research repository](https://github.com/hhhhzl/fedguide), unless stated otherwise. Author information, the title, conference details, and links come from that repository's `README.md` and `latex/latex_fedguide/main.tex`.

### Policy Demonstrations

Main-environment recordings follow the selections in `assets/video_selection.json`. Hard-environment recordings use the same selection rule, recomputed from the corresponding training histories and saved videos. All recordings are from round 100. Reacher-Hard uses `reacher/ablation/C`; the other hard environments use their respective `*_hard` directories.

For each environment and method, the selected seed has the highest environment-average evaluation return over the last ten rounds. These clips are qualitative examples: the selection score is neither a cross-seed average nor the return of the particular episode being played. Different methods may use different seeds, which are displayed above each recording.

MetaWorld client task names come from the existing environment assets. The current HalfCheetah metadata lists 64 clients, while the saved demonstrations contain eight. The website follows the recorded experiment rather than applying the current configuration to older recordings.

### Quantitative Results

Statistics were recomputed from the saved `training_history.pkl` files under `metrics/` and checked against the corresponding paper tables. The dataset covers five main environments and four hard environments, with seven methods, five seeds, and 100 rounds for every environment–method combination.

- **Final return:** Compute each seed's mean client-average evaluation return over its last ten rounds, then report the mean ± sample standard deviation (SD) across the five seeds.
- **Worst-seed return:** The minimum of those five per-seed final returns.
- **Learning curves:** Exported from the original histories using this repository's `scripts/export_curves.py`. The exporter reuses the research code's five-seed aggregation, smoothing, and standard-error calculations, while placing legends below the axes. Bands show mean ± one standard error (SE). Smoothing details are recorded in `metadata.curveDefinition` in `dist/results-data.json`.
- **Experimental protocol:** Eight clients per main or hard environment, except MetaWorld10, which has ten. All environments use eight experts.

FedGuide has the highest mean final return on four of the five main benchmarks; FedGuide-P is slightly higher on Reacher. The 2.10× HalfCheetah comparison is against FedKL, the strongest external baseline.

In the hard suite, FedGuide has the highest mean final return on Walker2D-Hard and HalfCheetah-Hard. FedGuide-P leads on Reacher-Hard, and FedRL leads on Hopper-Hard. Reacher-Hard uses a symmetric logarithmic return axis to accommodate the wide range of values, including negative returns.

The paper's table caption labels W as “worst-round,” while the metric implementation computes worst-seed return. The curve caption refers to SD, while the plotting code computes SE. The website labels these statistics according to their implemented definitions; the source paper is unchanged.

### Regenerating Assets

Regenerating curves requires the original FedGuide research checkout, its experiment histories, NumPy, and Matplotlib. If this website repository is not located inside the research checkout, specify the source directory:

```bash
FEDGUIDE_SOURCE_ROOT=/path/to/fedguide python3 scripts/export_curves.py --update-results
```

Re-exporting hard-environment recordings and posters also requires ffmpeg:

```bash
FEDGUIDE_SOURCE_ROOT=/path/to/fedguide FFMPEG=/path/to/ffmpeg python3 scripts/export_hard_demos.py
```

## Validation

Run the static checks with:

```bash
node --check dist/app.js
node --check server.mjs
python3 scripts/check_site.py
```

The published version has also been checked for:

- All 222 recordings and their client posters, nine environment posters, and nine sets of learning curves. Main-suite selections match the original manifest; hard-suite selections match their training histories and recordings.
- Successful HTTP responses and actual playback of all three H.264 videos in a comparison row.
- Expanded eight- and ten-client layouts, row playback, playback-speed controls, result-table metric switching, and BibTeX copying.
- A 390 px mobile viewport without page-wide horizontal overflow. Environment tabs, the framework diagram, and wide tables retain their own scroll areas.
- No browser console errors or warnings during verification.
