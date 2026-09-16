from pathlib import Path
from flask import Flask

from .config import Config
from .database import import_existing_files, init_db
from .routes import main


def create_app():
    app = Flask(
        __name__,
        template_folder=str(Path(__file__).resolve().parent.parent / "templates"),
        static_folder=str(Path(__file__).resolve().parent.parent / "static"),
    )
    app.config.from_object(Config)

    storage_root = Path(app.config["STORAGE_ROOT"])
    data_root = Path(app.config["DATA_ROOT"])

    for folder in (
        storage_root / "photos",
        storage_root / "videos",
        storage_root / "files",
        data_root,
    ):
        folder.mkdir(parents=True, exist_ok=True)

    init_db(app.config["DATABASE_PATH"])
    import_existing_files(
        db_path=app.config["DATABASE_PATH"],
        storage_root=storage_root,
    )

    app.register_blueprint(main)
    return app
