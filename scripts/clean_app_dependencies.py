"""Remove locally vendored Python packages before Catalyst installs Linux wheels."""

from pathlib import Path
import shutil


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEPENDENCY_DIRS = (PROJECT_ROOT, PROJECT_ROOT / "app")
DEPENDENCY_NAMES = {
    "bin",
    "blinker",
    "certifi",
    "charset_normalizer",
    "click",
    "dateutil",
    "flask",
    "gunicorn",
    "idna",
    "itsdangerous",
    "jinja2",
    "markupsafe",
    "numpy",
    "numpy.libs",
    "packaging",
    "pandas",
    "pandas.libs",
    "pytz",
    "requests",
    "six",
    "six.py",
    "typing_extensions",
    "typing_extensions.py",
    "urllib3",
    "werkzeug",
    "zcatalyst_sdk",
}


def main() -> None:
    normalized_dependencies = {
        dependency.replace("_", "-").replace(".py", "") for dependency in DEPENDENCY_NAMES
    }
    for dependency_dir in DEPENDENCY_DIRS:
        for path in dependency_dir.iterdir():
            name = path.name
            stem = name.split("-", 1)[0].replace("_", "-")
            module_name = name[:-3] if name.endswith(".py") else stem
            is_dependency = (
                name in DEPENDENCY_NAMES
                or module_name in DEPENDENCY_NAMES
                or stem in normalized_dependencies
                or (stem in normalized_dependencies and name.endswith(".dist-info"))
                or (module_name in normalized_dependencies and name.endswith(".py"))
            )
            if is_dependency:
                if path.is_dir():
                    shutil.rmtree(path)
                else:
                    path.unlink()


if __name__ == "__main__":
    main()
