import asyncio

import BAC0

bacnet = None


async def main():
    # Configuration
    # # Initialize BACnet
    print(BAC0.infos.__version__)

    # async with BAC0.start(ip="127.0.0.1/24") as bacnet:
    async with BAC0.start() as bacnet:
        # await bacnet.use_router(("192.168.1.150:47808", 3))
        c = await BAC0.device("3:10", 5310, bacnet)
        print("======== SETTING OVERRIDE to 40 ========")
        c["CLG-O"] = 40
        await asyncio.sleep(2)
        print("======== FINDING OVERRIDES ========")
        c.find_overrides()
        # bacnet.write('303:9 binaryValue 10998 presentValue active')
        while c._find_overrides_running:
            await asyncio.sleep(1)
        print("======== RESULT ========")
        print(c.properties.points_overridden)
        variable_in_result = c["CLG-O"] in c.properties.points_overridden
        print(f"CLG-O in the list : {variable_in_result}")
        print("======== RESULT ========")
        c.release_all_overrides()
        while c._release_overrides_running:
            await asyncio.sleep(1)

        # bacnet.write('303:9 binaryValue 10998 presentValue active')
        c.find_overrides()
        while c._find_overrides_running:
            await asyncio.sleep(1)

        variable_in_result = c["CLG-O"] in c.properties.points_overridden
        print("======== FINAL RESULT ========")
        print(c.properties.points_overridden)
        print(f"CLG-O in the list : {variable_in_result} <= SHOULD NOT")

        while True:
            await asyncio.sleep(0.5)


if __name__ == "__main__":
    # run(main, bacnet) # Run the script and deals with SIGINT and SIGTERM, useful for long time runnign scripts.
    asyncio.run(main())
