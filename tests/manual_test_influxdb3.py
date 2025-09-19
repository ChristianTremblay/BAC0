import BAC0
from BAC0.scripts.script_runner import run
import asyncio

bacnet = None

async def main():
    global bacnet
    db_params = {
        "version": 3,
        #"bucket": "BAC0_006s",
        "name": "InfluxDB",
        "database": "BAC0",
        "table": "client_006s"
        # other parameters are in the .env files so password are not shown here
    }
    #bacnet = BAC0.start(ip='10.138.103.17/16',db_params=db_params)
    async with BAC0.start(ip='192.168.211.208/24',db_params=db_params) as bacnet:

        cgm = await BAC0.device('303:4', 5221, bacnet, poll=10, history_size=500) # noqa F841

        while True:
            await asyncio.sleep(1)

if __name__ == "__main__":
    run(main, bacnet)