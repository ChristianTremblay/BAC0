import tomllib


def get_version_from_pyproject():
    with open("pyproject.toml", "rb") as f:
        pyproject_data = tomllib.load(f)
    return pyproject_data["project"]["version"]


def update_version_py(version_file, new_version):
    lines = []
    found = False
    with open(version_file, "r", encoding="utf-8") as f:
        for line in f:
            if "__version__" in line:
                lines.append(f'__version__ = "{new_version}"\n')
                found = True
            else:
                lines.append(line)
    if not found:
        lines.append(f'__version__ = "{new_version}"\n')
    with open(version_file, "w", encoding="utf-8") as f:
        f.writelines(lines)


if __name__ == "__main__":
    version = get_version_from_pyproject()
    print(f"BAC0 Version: {version}")
    update_version_py("BAC0/infos.py", version)
    print("Version updated in BAC0/infos.py")
