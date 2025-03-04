# -*- coding: utf-8 -*-
import pandas as pd

from ..signal import signal_rate, signal_sanitize
from .ecg_clean import ecg_clean
from .ecg_delineate import ecg_delineate
from .ecg_peaks import ecg_peaks
from .ecg_phase import ecg_phase
from .ecg_quality import ecg_quality


def ecg_process(ecg_signal, sampling_rate=1000, method="neurokit"):
    """**Automated pipeline for preprocessing an ECG signal**

    This function runs different preprocessing steps. **Help us improve the documentation of
    this function by making it more tidy and useful!**

    Parameters
    ----------
    ecg_signal : Union[list, np.array, pd.Series]
        The raw ECG channel.
    sampling_rate : int
        The sampling frequency of ``ecg_signal`` (in Hz, i.e., samples/second). Defaults to 1000.
    method : str
        The processing pipeline to apply. Defaults to ``"neurokit"``. We aim at improving this
        aspect to make the available methods more transparent, and be able to generate specific
        reports. Please get in touch if you are interested in helping out with this.

    Returns
    -------
    signals : DataFrame
        A DataFrame of the same length as the ``ecg_signal`` containing the following columns:

        * ``"ECG_Raw"``: the raw signal.
        * ``"ECG_Clean"``: the cleaned signal.
        * ``"ECG_R_Peaks"``: the R-peaks marked as "1" in a list of zeros.
        * ``"ECG_Rate"``: heart rate interpolated between R-peaks.
        * ``"ECG_P_Peaks"``: the P-peaks marked as "1" in a list of zeros
        * ``"ECG_Q_Peaks"``: the Q-peaks marked as "1" in a list of zeros .
        * ``"ECG_S_Peaks"``: the S-peaks marked as "1" in a list of zeros.
        * ``"ECG_T_Peaks"``: the T-peaks marked as "1" in a list of zeros.
        * ``"ECG_P_Onsets"``: the P-onsets marked as "1" in a list of zeros.
        * ``"ECG_P_Offsets"``: the P-offsets marked as "1" in a list of zeros (only when method in
          ``ecg_delineate()`` is wavelet).
        * ``"ECG_T_Onsets"``: the T-onsets marked as "1" in a list of zeros (only when method in
          ``ecg_delineate()`` is wavelet).
        * ``"ECG_T_Offsets"``: the T-offsets marked as "1" in a list of zeros.
        * ``"ECG_R_Onsets"``: the R-onsets marked as "1" in a list of zeros (only when method in
          ``ecg_delineate()`` is wavelet).
        * ``"ECG_R_Offsets"``: the R-offsets marked as "1" in a list of zeros (only when method in
          ``ecg_delineate()`` is wavelet).
        * ``"ECG_Phase_Atrial"``: cardiac phase, marked by "1" for systole and "0" for diastole.
        * ``"ECG_Phase_Ventricular"``: cardiac phase, marked by "1" for systole and "0" for
          diastole.
        * ``"ECG_Atrial_PhaseCompletion"``: cardiac phase (atrial) completion, expressed in
          percentage
          (from 0 to 1), representing the stage of the current cardiac phase.
        * ``"ECG_Ventricular_PhaseCompletion"``: cardiac phase (ventricular) completion, expressed
          in percentage (from 0 to 1), representing the stage of the current cardiac phase.
        * **This list is not up-to-date. Help us improve the documentation!**
    info : dict
        A dictionary containing the samples at which the R-peaks occur, accessible with the key
        ``"ECG_R_Peaks"``, as well as the signals' sampling rate.

    See Also
    --------
    ecg_clean, ecg_peaks, ecg_delineate, ecg_phase, ecg_plot, .signal_rate

    Examples
    --------
    .. ipython:: python

      import neurokit2 as nk

      # Simulate ECG signal
      ecg = nk.ecg_simulate(duration=15, sampling_rate=1000, heart_rate=80)

      # Preprocess ECG signal
      signals, info = nk.ecg_process(ecg, sampling_rate=1000)

      # Visualize
      @savefig p_ecg_process.png scale=100%
      nk.ecg_plot(signals)
      @suppress
      plt.close()

    """
    # Sanitize input
    ecg_signal = signal_sanitize(ecg_signal)

    ecg_cleaned = ecg_clean(ecg_signal, sampling_rate=sampling_rate, method=method)
    # R-peaks
    (instant_peaks, rpeaks,) = ecg_peaks(
        ecg_cleaned=ecg_cleaned, sampling_rate=sampling_rate, method=method, correct_artifacts=True
    )

    rate = signal_rate(rpeaks, sampling_rate=sampling_rate, desired_length=len(ecg_cleaned))

    quality = ecg_quality(ecg_cleaned, rpeaks=rpeaks["ECG_R_Peaks"], sampling_rate=sampling_rate)

    signals = pd.DataFrame(
        {"ECG_Raw": ecg_signal, "ECG_Clean": ecg_cleaned, "ECG_Rate": rate, "ECG_Quality": quality}
    )

    # Additional info of the ecg signal
    delineate_signal, delineate_info = ecg_delineate(
        ecg_cleaned=ecg_cleaned, rpeaks=rpeaks, sampling_rate=sampling_rate
    )

    cardiac_phase = ecg_phase(ecg_cleaned=ecg_cleaned, rpeaks=rpeaks, delineate_info=delineate_info)

    signals = pd.concat([signals, instant_peaks, delineate_signal, cardiac_phase], axis=1)

    # Rpeaks location and sampling rate in dict info
    info = rpeaks
    info["sampling_rate"] = sampling_rate

    return signals, info
