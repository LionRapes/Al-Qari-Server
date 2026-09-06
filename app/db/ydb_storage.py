"""Yandex Database (YDB) storage implementation with linter override for dynamic modules."""

import os

import ydb

from app.core.config import YDB_SETTINGS
from app.core.interfaces import YdbInterface


class YandexYdbStorage(YdbInterface):
    """YDB database client manager using session pools and drivers."""

    def __init__(self):
        """Initialize the YDB driver and session pool."""
        endpoint = YDB_SETTINGS.YDB_ENDPOINT
        database = YDB_SETTINGS.YDB_DATABASE

        key_file = os.getenv("YDB_SERVICE_ACCOUNT_KEY_FILE")

        if key_file and os.path.exists(key_file):
            credentials = ydb.iam.ServiceAccountCredentials.from_file(key_file)
        else:
            credentials = ydb.iam.MetadataUrlCredentials()

        driver_config = ydb.DriverConfig(endpoint=endpoint, database=database, credentials=credentials)
        self.driver = ydb.Driver(driver_config)

        try:
            self.driver.wait(timeout=5, fail_fast=True)
        except TimeoutError as exc:
            raise RuntimeError("Error connecting YDB") from exc

        self.pool = ydb.SessionPool(self.driver)

    def execute(self, query: str, parameters: dict | None = None) -> list:
        """Execute a query against YDB using a session pool and transaction retry."""

        def callee(session: ydb.Session):
            prepared = session.prepare(query)

            result_sets = session.transaction().execute(prepared, parameters, commit_tx=True)
            return result_sets

        result = self.pool.retry_operation_sync(callee)

        if result and len(result) > 0:
            return result[0].rows
        return []

    def close(self):
        """Gracefully close the session pool and YDB driver."""
        self.pool.stop()
        self.driver.stop()
