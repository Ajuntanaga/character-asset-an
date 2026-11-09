from __future__ import annotations

import argparse
import hashlib
import zipfile
from pathlib import Path


PREFIX = Path("Character Asset_An_V200")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def package_files(root: Path) -> list[Path]:
    files: set[Path] = set()
    files.add(root / "production_v200_final" / "ant_character_asset_final_v200.blend")
    files.update(path for path in (root / "pipeline").rglob("*.py") if "__pycache__" not in path.parts)
    files.update(path for path in (root / "references").rglob("*") if path.is_file())
    for relative in (
        "docs/superpowers/specs/2026-10-02-character-asset-completion-design.md",
        "docs/superpowers/plans/2026-10-02-character-asset-completion-plan.md",
    ):
        path = root / relative
        if path.is_file():
            files.add(path)
    for version in range(194, 201):
        matches = sorted(root.glob(f"production_v{version}_*"))
        if not matches:
            continue
        production = matches[0]
        for folder in ("analysis", "audit", "delivery"):
            candidate = production / folder
            if candidate.is_dir():
                files.update(path for path in candidate.rglob("*") if path.is_file())
        files.update(path for path in production.glob("*.md") if path.is_file())
        renders = production / "renders"
        if renders.is_dir():
            files.update(path for path in renders.rglob("*manifest*.json") if path.is_file())
    return sorted(files)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage-root", type=Path, required=True)
    parser.add_argument("--resume", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root = args.stage_root.resolve()
    resume = args.resume.resolve()
    output = args.output.resolve()
    files = package_files(root)
    missing = [str(path) for path in files if not path.is_file()]
    if missing:
        raise RuntimeError("Missing package inputs: " + ", ".join(missing))
    output.parent.mkdir(parents=True, exist_ok=True)
    manifest_lines = []
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        for path in files:
            relative = path.relative_to(root)
            arcname = PREFIX / relative
            archive.write(path, arcname.as_posix())
            manifest_lines.append(f"{sha256(path)}  {relative.as_posix()}")
        archive.write(resume, (PREFIX / "RESUME.md").as_posix())
        manifest_lines.append(f"{sha256(resume)}  RESUME.md")
        archive.writestr(
            (PREFIX / "PACKAGE_MANIFEST_SHA256.txt").as_posix(),
            "\n".join(sorted(manifest_lines)) + "\n",
        )
    with zipfile.ZipFile(output) as archive:
        bad_member = archive.testzip()
    if bad_member:
        raise RuntimeError(f"Corrupt package member: {bad_member}")
    digest = sha256(output)
    output.with_suffix(output.suffix + ".sha256").write_text(f"{digest}  {output.name}\n", encoding="utf-8")
    print(f"V200_PACKAGE={output}")
    print(f"V200_PACKAGE_SHA256={digest}")
    print(f"V200_PACKAGE_FILES={len(files) + 2}")


if __name__ == "__main__":
    main()
