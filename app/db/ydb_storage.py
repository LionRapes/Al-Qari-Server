"""Yandex Database (YDB) storage implementation with linter override for dynamic modules."""

import os
import time

import ydb

from app.core.config import YDB_SETTINGS
from app.core.interfaces import YdbInterface

MAX_CONNECTION_RETRIES = 3
RETRY_DELAY = 2


class YandexYdbStorage(YdbInterface):
    """YDB database client manager using session pools and drivers."""

    def __init__(self):
        """Initialize the YDB driver and session pool."""
        endpoint = YDB_SETTINGS.ydb_endpoint
        database = YDB_SETTINGS.ydb_database

        key_file = YDB_SETTINGS.ydb_service_account_key_file

        if key_file and os.path.exists(key_file):
            credentials = ydb.iam.ServiceAccountCredentials.from_file(key_file)
        else:
            credentials = ydb.iam.MetadataUrlCredentials()

        driver_config = ydb.DriverConfig(endpoint=endpoint, database=database, credentials=credentials)
        self.driver = ydb.Driver(driver_config)

        for attempt in range(1, MAX_CONNECTION_RETRIES + 1):
            try:
                self.driver.wait(timeout=5, fail_fast=True)
                break
            except TimeoutError as exc:
                if attempt == MAX_CONNECTION_RETRIES:
                    raise RuntimeError(f"Error connecting YDB after {MAX_CONNECTION_RETRIES} attempts") from exc

                time.sleep(RETRY_DELAY)

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
