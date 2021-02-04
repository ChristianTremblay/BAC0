#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2015 by Christian Tremblay, P.Eng <christian.tremblay@servisys.com>
# Licensed under LGPLv3, see file LICENSE in this source tree.
#
"""
sql.py - 
"""

# --- standard Python modules ---
import pickle
import os.path

# --- 3rd party modules ---
import sqlite3
import contextlib

try:
    import pandas as pd
    from pandas.io import sql

    try:
        from pandas import Timestamp
    except ImportError:
        from pandas.lib import Timestamp
    _PANDAS = True
except ImportError:
    _PANDAS = False

from ..core.io.IOExceptions import RemovedPointException

# --- this application's modules ---

# ------------------------------------------------------------------------------


class SQLMixin(object):
    """
    Use SQL to persist a device's contents.  By saving the device contents to an SQL 
    database, you can work with the device's data while offline, or while the device 
    is not available. 
    """

    def _read_from_sql(self, request, db_name):
        """
        Using the contextlib, I hope to close the connection to database when
        not in use
        """
        with contextlib.closing(sqlite3.connect("{}.db".format(db_name))) as con:
            return sql.read_sql(sql=request, con=con)

    def dev_properties_df(self):
        dic = self.properties.asdict.copy()
        dic.pop("network", None)
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
            pprops[each.properties.name] = p

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
        backup = {}
        if isinstance(resampling, str):
            resampling_needed = True
            resampling_freq = resampling
        elif resampling in [0, False]:
            resampling_needed = False

        # print(resampling, resampling_freq, resampling_needed)
        for point in self.points:
            try:
                if resampling_needed and "binary" in point.properties.type:
                    backup[point.properties.name] = (
                        point.history.replace(["inactive", "active"], [0, 1])
                        .resample(resampling_freq)
                        .last()
                    )
                elif resampling_needed and "analog" in point.properties.type:
                    backup[point.properties.name] = point.history.resample(
                        resampling_freq
                    ).mean()
                else:
                    backup[point.properties.name] = point.history.resample(
                        resampling_freq
                    ).last()

            except Exception as error:
                self._log.error(
                    "Error in resampling {} | {} (probably not enough points)".format(
                        point, error
                    )
                )
                if "binary" in point.properties.type:
                    backup[point.properties.name] = point.history.replace(
                        ["inactive", "active"], [0, 1]
                    )
                elif "analog" in point.properties.type:
                    backup[point.properties.name] = point.history.resample(
                        resampling_freq
                    ).mean()
                else:
                    backup[point.properties.name] = point.history

        df = pd.DataFrame(dict([(k, pd.Series(v)) for k, v in backup.items()]))
        if resampling_needed:
            return (
                df.resample(resampling_freq)
                .last()
                .fillna(method="ffill")
                .fillna(method="bfill")
            )
        else:
            return df

    def save(self, filename=None, resampling=None):
        """
        Save the point histories to sqlite3 database.  
        Save the device object properties to a pickle file so the device can be reloaded.

        Resampling : valid Pandas resampling frequency. If 0 or False, dataframe will not be resampled on save.
        """
        if filename:
            if ".db" in filename:
                filename = filename.split(".")[0]
            self.properties.db_name = filename
        else:
            self.properties.db_name = "dev_{}".format(self.properties.device_id)

        if resampling is None:
            resampling = self.properties.save_resampling

        # Does file exist? If so, append data
        if os.path.isfile("{}.db".format(self.properties.db_name)):
            his = self._read_from_sql(
                'select * from "{}"'.format("history"), self.properties.db_name
            )
            his.index = his["index"].apply(Timestamp)
            try:
                last = his.index[-1]
                df_to_backup = self.backup_histories_df(resampling=resampling)[last:]
            except IndexError:
                df_to_backup = self.backup_histories_df(resampling=resampling)

        else:
            self._log.debug("Creating a new backup database")
            df_to_backup = self.backup_histories_df(resampling=resampling)

        # DataFrames that will be saved to SQL
        with contextlib.closing(
            sqlite3.connect("{}.db".format(self.properties.db_name))
        ) as con:
            try:
                data = pd.read_sql("SELECT * FROM history", con)
                df = pd.concat([data, df_to_backup], sort=True)
            except:
                df = df_to_backup

            sql.to_sql(
                df_to_backup,
                name="history",
                con=con,
                index_label="index",
                index=True,
                if_exists="append",
            )

        # Saving other properties to a pickle file...
        prop_backup = {"device": self.dev_properties_df()}
        prop_backup["points"] = self.points_properties_df()
        with open("{}.bin".format(self.properties.db_name), "wb") as file:
            pickle.dump(prop_backup, file)

        if self.properties.clear_history_on_save:
            self.clear_histories()

        self._log.info("Device saved to {}.db".format(self.properties.db_name))

    def points_from_sql(self, db_name):
        """
        Retrieve point list from SQL database
        """
        points = self._read_from_sql("SELECT * FROM history;", db_name)
        return list(points.columns.values)[1:]

    def his_from_sql(self, db_name, point):
        """
        Retrive point histories from SQL database
        """
        his = self._read_from_sql('select * from "{}"'.format("history", db_name))
        his.index = his["index"].apply(Timestamp)
        return his.set_index("index")[point]

    def value_from_sql(self, db_name, point):
        """
        Take last known value as the value
        """
        return self.his_from_sql(db_name, point).last_valid_index()

    def read_point_prop(self, device_name, point):
        """
        Points properties retrieved from pickle
        """
        with open("{}.bin".format(device_name), "rb") as file:
            try:
                _point = pickle.load(file)["points"][point]
            except KeyError:
                raise RemovedPointException(
                    "{} not found (probably deleted)".format(point)
                )
            return _point

    def read_dev_prop(self, device_name):
        """
        Device properties retrieved from pickle
        """
        self._log.debug("Reading prop from DB file")
        with open("{}.bin".format(device_name), "rb") as file:
            return pickle.load(file)["device"]
