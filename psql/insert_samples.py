#!/usr/bin/env python3
"""
Insert sample readings into a PostgreSQL database.

Samples (short_name, epics_pv, phase) are loaded from a YAML file.
float_val values are either passed via --values or read from each
sample's EPICS PV via Channel Access (requires `pyepics`).

Examples:
    python insert_samples.py 42 --epics
    python insert_samples.py 42 --values 23.1 1.01
    python insert_samples.py 42 --values 23.1 1.01 \
        --time-date "2025-01-15 10:30:00"
"""

import argparse
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

import psycopg2
import yaml

from db_config import DB_CONFIG

"""
e.g. use:
DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "dbname": "xxxxxx",
    "user": "yyyyy",
    "password": "zzzzzz",
}
"""

INSERT_SQL = (
    "INSERT INTO sample "
    "(time_date, reports_id, short_name, pulse_phase, float_val) "
    "VALUES (%s, %s, %s, %s, %s)"
)

DEFAULT_SAMPLES_FILE = Path(__file__).with_name("samples.yaml")

log = logging.getLogger("insert_samples")


def setup_logging(verbosity: int, log_file: Optional[Path]) -> None:
    """Configure root logger. -v -> INFO, -vv -> DEBUG."""
    level = logging.WARNING
    if verbosity == 1:
        level = logging.INFO
    elif verbosity >= 2:
        level = logging.DEBUG

    handlers: List[logging.Handler] = [logging.StreamHandler(sys.stderr)]
    if log_file:
        handlers.append(logging.FileHandler(log_file, encoding="utf-8"))

    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)-7s %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=handlers,
    )


def load_samples(path: Path) -> List[dict]:
    """Load and validate the samples YAML file."""
    log.debug("Loading samples from %s", path)
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    if not isinstance(data, list) or not data:
        raise ValueError(f"{path}: expected a non-empty list of samples.")

    required = {"short_name", "epics_pv", "phase"}
    for i, entry in enumerate(data):
        missing = required - entry.keys()
        if missing:
            raise ValueError(f"{path}: sample #{i} missing keys: {missing}")

    log.info("Loaded %d sample(s) from %s", len(data), path)
    return data


def parse_time(value: Optional[str]) -> datetime:
    """Parse a time string or fall back to current time."""
    if value is None:
        return datetime.now(timezone.utc)

    try:
        ts = float(value)
        return datetime.fromtimestamp(ts, tz=timezone.utc)
    except ValueError:
        pass

    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue

    raise argparse.ArgumentTypeError(
        f"Unrecognized time-date format: {value!r}. "
        "Use a UNIX timestamp or 'YYYY-MM-DD HH:MM:SS'."
    )


def read_epics_values(pv_names: List[str], timeout: float = 3.0) -> List[float]:
    """Read float values from EPICS Channel Access PVs."""
    try:
        from epics import caget  # pyepics
    except ImportError as exc:
        raise RuntimeError(
            "pyepics is required for --epics mode. "
            "Install it with `pip install pyepics`."
        ) from exc

    values: List[float] = []
    for pv in pv_names:
        log.debug("caget %s (timeout=%.1fs)", pv, timeout)
        val = caget(pv, timeout=timeout)
        if val is None:
            raise RuntimeError(f"Failed to read EPICS PV: {pv}")
        fval = float(val)
        log.info("EPICS %s = %g", pv, fval)
        values.append(fval)
    return values


def build_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Insert sample readings into the DB.")

    parser.add_argument("reports_id", type=int, help="reports_id foreign key value.")

    parser.add_argument(
        "--time-date",
        type=str,
        default=None,
        help="Timestamp: UNIX seconds or 'YYYY-MM-DD HH:MM:SS'. Defaults to now (UTC).",
    )

    parser.add_argument(
        "--samples-file",
        type=Path,
        default=DEFAULT_SAMPLES_FILE,
        help=f"YAML samples file (default: {DEFAULT_SAMPLES_FILE.name}).",
    )

    src = parser.add_mutually_exclusive_group(required=True)
    src.add_argument(
        "--values",
        type=float,
        nargs="+",
        help="Float values, one per sample in YAML order.",
    )
    src.add_argument(
        "--epics",
        action="store_true",
        help="Read float values from each sample's epics_pv.",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the rows without writing to the DB.",
    )

    parser.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=1,
        help="Increase verbosity: -v INFO (default), -vv DEBUG.",
    )
    parser.add_argument(
        "-q", "--quiet", action="store_true", help="Only show warnings and errors."
    )
    parser.add_argument(
        "--log-file",
        type=Path,
        default=None,
        help="Optional file to also write log records to.",
    )
    return parser.parse_args()


def main() -> int:
    args = build_args()
    verbosity = 0 if args.quiet else args.verbose
    setup_logging(verbosity, args.log_file)

    log.debug("Arguments: %s", vars(args))

    try:
        samples = load_samples(args.samples_file)
    except (OSError, ValueError, yaml.YAMLError) as exc:
        log.error("Failed to load samples: %s", exc)
        return 2

    if args.epics:
        pvs = [s["epics_pv"] for s in samples]
        try:
            float_vals = read_epics_values(pvs)
        except RuntimeError as exc:
            log.error("%s", exc)
            return 1
    else:
        if len(args.values) != len(samples):
            log.error("Expected %d value(s), got %d.", len(samples), len(args.values))
            return 2
        float_vals = args.values

    time_date = parse_time(args.time_date)
    log.info(
        "Using time_date=%s, reports_id=%d", time_date.isoformat(), args.reports_id
    )

    rows = [
        (time_date, args.reports_id, s["short_name"], s["phase"], fv)
        for s, fv in zip(samples, float_vals)
    ]

    for i, r in enumerate(rows, start=1):
        log.info(
            "Row %d/%d: time_date=%s reports_id=%d short_name=%r "
            "pulse_phase=%r float_val=%g",
            i,
            len(rows),
            r[0].isoformat(),
            r[1],
            r[2],
            r[3],
            r[4],
        )

    if args.dry_run:
        log.warning("Dry run: no rows written to the database.")
        return 0

    try:
        with psycopg2.connect(**DB_CONFIG) as conn:
            with conn.cursor() as cur:
                for i, r in enumerate(rows, start=1):
                    cur.execute(INSERT_SQL, r)
                    log.debug(
                        "Inserted row %d/%d (rowcount=%d)", i, len(rows), cur.rowcount
                    )
        log.info("Inserted %d row(s) into sample.", len(rows))
    except psycopg2.Error as exc:
        log.error("Database error: %s", exc)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
