"""SVT Time App - Date and time utilities wrapping Python's datetime and time modules."""

import calendar
import time as _time
from datetime import datetime, timedelta, timezone, date
from svt.sdk import SVTApp, CommandResult, ExecutionContext

# Default ISO format used throughout
_ISO_FMT = "%Y-%m-%dT%H:%M:%S"
_DATE_FMT = "%Y-%m-%d"

# Formats tried when auto-detecting during parse
_AUTO_FORMATS = [
    "%Y-%m-%dT%H:%M:%S",
    "%Y-%m-%dT%H:%M:%S.%f",
    "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%d %H:%M:%S.%f",
    "%Y-%m-%d",
    "%d/%m/%Y %H:%M:%S",
    "%d/%m/%Y",
    "%m/%d/%Y %H:%M:%S",
    "%m/%d/%Y",
    "%Y%m%d",
]


def _dt_to_dict(dt: datetime) -> dict:
    """Convert a datetime object to the canonical SVT datetime dict."""
    return {
        "year":    dt.year,
        "month":   dt.month,
        "day":     dt.day,
        "hour":    dt.hour,
        "minute":  dt.minute,
        "second":  dt.second,
        "weekday": dt.weekday(),
        "iso":     dt.strftime(_ISO_FMT),
        "date":    dt.strftime(_DATE_FMT),
    }


def _dict_to_dt(d: dict) -> datetime:
    """Reconstruct a datetime from an SVT datetime dict."""
    return datetime(
        year=int(d.get("year", 1970)),
        month=int(d.get("month", 1)),
        day=int(d.get("day", 1)),
        hour=int(d.get("hour", 0)),
        minute=int(d.get("minute", 0)),
        second=int(d.get("second", 0)),
    )


