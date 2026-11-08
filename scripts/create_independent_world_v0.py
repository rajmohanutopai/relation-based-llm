#!/usr/bin/env python3
"""Run scanned household objects through MuJoCo. Design: docs/independent-world-v0.md

  --calibrate   outcome rates over a grid of impulses, on 24 objects (no scores)
  --build       all 150 objects, with the impulses in GENTLE and HARD
"""

from __future__ import annotations

import argparse
import hashlib
import json
import multiprocessing as mp
import random
import xml.etree.ElementTree as ET
from pathlib import Path

import mujoco
import numpy as np

MODELS = Path("data/external/mujoco_scanned_objects/models")
SAMPLE = Path("data/external/scanned_objects_sample.json")
OUT = Path("data/developmental_graph/experiments/independent_world_v0")
FRICTIONS = {"slippery": 0.2, "grippy": 1.0}
REPEATS = 6
DT = 0.002
PUSH_TIME = 0.02
GENTLE, HARD = 0.5, 2.0  # N*s, set once by --calibrate
ACTIONS = {"push_gentle": 3, "push_hard": 3, "drop": 2}


def build_model(name: str, friction: float) -> mujoco.MjModel:
    root = ET.parse(MODELS / name / "model.xml").getroot()
    meshes = sorted({m.get("file") for m in root.iter("mesh") if "collision" in (m.get("file") or "")})
    assets = "".join(f'<mesh name="m{i}" file="{f}"/>' for i, f in enumerate(meshes))
    geoms = "".join(f'<geom type="mesh" mesh="m{i}" friction="{friction} 0.005 0.0001"/>' for i in range(len(meshes)))
    xml = f"""<mujoco><compiler meshdir="{(MODELS / name).resolve()}"/>
    <option timestep="{DT}" integrator="implicitfast"/>
    <asset>{assets}</asset><worldbody>
    <geom type="plane" size="5 5 0.1" friction="{friction} 0.005 0.0001"/>
    <body name="thing"><freejoint/>{geoms}</body></worldbody></mujoco>"""
    return mujoco.MjModel.from_xml_string(xml)


def extent(m, d, body):
    """Lowest and highest world z of the thing's meshes."""
    low, high = np.inf, -np.inf
    for g in range(m.ngeom):
        if m.geom_bodyid[g] != body:
            continue
        mesh = m.geom_dataid[g]
        start, n = m.mesh_vertadr[mesh], m.mesh_vertnum[mesh]
        z = (m.mesh_vert[start:start + n] @ d.geom_xmat[g].reshape(3, 3).T + d.geom_xpos[g])[:, 2]
        low, high = min(low, z.min()), max(high, z.max())
    return low, high


def rest(m, d, body, yaw):
    mujoco.mj_resetData(m, d)
    half = yaw / 2
    d.qpos[3:7] = [np.cos(half), 0, 0, np.sin(half)]
    mujoco.mj_forward(m, d)
    low, _ = extent(m, d, body)
    d.qpos[2] += 0.002 - low
    for _ in range(int(1.0 / DT)):
        mujoco.mj_step(m, d)
    d.qvel[:] = 0
    mujoco.mj_forward(m, d)


