import asyncio
from pg_perfbench.run import execute_pg_perfbench


if __name__ == "__main__":
    # run the asynchronous entry point
    asyncio.run(execute_pg_perfbench())
