import hashlib
import json
import os
from pathlib import Path
from typing import Union

UNITS = ["B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB"]


def get_hash(path: Union[Path, str]) -> str:
    sha256_hash = hashlib.sha256()

    sha256_hash.update(Path(path).read_bytes())

    return sha256_hash.hexdigest()


def get_file_size(path: Union[Path, str]) -> int:
    size = os.path.getsize(path)

    for unit in UNITS:
        if size < 1024.0 or UNITS[-1] == unit:
            break
        size /= 1024.0

    return f"{size:.2f} {unit}"


def get_properties(path: Union[Path, str]) -> dict[str]:
    properties = {}
    for line in Path(path).read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue

        key, value = line.split("=", 1)
        properties[key] = value.lstrip()
    return properties


def main():
    builds_dir = Path("builds")
    builds_dir.mkdir(parents=True, exist_ok=True)
    versions: list[str] = json.loads(Path("versions.json").read_text())
    target_subprojects = list(
        filter(bool, os.environ.get("TARGET_SUBPROJECTS", "").split(","))
    )

    GITHUB_STEP_SUMMARY = os.environ["GITHUB_STEP_SUMMARY"]
    with open(GITHUB_STEP_SUMMARY, "w") as f:
        f.write("## Summary\n\n")
        f.write("| Subproject | For Minecraft | File | Size | SHA-256 |\n")
        f.write("| ---------- | ------------- | ---- | ---- | ------- |\n")

        for subproject in versions:
            print("---------------")
            if target_subprojects and subproject not in target_subprojects:
                print(f"skipping {subproject}")
                continue

            print(f"processing {subproject}")

            project_dir = Path(f"versions/{subproject}")
            project_files = list(
                filter(
                    lambda x: not (
                        x.stem.endswith("-sources") or x.stem.endswith("-dev")
                    ),
                    Path(f"versions/{subproject}/build/libs").glob("*.jar"),
                )
            )

            properties = get_properties(project_dir / "gradle.properties")
            minecraft_version = properties["minecraft_version"]
            game_versions = ", ".join(properties["game_versions"].strip().split(","))

            # minecraft versions
            f.write(f"|{minecraft_version}")
            # game versions
            f.write(f"|{game_versions}")

            file_name, file_size, file_hash = "Not Found", "N/A", "N/A"
            if not project_files:
                print(f"no files found for {subproject}")
            elif len(project_files) > 1:
                print(f"multiple files found for {subproject}")
            else:
                project_file = project_files[0]
                file_name = project_file.name
                file_size = get_file_size(project_file)
                file_hash = get_hash(project_file)
                project_file.rename(builds_dir / project_file.name)

            # file name
            f.write(f"|`{file_name}`")
            # file size
            f.write(f"|`{file_size}`")
            # file hash
            f.write(f"|`{file_hash}`|\n")

    (builds_dir / "SUMMARY.md").write_bytes(Path(GITHUB_STEP_SUMMARY).read_bytes())


if __name__ == "__main__":
    main()