def simulate(m, action, impulse, yaw):
    d = mujoco.MjData(m)
    body = m.body("thing").id
    rest(m, d, body, yaw)
    start_xy = d.subtree_com[body][:2].copy()
    start_up = d.xmat[body].reshape(3, 3)[:, 2].copy()
    _, top = extent(m, d, body)
    turned = 0.0
    touch_xy = None
    if action == "drop":
        d.qpos[2] += 0.30
        mujoco.mj_forward(m, d)
    steps = int(1.5 / DT)
    push_steps = int(PUSH_TIME / DT)
    for step in range(steps):
        d.qfrc_applied[:] = 0
        if action != "drop" and step < push_steps:
            com = d.subtree_com[body].copy()
            point = com + [0, 0, (top - com[2]) * 0.5]  # above the centre, as a hand pushes
            mujoco.mj_applyFT(m, d, np.array([impulse / PUSH_TIME, 0, 0]), np.zeros(3), point, body, d.qfrc_applied)
        mujoco.mj_step(m, d)
        if action == "drop" and touch_xy is None and d.ncon > 0:
            touch_xy = d.subtree_com[body][:2].copy()
        else:
            spin = d.xmat[body].reshape(3, 3) @ d.qvel[3:6]
            turned += float(np.hypot(spin[0], spin[1])) * DT
    if d.warning[mujoco.mjtWarning.mjWARN_BADQACC].number or d.warning[mujoco.mjtWarning.mjWARN_BADQVEL].number \
            or d.warning[mujoco.mjtWarning.mjWARN_BADQPOS].number:
        return None  # MuJoCo reset an unstable run, so its end state means nothing
    end_xy = d.subtree_com[body][:2]
    end_up = d.xmat[body].reshape(3, 3)[:, 2]
    tipped = bool(start_up @ end_up < np.cos(np.pi / 4))
    if action == "drop":
        return [bool(np.linalg.norm(end_xy - (touch_xy if touch_xy is not None else start_xy)) > 0.10), tipped]
    return [bool(np.linalg.norm(end_xy - start_xy) > 0.05), bool(turned > np.pi), tipped]


def stable_seed(*parts) -> int:
    return int.from_bytes(hashlib.sha256("|".join(map(str, parts)).encode()).digest()[:4], "big")


def run_object(job):
    name, impulses, repeats = job
    out = {"name": name, "cases": {}}
    for surface, friction in FRICTIONS.items():
        m = build_model(name, friction)
        for label, impulse in impulses.items():
            action = "drop" if label == "drop" else label.split("@")[0]
            rng = random.Random(stable_seed(name, surface, label))
            out["cases"][f"{label}|{surface}"] = [simulate(m, action, impulse, rng.uniform(0, 2 * np.pi)) for _ in range(repeats)]
    d = mujoco.MjData(m)
    body = m.body("thing").id
    rest(m, d, body, 0.0)
    verts = []
    for g in range(m.ngeom):
        if m.geom_bodyid[g] == body:
            mesh = m.geom_dataid[g]
            s, n = m.mesh_vertadr[mesh], m.mesh_vertnum[mesh]
            verts.append(m.mesh_vert[s:s + n] @ d.geom_xmat[g].reshape(3, 3).T + d.geom_xpos[g])
    v = np.vstack(verts)
    out["size"] = (v.max(0) - v.min(0)).round(4).tolist()
    out["mass"] = round(float(m.body_subtreemass[body]), 4)
    return out


def calibrate():
    names = random.Random(1).sample(json.loads(SAMPLE.read_text()), 24)
    grid = [0.2, 0.5, 1.0, 2.0, 3.0, 5.0, 8.0]
    impulses = {f"push@{j}": j for j in grid} | {"drop": 0.0}
    with mp.Pool(8) as pool:
        results = pool.map(run_object, [(n, impulses, 3) for n in names])
    masses = sorted(r["mass"] for r in results)
    print("mass kg: min", masses[0], "median", masses[len(masses) // 2], "max", masses[-1])
    for label in impulses:
        for surface in FRICTIONS:
            rows = [b for r in results for b in r["cases"][f"{label}|{surface}"] if b is not None]
            rates = np.mean(rows, axis=0).round(2).tolist()
            print(f"{label:10} {surface:9} rates {rates}")


def build():
    OUT.mkdir(parents=True, exist_ok=True)
    impulses = {"push_gentle": GENTLE, "push_hard": HARD, "drop": 0.0}
    with mp.Pool(8) as pool:
        results = pool.map(run_object, [(n, impulses, REPEATS) for n in json.loads(SAMPLE.read_text())], chunksize=1)
    (OUT / "outcomes.json").write_text(json.dumps({"gentle": GENTLE, "hard": HARD, "objects": results}))
    for label in impulses:
        every = [b for r in results for s in FRICTIONS for b in r["cases"][f"{label}|{s}"]]
        rows = [b for b in every if b is not None]
        print(label, np.mean(rows, axis=0).round(3).tolist(), "unstable runs dropped", len(every) - len(rows), "of", len(every))
    print("objects", len(results))


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--calibrate", action="store_true")
    p.add_argument("--build", action="store_true")
    cli = p.parse_args()
    calibrate() if cli.calibrate else build()
