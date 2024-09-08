#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2015 by Christian Tremblay, P.Eng <christian.tremblay@servisys.com>
# Licensed under LGPLv3, see file LICENSE in this source tree.
#
"""
sql.py -
"""

import os.path

# --- standard Python modules ---
import pickle

# --- 3rd party modules ---
import aiosqlite

from ..core.io.IOExceptions import (
    DataError,
    NoResponseFromController,
    RemovedPointException,
)
from ..core.utils.lookfordependency import pandas_if_available

_PANDAS, pd, sql, Timestamp = pandas_if_available()
# --- this application's modules ---

# ------------------------------------------------------------------------------


class SQLMixin(object):
    """
    Use SQL to persist a device's contents.  By saving the device contents to an SQL
    database, you can work with the device's data while offline, or while the device
    is not available.
    """

    async def _read_from_sql(self, request, db_name):
        """
        Using the contextlib, I hope to close the connection to database when
        not in use
        """
        async with aiosqlite.connect(f"{db_name}.db") as con:
            async with con.execute(request) as cursor:
                rows = await cursor.fetchall()
                columns = [description[0] for description in cursor.description]
                return pd.DataFrame(rows, columns=columns)

    def dev_properties_df(self):
        dic = self.properties.asdict.copy()
        dic.pop("network", None)
        dic["objects_list"] = []
        dic.pop("pss", None)
        return dic

    def points_properties_df(self):
        """
        Return a dictionary of point/point_properties in preparation for storage in SQL.
        """
        pprops = {}
        for each in self.points:
            p = each.properties.asdict.copy()
            p.pop("device", None)
            p.pop("network", None)
            p.pop("simulated", None)
            p.pop("overridden", None)
            pprops[str(each.properties.name)] = p

        return pd.DataFrame(pprops)

    def backup_histories_df(self, resampling="1s"):
        """
        Build a dataframe of the point histories
        By default, dataframe will be resampled for 1sec intervals,
        NaN will be forward filled then backward filled. This way, no
        NaN values will remains and analytics will be easier.

        Please note that this can be disabled using resampling=False

        In the process of building the dataframe, analog values are
        resampled using the mean() function. So we have intermediate
        results between to records.

        For binary values, we'll use .last() so we won't get a 0.5 value
        which means nothing in this context.

        If saving a DB that already exists, previous resampling will survive
        the merge of old data and new data.
        """
        if not _PANDAS:
            self.log("Pandas is required to create dataframe.", level="error")
            return
        backup = {}
        if isinstance(resampling, str):
            resampling_needed = True
            resampling_freq = resampling
        elif resampling in [0, False]:
            resampling_needed = False

        def extract_value_and_string(val):
            if isinstance(val, str):
                if ":" in val:
                    _v, _s = val.split(":")
                    return (int(_v), _s)
                elif val == "active":
                    val = 1
                elif val == "inactive":
                    val = 0
            return (int(val), "unknown")

        # print(resampling, resampling_freq, resampling_needed)
        for point in self.points:
            _name = str(point.properties.name)
            try:
                if (
                    "binary" in point.properties.type
                    or "multi" in point.properties.type
                ):
                    backup[f"{_name}_str"] = (
                        point.history.apply(lambda x: extract_value_and_string(x)[1])
                        .resample(resampling_freq)
                        .last()
                    )
                    backup[_name] = (
                        point.history.apply(lambda x: extract_value_and_string(x)[0])
                        .resample(resampling_freq)
                        .last()
                    )
                elif resampling_needed and "analog" in point.properties.type:
                    backup[_name] = point.history.resample(resampling_freq).mean()
                else:
                    # backup[point.properties.name] = point.history.resample(
                    #    resampling_freq
                    # ).last()
                    continue

            except Exception as error:
                try:
                    self.log(
                        f"{self.properties.name} ({self.properties.device.properties.address}) | Error in resampling {point.properties.name} | {error} (probably not enough points)",
                        level="error",
                    )
                except AttributeError as error:
                    raise DataError(
                        f"Cannot save, missing required information : {error}"
                    )
                if (
                    "binary" in point.properties.type
                    or "multi" in point.properties.type
                ):
                    backup[f"{_name}.str"] = (
                        point.history.apply(lambda x: extract_value_and_string(x)[1])
                        .resample(resampling_freq)
                        .last()
                    )
                    backup[f"{_name}.val"] = (
                        point.history.apply(lambda x: extract_value_and_string(x)[0])
                        .resample(resampling_freq)
                        .last()
                    )
                    backup[_name] = point.history.resample(resampling_freq).last()
                elif "analog" in point.properties.type:
                    backup[_name] = point.history.resample(resampling_freq).mean()
                else:
                    # backup[point.properties.name] = point.history
                    continue

        df = pd.DataFrame(dict([(k, pd.Series(v)) for k, v in backup.items()]))
        if resampling_needed:
            return df.resample(resampling_freq).last().ffill().bfill()
        else:
            return df

    async def save(self, filename=None, resampling=None):
        """
        Save the point histories to sqlite3 database.
        Save the device object properties to a pickle file so the device can be reloaded.

        Resampling : valid Pandas resampling frequency. If 0 or False, dataframe will not be resampled on save.
        """
        if not _PANDAS:
            self.log("Pandas is required to save to SQLite.", level="error")
            return

        if filename:
            if ".db" in filename:
                filename = filename.split(".")[0]
            self.properties.db_name = filename
        else:
            self.properties.db_name = f"Device_{self.properties.device_id}"

        if resampling is None:
            resampling = self.properties.save_resampling

        # Does file exist? If so, append data

        def _df_to_backup():
            try:
                return self.backup_histories_df(resampling=resampling)
            except (DataError, NoResponseFromController):
                self.log("Impossible to save right now, error in data", level="error")
                return pd.DataFrame()

        if os.path.isfile(f"{self.properties.db_name}.db"):
            try:
                his = await self._read_from_sql(
                    'select * from "history"', self.properties.db_name
                )
                his.index = his["index"].apply(Timestamp)
                last = his.index[-1]
                df_to_backup = _df_to_backup()[last:]
            except Exception:
                df_to_backup = _df_to_backup()

        else:
            self.log("Creating a new backup database", level="debug")
            df_to_backup = _df_to_backup()

        if df_to_backup is None:
            return
        # DataFrames that will be saved to SQL
        async with aiosqlite.connect(f"{self.properties.db_name}.db") as con:
            try:
                async with con.execute("SELECT * FROM history") as cursor:
                    data = await cursor.fetchall()
                    columns = [description[0] for description in cursor.description]
                    data = pd.DataFrame(data, columns=columns)
                    df = pd.concat([data, df_to_backup], sort=True)
                    sql.to_sql(
                        df_to_backup,
                        name="history",
                        con=con,
                        index_label="index",
                        index=True,
                        if_exists="append",
                    )
            except Exception:
                # df = df_to_backup
                self._log.error("Error saving to SQL database")

            # asyncio.run(
            #    None, df_to_backup.to_sql, "history", con, None, "append", True, "index"
            # )

        # Saving other properties to a pickle file...
        prop_backup = {"device": self.dev_properties_df()}
        prop_backup["points"] = self.points_properties_df()
        try:
            with open(f"{self.properties.db_name}.bin", "wb") as file:
                pickle.dump(prop_backup, file)
            if self.properties.clear_history_on_save:
                self.clear_histories()

            self.log(f"Device saved to {self.properties.db_name}.db", level="info")
        except Exception as error:
            self._log.error(f"Error saving to pickle file: {error}")

    async def points_from_sql(self, db_name):
        """
        Retrieve point list from SQL database
        """
        try:
            points = await self._read_from_sql("SELECT * FROM history;", db_name)
            return list(points.columns.values)[1:]
        except Exception:
            self._log.warning(f"No history retrieved from {db_name}.db:")
            return []

    async def his_from_sql(self, db_name, point):
        """
        Retrive point histories from SQL database
        """
        his = await self._read_from_sql('select * from "history"', db_name)
        his.index = his["index"].apply(Timestamp)
        return his.set_index("index")[point]

    async def value_from_sql(self, db_name, point):
        """
        Take last known value as the value
        """
        return await self.his_from_sql(db_name, point).last_valid_index()

    def read_point_prop(self, device_name, point):
        """
        Points properties retrieved from pickle
        """
        with open(f"{device_name}.bin", "rb") as file:
            try:
                _point = pickle.load(file)["points"][point]
            except KeyError:
                raise RemovedPointException(f"{point} not found (probably deleted)")
            return _point

    def read_dev_prop(self, device_name):
        """
        Device properties retrieved from pickle
        """
        self.log("Reading prop from DB file", level="debug")
        try:
            with open(f"{device_name}.bin", "rb") as file:
                return pickle.load(file)["device"]
        except (EOFError, FileNotFoundError):
            self._log.error("Error reading device properties")
            raise ValueError
