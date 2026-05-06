import re
from dataclasses import dataclass
from pathlib import Path


_USERNAME_SAFE_RE = re.compile(r"[^a-z0-9_-]+")


@dataclass(frozen=True)
class UserWorkspace:
    username: str
    root: Path
    shared_data_dir: Path
    data_dir: Path
    history_db: Path
    recommendation_dir: Path
    dashboard_history_dir: Path
    report_history_dir: Path
    model_dir: Path
    reports_dir: Path
    exports_dir: Path


def normalize_username(value: str) -> str:
    normalized = _USERNAME_SAFE_RE.sub("-", str(value or "").strip().lower()).strip("-_")
    if not normalized:
        raise ValueError("username must contain at least one ASCII letter or digit")
    return normalized


def workspace_for_user(root: Path, username: str, create: bool = True) -> UserWorkspace:
    root_path = Path(root)
    safe_username = normalize_username(username)
    shared_data_dir = root_path / "data" / "normalized"
    data_dir = root_path / "data" / "users" / safe_username
    reports_dir = root_path / "reports" / "users" / safe_username / "latest"
    workspace = UserWorkspace(
        username=safe_username,
        root=root_path,
        shared_data_dir=shared_data_dir,
        data_dir=data_dir,
        history_db=data_dir / "history.sqlite3",
        recommendation_dir=data_dir / "recommendations",
        dashboard_history_dir=data_dir / "dashboard-history",
        report_history_dir=data_dir / "report-history",
        model_dir=data_dir / "models",
        reports_dir=reports_dir,
        exports_dir=root_path / "reports" / "users" / safe_username / "exports",
    )
    if create:
        for directory in (
            workspace.shared_data_dir,
            workspace.data_dir,
            workspace.recommendation_dir,
            workspace.dashboard_history_dir,
            workspace.report_history_dir,
            workspace.model_dir,
            workspace.reports_dir,
            workspace.exports_dir,
        ):
            directory.mkdir(parents=True, exist_ok=True)
    return workspace
