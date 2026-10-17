"""Keep automated tests away from the developer's local hospital database."""
import os
import tempfile
from pathlib import Path


_test_database_directory = None
if "DATABASE_URL" not in os.environ:
    _test_database_directory = tempfile.TemporaryDirectory(prefix="aeg-hospital-tests-")
    database_path = Path(_test_database_directory.name, "hospital.db").as_posix()
    os.environ["DATABASE_URL"] = f"sqlite:///{database_path}"


def pytest_unconfigure(config):
    if _test_database_directory is not None:
        from backend.app.database.session import engine

        engine.dispose()
        _test_database_directory.cleanup()