"""SQL source connector built on SQLAlchemy.

Works with any SQLAlchemy dialect: SQLite for the local demo, SQL Server
(``mssql+pyodbc://``) for production. Timestamp bucketing is done in Python
so checks stay dialect-agnostic.
"""

from __future__ import annotations

from collections import Counter
from datetime import UTC, date, datetime, timedelta

from sqlalchemy import create_engine, inspect, text

from pipeline_sentinel.types import ColumnInfo, Source


def _parse_timestamp(value: object) -> datetime | None:
    """Parse a DB timestamp into a timezone-aware UTC datetime."""
    if value is None:
        return None
    if isinstance(value, datetime):
        parsed = value
    elif isinstance(value, date):
        parsed = datetime(value.year, value.month, value.day)
    else:
        try:
            parsed = datetime.fromisoformat(str(value))
        except ValueError:
            return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed


class SqlSource:
    """Read-only accessor over one table of a SQL database."""

    def __init__(self, source: Source) -> None:
        self.source = source
        self._engine = create_engine(source.connection_string)

    def _timestamps(self, since: datetime) -> list[datetime]:
        query = text(
            f"SELECT {self.source.timestamp_column} FROM {self.source.table} "
            f"WHERE {self.source.timestamp_column} >= :since"
        )
        with self._engine.connect() as conn:
            rows = conn.execute(query, {"since": since.isoformat()}).all()
        return [ts for row in rows if (ts := _parse_timestamp(row[0])) is not None]

    def row_counts_by_date(self, days: int) -> dict[date, int]:
        """Row counts per calendar date for the last ``days`` days."""
        since = datetime.now(UTC) - timedelta(days=days)
        counts: Counter[date] = Counter()
        for ts in self._timestamps(since):
            counts[ts.date()] += 1
        return dict(counts)

    def max_timestamp(self) -> datetime | None:
        """Newest timestamp in the table, or None when the table is empty."""
        query = text(f"SELECT MAX({self.source.timestamp_column}) FROM {self.source.table}")
        with self._engine.connect() as conn:
            value = conn.execute(query).scalar()
        return _parse_timestamp(value)

    def columns(self) -> list[ColumnInfo]:
        """Current (name, type) pairs of the table."""
        inspector = inspect(self._engine)
        return [
            ColumnInfo(name=col["name"], type=str(col["type"]))
            for col in inspector.get_columns(self.source.table)
        ]

    def null_rate(self, column: str) -> float:
        """Fraction of NULL values in ``column`` (0..1)."""
        query = text(
            f"SELECT COUNT(*) AS total, SUM(CASE WHEN {column} IS NULL THEN 1 ELSE 0 END) "
            f"AS nulls FROM {self.source.table}"
        )
        with self._engine.connect() as conn:
            total, nulls = conn.execute(query).one()
        if not total:
            return 0.0
        return (nulls or 0) / total

    def duplicate_rate(self, columns: list[str] | None) -> float:
        """Fraction of rows duplicated on ``columns`` (whole row when None)."""
        key = ", ".join(columns) if columns else "*"
        with self._engine.connect() as conn:
            total = conn.execute(text(f"SELECT COUNT(*) FROM {self.source.table}")).scalar() or 0
            distinct = (
                conn.execute(
                    text(
                        f"SELECT COUNT(*) FROM (SELECT DISTINCT {key} FROM {self.source.table}) AS d"
                    )
                ).scalar()
                or 0
            )
        if not total:
            return 0.0
        return (total - distinct) / total

    def out_of_range_rate(self, column: str, min_value: float, max_value: float) -> float:
        """Fraction of ``column`` values outside [``min_value``, ``max_value``]."""
        query = text(
            f"SELECT COUNT(*) AS total, "
            f"SUM(CASE WHEN {column} < :lo OR {column} > :hi THEN 1 ELSE 0 END) AS ooo "
            f"FROM {self.source.table}"
        )
        with self._engine.connect() as conn:
            total, ooo = conn.execute(query, {"lo": min_value, "hi": max_value}).one()
        if not total:
            return 0.0
        return (ooo or 0) / total
