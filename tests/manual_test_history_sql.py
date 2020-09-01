import BAC0
import time

bacnet = BAC0.lite()

pcv = BAC0.device("303:12", 5012, bacnet)
for _ in range(4):
    pcv["SUPHTG1-C"] = True
    time.sleep(1)

pcv.backup_histories_df()
