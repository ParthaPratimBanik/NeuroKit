# -*- coding: utf-8 -*-
import numpy as np
import pandas as pd

from ..hrv import hrv


def ppg_intervalrelated(data, sampling_rate=1000):
    """**Performs PPG analysis on longer periods of data (typically > 10 seconds), such as
    resting-state data**

    Parameters
    ----------
    data : Union[dict, pd.DataFrame]
        A DataFrame containing the different processed signal(s) as different columns, typically
        generated by :func:`.ppg_process`. Can also take a dict containing sets of
        separately processed DataFrames.
    sampling_rate : int
        The sampling frequency of the signal (in Hz, i.e., samples/second).

    Returns
    -------
    DataFrame
        A dataframe containing the analyzed PPG features. The analyzed features consist of the following:

        * ``"PPG_Rate_Mean"``: the mean heart rate.

        * ``"HRV"``: the different heart rate variability metrices.

        See :func:`.hrv` docstrings for details.

    See Also
    --------
    ppg_process

    Examples
    ----------
    .. ipython:: python

      import neurokit2 as nk

      # Download data
      data = nk.data("bio_resting_5min_100hz")

      # Process the data
      df, info = nk.ppg_process(data["PPG"], sampling_rate=100)

      # Single dataframe is passed
      nk.ppg_intervalrelated(df, sampling_rate=100)

      epochs = nk.epochs_create(df, events=[0, 15000], sampling_rate=100,
                                epochs_end=150)
      nk.ppg_intervalrelated(epochs)


    """
    intervals = {}

    # Format input
    if isinstance(data, pd.DataFrame):
        rate_cols = [col for col in data.columns if "PPG_Rate" in col]
        if len(rate_cols) == 1:
            intervals.update(_ppg_intervalrelated_formatinput(data))
            intervals.update(_ppg_intervalrelated_hrv(data, sampling_rate))
        else:
            raise ValueError(
                "NeuroKit error: ppg_intervalrelated(): Wrong input,"
                "we couldn't extract heart rate. Please make sure"
                "your DataFrame contains a `PPG_Rate` column."
            )
        ppg_intervals = pd.DataFrame.from_dict(intervals, orient="index").T

    elif isinstance(data, dict):
        for index in data:
            intervals[index] = {}  # Initialize empty container

            # Add label info
            intervals[index]["Label"] = data[index]["Label"].iloc[0]

            # Rate
            intervals[index] = _ppg_intervalrelated_formatinput(
                data[index], intervals[index]
            )

            # HRV
            intervals[index] = _ppg_intervalrelated_hrv(
                data[index], sampling_rate, intervals[index]
            )

        ppg_intervals = pd.DataFrame.from_dict(intervals, orient="index")

    return ppg_intervals


# =============================================================================
# Internals
# =============================================================================


def _ppg_intervalrelated_formatinput(data, output={}):

    # Sanitize input
    colnames = data.columns.values
    if len([i for i in colnames if "PPG_Rate" in i]) == 0:
        raise ValueError(
            "NeuroKit error: ppg_intervalrelated(): Wrong input,"
            "we couldn't extract heart rate. Please make sure"
            "your DataFrame contains a `PPG_Rate` column."
        )
    signal = data["PPG_Rate"].values
    output["PPG_Rate_Mean"] = np.mean(signal)

    return output


def _ppg_intervalrelated_hrv(data, sampling_rate, output={}):

    # Sanitize input
    colnames = data.columns.values
    if len([i for i in colnames if "PPG_Peaks" in i]) == 0:
        raise ValueError(
            "NeuroKit error: ppg_intervalrelated(): Wrong input,"
            "we couldn't extract peaks. Please make sure"
            "your DataFrame contains a `PPG_Peaks` column."
        )

    # Transform rpeaks from "signal" format to "info" format.
    peaks = np.where(data["PPG_Peaks"].values)[0]
    peaks = {"PPG_Peaks": peaks}

    results = hrv(peaks, sampling_rate=sampling_rate)
    for column in results.columns:
        output[column] = results[column].values.astype("float")

    return output