class TimeApp(SVTApp):

    # ── Current time ──────────────────────────────────────────────────────────

    def cmd_now(self, ctx: ExecutionContext) -> CommandResult:
        use_utc = ctx.options.get("utc", False)
        as_ts = ctx.options.get("ts", False)
        fmt = ctx.options.get("fmt", None)

        dt = datetime.now(tz=timezone.utc) if use_utc else datetime.now()

        if as_ts:
            result = dt.timestamp()
            print(result)
            return CommandResult.success(value=result)

        if fmt:
            result = dt.strftime(str(fmt))
            print(result)
            return CommandResult.success(value=result)

        result = _dt_to_dict(dt)
        print(f"  {result['iso']}")
        return CommandResult.success(value=result)

    def cmd_today(self, ctx: ExecutionContext) -> CommandResult:
        use_utc = ctx.options.get("utc", False)
        d = datetime.now(tz=timezone.utc).date() if use_utc else date.today()
        result = str(d)
        print(f"  {result}")
        return CommandResult.success(value=result)

    def cmd_timestamp(self, ctx: ExecutionContext) -> CommandResult:
        as_ms = ctx.options.get("ms", False)
        ts = _time.time()
        result = ts * 1000 if as_ms else ts
        print(f"  {result}")
        return CommandResult.success(value=result)

    def cmd_perf(self, ctx: ExecutionContext) -> CommandResult:
        as_ns = ctx.options.get("ns", False)
        result = _time.perf_counter_ns() if as_ns else _time.perf_counter()
        print(f"  {result}")
        return CommandResult.success(value=result)

    # ── Conversion ────────────────────────────────────────────────────────────

    def cmd_from_timestamp(self, ctx: ExecutionContext) -> CommandResult:
        if not ctx.args:
            return CommandResult.error("Usage: time:from_timestamp <ts>")
        try:
            ts = float(str(ctx.args[0]))
        except (ValueError, TypeError):
            return CommandResult.error(f"Invalid timestamp: {ctx.args[0]}")

        use_utc = ctx.options.get("utc", False)
        fmt = ctx.options.get("fmt", None)

        dt = datetime.fromtimestamp(ts, tz=timezone.utc) if use_utc else datetime.fromtimestamp(ts)

        if fmt:
            result = dt.strftime(str(fmt))
            print(result)
            return CommandResult.success(value=result)

        result = _dt_to_dict(dt)
        print(f"  {result['iso']}")
        return CommandResult.success(value=result)

    def cmd_to_timestamp(self, ctx: ExecutionContext) -> CommandResult:
        if not ctx.args:
            return CommandResult.error("Usage: time:to_timestamp <dt>")
        dt, err = self._require_dt(ctx.args[0])
        if err:
            return err
        result = dt.timestamp()
        print(f"  {result}")
        return CommandResult.success(value=result)

    def cmd_to_iso(self, ctx: ExecutionContext) -> CommandResult:
        if not ctx.args:
            return CommandResult.error("Usage: time:to_iso <dt>")
        dt, err = self._require_dt(ctx.args[0])
        if err:
            return err
        result = dt.strftime(_ISO_FMT)
        print(result)
        return CommandResult.success(value=result)

    # ── Parse / Format ────────────────────────────────────────────────────────

    def cmd_parse(self, ctx: ExecutionContext) -> CommandResult:
        if not ctx.args:
            return CommandResult.error("Usage: time:parse <datetime_string>")
        s = str(ctx.args[0])
        fmt = ctx.options.get("fmt", None)

        if fmt:
            try:
                dt = datetime.strptime(s, str(fmt))
                result = _dt_to_dict(dt)
                print(f"  {result['iso']}")
                return CommandResult.success(value=result)
            except ValueError as e:
                return CommandResult.error(f"Parse failed with format '{fmt}': {e}")

        for f in _AUTO_FORMATS:
            try:
                dt = datetime.strptime(s, f)
                result = _dt_to_dict(dt)
                print(f"  {result['iso']}")
                return CommandResult.success(value=result)
            except ValueError:
                continue

        return CommandResult.error(
            f"Could not parse '{s}'. Use --fmt to specify a strptime format string."
        )

    def cmd_format(self, ctx: ExecutionContext) -> CommandResult:
        if not ctx.args:
            return CommandResult.error("Usage: time:format <dt> [fmt]")
        dt, err = self._require_dt(ctx.args[0])
        if err:
            return err

        # fmt can come from a positional arg or --fmt option
        fmt = str(ctx.args[1]) if len(ctx.args) > 1 else str(ctx.options.get("fmt", _ISO_FMT))
        try:
            result = dt.strftime(fmt)
            print(result)
            return CommandResult.success(value=result)
        except Exception as e:
            return CommandResult.error(f"Format error: {e}")

    def cmd_make(self, ctx: ExecutionContext) -> CommandResult:
        now = datetime.now()
        try:
            dt = datetime(
                year=int(ctx.options.get("year",   now.year)),
                month=int(ctx.options.get("month",  now.month)),
                day=int(ctx.options.get("day",    now.day)),
                hour=int(ctx.options.get("hour",   0)),
                minute=int(ctx.options.get("minute", 0)),
                second=int(ctx.options.get("second", 0)),
            )
        except (ValueError, TypeError) as e:
            return CommandResult.error(f"Invalid date components: {e}")
        result = _dt_to_dict(dt)
        print(f"  {result['iso']}")
        return CommandResult.success(value=result)

    # ── Arithmetic ────────────────────────────────────────────────────────────

    def cmd_add(self, ctx: ExecutionContext) -> CommandResult:
        if not ctx.args:
            return CommandResult.error("Usage: time:add <dt> --days N --hours N --minutes N --seconds N --weeks N")
        dt, err = self._require_dt(ctx.args[0])
        if err:
            return err
        delta = self._parse_delta(ctx)
        result = _dt_to_dict(dt + delta)
        print(f"  {result['iso']}")
        return CommandResult.success(value=result)

    def cmd_sub(self, ctx: ExecutionContext) -> CommandResult:
        if not ctx.args:
            return CommandResult.error("Usage: time:sub <dt> --days N --hours N --minutes N --seconds N --weeks N")
        dt, err = self._require_dt(ctx.args[0])
        if err:
            return err
        delta = self._parse_delta(ctx)
        result = _dt_to_dict(dt - delta)
        print(f"  {result['iso']}")
        return CommandResult.success(value=result)

    def cmd_diff(self, ctx: ExecutionContext) -> CommandResult:
        if len(ctx.args) < 2:
            return CommandResult.error("Usage: time:diff <dt1> <dt2>")
        dt1, err = self._require_dt(ctx.args[0])
        if err:
            return err
        dt2, err = self._require_dt(ctx.args[1])
        if err:
            return err
        delta = dt2 - dt1
        total_seconds = int(delta.total_seconds())
        sign = -1 if total_seconds < 0 else 1
        abs_seconds = abs(total_seconds)
        result = {
            "total_seconds": total_seconds,
            "days":    sign * (abs_seconds // 86400),
            "hours":   sign * ((abs_seconds % 86400) // 3600),
            "minutes": sign * ((abs_seconds % 3600) // 60),
            "seconds": sign * (abs_seconds % 60),
        }
        print(f"  {result['days']}d {result['hours']}h {result['minutes']}m {result['seconds']}s")
        return CommandResult.success(value=result)

    # ── Component extractors ──────────────────────────────────────────────────

    def cmd_year(self, ctx: ExecutionContext) -> CommandResult:
        return self._extract(ctx, "year")

    def cmd_month(self, ctx: ExecutionContext) -> CommandResult:
        return self._extract(ctx, "month")

    def cmd_day(self, ctx: ExecutionContext) -> CommandResult:
        return self._extract(ctx, "day")

    def cmd_hour(self, ctx: ExecutionContext) -> CommandResult:
        return self._extract(ctx, "hour")

    def cmd_minute(self, ctx: ExecutionContext) -> CommandResult:
        return self._extract(ctx, "minute")

    def cmd_second(self, ctx: ExecutionContext) -> CommandResult:
        return self._extract(ctx, "second")

    def cmd_weekday(self, ctx: ExecutionContext) -> CommandResult:
        return self._extract(ctx, "weekday")

    def cmd_weekday_name(self, ctx: ExecutionContext) -> CommandResult:
        if not ctx.args:
            return CommandResult.error("Usage: time:weekday_name <dt>")
        dt, err = self._require_dt(ctx.args[0])
        if err:
            return err
        result = dt.strftime("%A")
        print(result)
        return CommandResult.success(value=result)

    def cmd_month_name(self, ctx: ExecutionContext) -> CommandResult:
        if not ctx.args:
            return CommandResult.error("Usage: time:month_name <dt>")
        dt, err = self._require_dt(ctx.args[0])
        if err:
            return err
        result = dt.strftime("%B")
        print(result)
        return CommandResult.success(value=result)

    # ── Calendar helpers ──────────────────────────────────────────────────────

    def cmd_is_leap(self, ctx: ExecutionContext) -> CommandResult:
        if not ctx.args:
            return CommandResult.error("Usage: time:is_leap <dt_or_year>")
        val = ctx.args[0]
        if isinstance(val, dict):
            year = int(val.get("year", 0))
        else:
            try:
                year = int(val)
            except (ValueError, TypeError):
                return CommandResult.error(f"Expected a year number or datetime dict, got: {val!r}")
        result = calendar.isleap(year)
        return CommandResult.success(value=result)

    def cmd_days_in_month(self, ctx: ExecutionContext) -> CommandResult:
        if not ctx.args:
            return CommandResult.error("Usage: time:days_in_month <dt>")
        dt, err = self._require_dt(ctx.args[0])
        if err:
            return err
        _, days = calendar.monthrange(dt.year, dt.month)
        print(f"  {days}")
        return CommandResult.success(value=days)

    # ── Compare ───────────────────────────────────────────────────────────────

    def cmd_compare(self, ctx: ExecutionContext) -> CommandResult:
        if len(ctx.args) < 2:
            return CommandResult.error("Usage: time:compare <dt1> <dt2>")
        dt1, err = self._require_dt(ctx.args[0])
        if err:
            return err
        dt2, err = self._require_dt(ctx.args[1])
        if err:
            return err
        if dt1 < dt2:
            result = -1
        elif dt1 > dt2:
            result = 1
        else:
            result = 0
        print(f"  {result}")
        return CommandResult.success(value=result)

    def cmd_between(self, ctx: ExecutionContext) -> CommandResult:
        if len(ctx.args) < 3:
            return CommandResult.error("Usage: time:between <dt> <start> <end>")
        dt,    err = self._require_dt(ctx.args[0])
        if err: return err
        start, err = self._require_dt(ctx.args[1])
        if err: return err
        end,   err = self._require_dt(ctx.args[2])
        if err: return err
        result = start <= dt <= end
        return CommandResult.success(value=result)

    # ── Timezone ──────────────────────────────────────────────────────────────

    def cmd_timezone(self, ctx: ExecutionContext) -> CommandResult:
        as_offset = ctx.options.get("offset", False)
        local_dt = datetime.now().astimezone()
        if as_offset:
            offset = local_dt.utcoffset()
            result = int(offset.total_seconds()) if offset else 0
            print(f"  {result}")
            return CommandResult.success(value=result)
        result = local_dt.tzname() or "unknown"
        print(f"  {result}")
        return CommandResult.success(value=result)

    # ── Sleep ─────────────────────────────────────────────────────────────────

    def cmd_sleep(self, ctx: ExecutionContext) -> CommandResult:
        if not ctx.args:
            return CommandResult.error("Usage: time:sleep <seconds>")
        try:
            secs = float(str(ctx.args[0]))
        except (ValueError, TypeError):
            return CommandResult.error(f"Invalid duration: {ctx.args[0]}")
        _time.sleep(secs)
        return CommandResult.success(value=secs)

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _require_dt(self, value):
        """Accept a datetime dict, ISO string, or Unix timestamp float/int.
        Returns (datetime, None) on success, (None, CommandResult.error) on failure."""
        if isinstance(value, dict):
            try:
                return _dict_to_dt(value), None
            except (ValueError, TypeError) as e:
                return None, CommandResult.error(f"Invalid datetime dict: {e}")

        if isinstance(value, (int, float)):
            try:
                return datetime.fromtimestamp(float(value)), None
            except (ValueError, OSError) as e:
                return None, CommandResult.error(f"Invalid timestamp: {e}")

        s = str(value)
        for fmt in _AUTO_FORMATS:
            try:
                return datetime.strptime(s, fmt), None
            except ValueError:
                continue

        return None, CommandResult.error(
            f"Cannot interpret as datetime: '{s}'. "
            "Pass a datetime dict (from time:now/time:parse) or an ISO string."
        )

    @staticmethod
    def _parse_delta(ctx: ExecutionContext) -> timedelta:
        return timedelta(
            weeks=int(ctx.options.get("weeks", 0)),
            days=int(ctx.options.get("days", 0)),
            hours=int(ctx.options.get("hours", 0)),
            minutes=int(ctx.options.get("minutes", 0)),
            seconds=int(ctx.options.get("seconds", 0)),
        )

    def _extract(self, ctx: ExecutionContext, field: str) -> CommandResult:
        cmd = f"time:{field}"
        if not ctx.args:
            return CommandResult.error(f"Usage: {cmd} <dt>")
        dt, err = self._require_dt(ctx.args[0])
        if err:
            return err
        result = getattr(dt, field)() if callable(getattr(dt, field, None)) else getattr(dt, field)
        print(f"  {result}")
        return CommandResult.success(value=result)