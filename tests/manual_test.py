import asyncio

import BAC0
from BAC0.scripts.script_runner import run

bacnet = None


async def main():
    # Configuration
    # # Initialize BACnet
    print(BAC0.infos.__version__)

    async with BAC0.start(ip="127.0.0.1/24") as bacnet:

        await bacnet._discover()
        lst = await bacnet._devices(_return_list=True)
        print(lst)


if __name__ == "__main__":
    # run(main, bacnet) # Run the script and deals with SIGINT and SIGTERM, useful for long time runnign scripts.
    asyncio.run(main())
