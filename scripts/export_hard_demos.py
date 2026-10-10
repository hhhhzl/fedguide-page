"""Export all clients' representative round-100 hard-environment recordings.

Requires Python, NumPy, the original FedGuide checkout, and ffmpeg. Set
FEDGUIDE_SOURCE_ROOT when that checkout is not the parent of this website;
set FFMPEG to an executable path when ffmpeg is not on PATH.

As with the main demonstrations, one seed is selected per environment/method
by highest last-10-round environment-average evaluation return. The score is
not the return of the displayed episode. Video streams are copied without
re-encoding, with the MP4 index moved to the front for browser playback.
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

SITE_ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = Path(os.environ.get("FEDGUIDE_SOURCE_ROOT", SITE_ROOT.parent)).resolve()
sys.path.insert(0, str(SOURCE_ROOT))
from scripts.viz.compute_table_metrics import load_stack  # noqa: E402

OUTPUT = SITE_ROOT / "dist"
FFMPEG = os.environ.get("FFMPEG") or shutil.which("ffmpeg")
HARD_ENVS = [
    ("reacher_hard", "Reacher-Hard", "reacher/ablation/C",
     "Reaching under stronger goal, action-noise, and reward heterogeneity (level C)."),
    ("hopper_hard", "Hopper-Hard", "hopper_hard",
     "One-legged locomotion with stronger client dynamics and reward differences."),
    ("walker_hard", "Walker2D-Hard", "walker_hard",
     "Bipedal locomotion with stronger client dynamics and reward differences."),
    ("halfcheetah_hard", "HalfCheetah-Hard", "halfcheetah_hard",
     "Running with stronger client dynamics and reward differences."),
]
METHODS = [("fedguide", "FedGuide"), ("fedguide_a", "FedGuide-A"), ("fedguide_p", "FedGuide-P")]


def export_clip(task: tuple[Path, Path, Path]) -> None:
    source, video, poster = task
    video.parent.mkdir(parents=True, exist_ok=True)
    poster.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run([
        FFMPEG, "-hide_banner", "-loglevel", "error", "-nostdin", "-y",
        "-i", str(source), "-map", "0:v:0", "-c", "copy",
        "-movflags", "+faststart", str(video),
    ], check=True)
    subprocess.run([
        FFMPEG, "-hide_banner", "-loglevel", "error", "-nostdin", "-y",
        "-i", str(video), "-frames:v", "1", "-q:v", "3", str(poster),
    ], check=True)
    # Decode the whole recording, catching truncation beyond the poster frame.
    subprocess.run([
        FFMPEG, "-hide_banner", "-loglevel", "error", "-nostdin", "-xerror",
        "-i", str(video), "-f", "null", "-",
    ], check=True)
    if not poster.is_file() or poster.stat().st_size == 0:
        raise RuntimeError(f"No poster generated: {poster}")


def main() -> None:
    if not FFMPEG:
        raise SystemExit("Set FFMPEG to the ffmpeg executable or add ffmpeg to PATH.")
    manifest_path = OUTPUT / "demo-data.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["environments"] = [env for env in manifest["environments"] if env.get("suite") != "hard" and not env["id"].endswith("_hard")]
    for env in manifest["environments"]:
        env["suite"] = "main"
    manifest["selectionNote"] = (
        "Representative round-100 recordings use the highest-scoring seed for each "
        "environment/method. Selection scores are tail-10 environment-average evaluation "
        "returns, not the return of the displayed episode. Different methods may use "
        "different selected seeds. Main-suite selections follow assets/video_selection.json; "
        "hard-suite selections are recomputed from the original five-seed training histories."
    )
    manifest["mainSourceManifest"] = manifest.pop("sourceManifest", "assets/video_selection.json")
    manifest["hardSelectionScript"] = "scripts/export_hard_demos.py"
    tasks = []
    for key, name, source_key, description in HARD_ENVS:
        env = {
            "id": key, "name": name, "suite": "hard", "description": description,
            "poster": f"assets/posters/{key}.jpg",
            "clients": [{"id": i, "label": f"Client {i}"} for i in range(8)],
            "methods": [],
        }
        for algorithm, label in METHODS:
            metric_root = SOURCE_ROOT / "metrics" / source_key
            # The fixed five-seed check makes the stack index the actual seed ID.
            assert all((metric_root / algorithm / f"seed_{s}/training_history.pkl").is_file() for s in range(5))
            stack = load_stack(str(metric_root), algorithm)
            assert stack is not None and stack.shape == (5, 100), (key, algorithm)
            scores = stack[:, -10:].mean(axis=1)
            seed = int(scores.argmax())
            method = {
                "id": algorithm, "label": label, "seed": seed,
                "selectionScore": float(scores[seed]), "selectionMode": "env_algo_average",
                "scoreSource": "metrics_distributed_fit:eval/return:tail10",
                "metricSource": f"metrics/{source_key}/{algorithm}/seed_{seed}/training_history.pkl",
                "videos": {},
            }
            for client in range(8):
                source = f"plots/{source_key}/{algorithm}/seed_{seed}/client_{client}/round_0100.mp4"
                source_path = SOURCE_ROOT / source
                assert source_path.is_file(), source
                video = f"assets/videos/{key}/{algorithm}/client-{client}.mp4"
                poster = f"assets/posters/{key}/{algorithm}/client-{client}.jpg"
                method["videos"][str(client)] = {
                    "src": video, "poster": poster, "seed": seed, "client": client,
                    "round": 100, "source": source,
                }
                tasks.append((source_path, OUTPUT / video, OUTPUT / poster))
            env["methods"].append(method)
            print(f"{key}/{algorithm}: seed {seed}, tail-10 return {scores[seed]:.6f}, 8 clients")
        manifest["environments"].append(env)
    with ThreadPoolExecutor(max_workers=4) as executor:
        list(executor.map(export_clip, tasks))
    for key, *_ in HARD_ENVS:
        shutil.copyfile(OUTPUT / f"assets/posters/{key}/fedguide/client-0.jpg", OUTPUT / f"assets/posters/{key}.jpg")
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"Exported and decoded {len(tasks)} hard recordings and extracted their posters.")


if __name__ == "__main__":
    main()
