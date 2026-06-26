import os
import shutil
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv


load_dotenv()


def main() -> int:
    db_path = Path(os.getenv("DB_PATH", "autobot.db"))
    backup_dir = Path(os.getenv("BACKUP_DIR", "backups"))

    if not db_path.exists():
        print(f"DB not found: {db_path}")
        return 1

    backup_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_path = backup_dir / f"{db_path.stem}-{stamp}{db_path.suffix}"
    shutil.copy2(db_path, backup_path)
    print(f"Backup OK: {backup_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
