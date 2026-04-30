from importlib.metadata import PackageNotFoundError, version

try:
    from reo_census import ReoEventLogger

    try:
        _pkg_version = version("langchain-couchbase")
    except PackageNotFoundError:
        _pkg_version = "0.0.0"

    _logger = ReoEventLogger(
        endpoint_url="https://telemetry.reo.dev/data",
        timeout=3.0,
        package_name="langchain-couchbase",
        package_version=_pkg_version,
    )
    _logger.log_event()
except Exception:
    pass
