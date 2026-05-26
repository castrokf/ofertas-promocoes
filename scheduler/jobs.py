from __future__ import annotations

import time
from datetime import datetime, timedelta
from typing import Callable

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from config import Settings
from database.models import ExecutionStats


console = Console()


def render_status_panel(stats: ExecutionStats, mode: str, segment: str) -> None:
    table = Table(show_header=False, box=None)
    table.add_row("Modo", mode)
    table.add_row("Segmento", segment)
    table.add_row("Ofertas coletadas", str(stats.offers_collected))
    table.add_row("Ofertas aprovadas", str(stats.offers_approved))
    table.add_row("Ofertas postadas", str(stats.offers_posted))
    table.add_row("Erros", str(len(stats.errors)))
    table.add_row(
        "Proxima execucao",
        stats.next_run_at.strftime("%Y-%m-%d %H:%M:%S") if stats.next_run_at else "n/a",
    )
    if stats.last_run_started_at:
        table.add_row(
            "Ultima execucao",
            stats.last_run_started_at.strftime("%Y-%m-%d %H:%M:%S"),
        )
    console.print(Panel(table, title="AutoTechDealsX", border_style="cyan"))


def run_scheduler(
    settings: Settings,
    job_callable: Callable[[ExecutionStats], ExecutionStats],
    segment: str = "all",
) -> None:
    while True:
        stats = ExecutionStats(last_run_started_at=datetime.now())
        try:
            stats = job_callable(stats)
        except KeyboardInterrupt:
            raise
        except Exception as exc:
            stats.errors.append(str(exc))
        stats.last_run_finished_at = datetime.now()
        stats.next_run_at = datetime.now() + timedelta(minutes=settings.post_interval_minutes)
        render_status_panel(
            stats=stats,
            mode="test" if settings.test_mode else "run",
            segment=segment,
        )

        sleep_seconds = settings.post_interval_minutes * 60
        for _ in range(sleep_seconds):
            time.sleep(1)
