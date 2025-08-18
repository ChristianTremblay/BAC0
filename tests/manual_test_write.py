import asyncio

import BAC0

bacnet = None


async def main():
    # Configuration
    # # Initialize BACnet
    print(BAC0.infos.__version__)

    # async with BAC0.start(ip="127.0.0.1/24") as bacnet:
    async with BAC0.start(ip="192.168.4.2/24") as bacnet:
        await bacnet.use_router(("192.168.1.150:47808", 3))
        # c = await BAC0.device('3:10', 5310, bacnet)

        # bacnet.write('303:9 binaryValue 10998 presentValue active')
        bacnet.write("3:10 binaryValue 14 presentValue active")

        await asyncio.sleep(2)
        # await bacnet._write('303:9 binaryValue 10998 presentValue inactive')
        await bacnet._write("3:10 binaryValue 14 presentValue inactive")

        await asyncio.sleep(2)


if __name__ == "__main__":
    # run(main, bacnet) # Run the script and deals with SIGINT and SIGTERM, useful for long time runnign scripts.
    asyncio.run(main())
