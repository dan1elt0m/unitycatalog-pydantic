import asyncio

import pytest
import pytest_asyncio
from pyspark.sql import SparkSession
from testcontainers.core.container import DockerContainer
import logging
from testcontainers.core.waiting_utils import wait_for_logs
from unitycatalog.client import Configuration, ApiClient

logging.basicConfig(level=logging.INFO)

version = "0.2.1"
unity_catalog_container = DockerContainer(f"godatadriven/unity-catalog:{version}")

@pytest.fixture(scope="module")
def event_loop():
    loop = asyncio.get_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="module")
def unity_catalog():
    unity_catalog_container.with_exposed_ports(8080).start()
    wait_for_logs(unity_catalog_container, version, 30)
    yield
    unity_catalog_container.stop()


@pytest_asyncio.fixture(scope="module")
async def catalog_client(unity_catalog) -> ApiClient:
    logging.debug("Getting exposed port...")
    port = unity_catalog_container.get_exposed_port(8080)
    logging.debug(f"Exposed port: {port}")
    config = Configuration(
        host=f"http://{unity_catalog_container.get_container_host_ip()}:{port}/api/2.1/unity-catalog"
    )
    yield ApiClient(config)


@pytest_asyncio.fixture(scope="module")
async def spark(unity_catalog):
    uri = f"http://{unity_catalog_container.get_container_host_ip()}:{unity_catalog_container.get_exposed_port(8080)}"
    spark = (
        SparkSession.builder.appName("local-uc-test")
        .master("local[*]")
        .config(
            "spark.jars.packages",
            "io.delta:delta-spark_2.12:3.2.1,io.unitycatalog:unitycatalog-spark_2.12:0.2.0",
        )
        .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension")
        .config(
            "spark.sql.catalog.spark_catalog", "io.unitycatalog.spark.UCSingleCatalog"
        )
        .config("spark.sql.catalog.unity", "io.unitycatalog.spark.UCSingleCatalog")
        .config("spark.sql.catalog.unity.uri", uri)
        .config("spark.sql.catalog.unity.token", "")
        .config("spark.sql.defaultCatalog", "unity")
        .config(
            "spark.driver.extraJavaOptions",
            "-Dio.netty.tryReflectionSetAccessible=true",
        )
        .config(
            "spark.executor.extraJavaOptions",
            "-Dio.netty.tryReflectionSetAccessible=true",
        )
        .getOrCreate()
    )
    yield spark
    spark.stop()
