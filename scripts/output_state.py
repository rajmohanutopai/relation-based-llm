"""Safe transitions for files other scripts rely on. See docs/state-machines.md.

Readers must never see a half-written file, or files from two different builds
presented as one. Everything here writes aside, then moves into place.
"""

from __future__ import annotations

import atexit
import contextlib
import os
import shutil
import sys
from pathlib import Path
from typing import Iterator


def atomic_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(f"{path.name}.tmp-{os.getpid()}")
    try:
        with temp.open("w", encoding="utf-8") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp, path)
    except BaseException:
        temp.unlink(missing_ok=True)
        raise


def claim_results(path: Path, overwrite: bool) -> None:
    """Take a results file for this run. Without overwrite, a second run on the
    same file stops here, so runs can't silently replace each other's results."""
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        os.close(os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY))
    except FileExistsError:
        if not overwrite:
            raise SystemExit(f"{path} already exists, or another run is using it; pass --overwrite "
                             "or choose another --out") from None


def _alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


@contextlib.contextmanager
def directory_lock(directory: Path) -> Iterator[None]:
    """One writer per directory. A lock left by a dead process is taken over."""
    directory.mkdir(parents=True, exist_ok=True)
    lock = directory / ".lock"
    for _ in range(2):
        try:
            fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            break
        except FileExistsError:
            try:
                holder = int(lock.read_text().strip() or 0)
            except (OSError, ValueError):
                holder = 0
            if holder and _alive(holder):
                raise SystemExit(f"{directory} is in use by process {holder}") from None
            lock.unlink(missing_ok=True)
    else:
        raise SystemExit(f"could not lock {directory}")
    with os.fdopen(fd, "w") as handle:
        handle.write(str(os.getpid()))
    try:
        yield
    finally:
        lock.unlink(missing_ok=True)


def refuse_overlap(output_dir: Path, inputs: Path) -> None:
    """Replacing output_dir must never be able to delete the inputs."""
    output, source = output_dir.resolve(), inputs.resolve()
    if output == source or output in source.parents:
        raise SystemExit(f"--output-dir {output_dir} would delete the inputs in {inputs}")


@contextlib.contextmanager
def staged_directory(final: Path) -> Iterator[Path]:
    """Yield an empty sibling directory; on success it replaces final, on any
    failure final stays as it was and the sibling goes away."""
    final.parent.mkdir(parents=True, exist_ok=True)
    staged = final.with_name(f".{final.name}.staging-{os.getpid()}")
    retired = final.with_name(f".{final.name}.retired-{os.getpid()}")
    shutil.rmtree(staged, ignore_errors=True)
    staged.mkdir()
    try:
        yield staged
        if final.exists():
            final.rename(retired)
        staged.rename(final)
    except BaseException:
        shutil.rmtree(staged, ignore_errors=True)
        if retired.exists() and not final.exists():
            retired.rename(final)
        raise
    shutil.rmtree(retired, ignore_errors=True)


def retire_output_dir(path: Path) -> None:
    """For generators that write straight into their output directory: move the
    old directory aside instead of deleting it. If the script dies on an uncaught
    exception, the old directory comes back; otherwise it's removed at exit.

    A script that fails through SystemExit counts as finished, because Python
    doesn't report the exit status to exit handlers. Kill -9 leaves the old
    directory beside the new one under a .retired name, so nothing is lost.
    """
    path = Path(path)
    retired = path.with_name(f".{path.name}.retired-{os.getpid()}")
    shutil.rmtree(retired, ignore_errors=True)
    path.rename(retired)
    previous_hook = sys.excepthook

    def restore(kind, value, trace):
        shutil.rmtree(path, ignore_errors=True)
        if retired.exists():
            retired.rename(path)
            print(f"Run failed; restored previous {path}", file=sys.stderr)
        previous_hook(kind, value, trace)

    sys.excepthook = restore
    atexit.register(shutil.rmtree, retired, ignore_errors=True)
