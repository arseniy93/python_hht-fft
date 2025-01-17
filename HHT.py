import numpy as np
from scipy.signal import hilbert, stft
from scipy.fft import fft, fftfreq
from PyEMD import EMD



class SignalProcessor:
    def __init__(self, fs, times_list, signal):
        self.fs = fs
        self.t = np.array(times_list)
        self.signal = np.array(signal)
        self.IMFs = None
        self.num_imfs = 0
        self.inst_amplitudes = []
        self.inst_frequencies = []
        self.marginal_spectrum = None

    def set_signal(self, signal_update):
        self.signal = np.array(signal_update)

    def perform_emd(self):
        print("Performing EMD...")
        emd = EMD()
        try:
            self.IMFs = emd(self.signal)
            self.num_imfs = self.IMFs.shape[0]
            print(f'Number of IMFs: {self.num_imfs}')
        except Exception as e:
            print(f"Error during EMD: {e}")
            self.IMFs = None
            self.num_imfs = 0

    def apply_hilbert_transform(self):
        self.inst_amplitudes = []
        self.inst_frequencies = []
        if self.IMFs is not None:
            for i in range(self.num_imfs):
                analytic_signal = hilbert(self.IMFs[i])
                amplitude_envelope = np.abs(analytic_signal)
                instantaneous_phase = np.unwrap(np.angle(analytic_signal))
                instantaneous_freq = (np.diff(instantaneous_phase) / (2.0 * np.pi)) * self.fs
                instantaneous_freq = np.insert(instantaneous_freq, 0, instantaneous_freq[0])
                self.inst_amplitudes.append(amplitude_envelope)
                self.inst_frequencies.append(instantaneous_freq)

    def compute_marginal_spectrum(self):
        if not self.inst_frequencies or not self.inst_amplitudes:
            print("Error: Instantaneous frequencies and amplitudes not computed.")
            return
        freq_bins = np.linspace(0, self.fs / 2, self.fs // 2 + 1)
        marginal_spectrum = np.zeros_like(freq_bins)
        for i in range(self.num_imfs):
            amp = self.inst_amplitudes[i]
            freq = self.inst_frequencies[i]
            epsilon = 1e-6
            freq_binned = np.digitize(freq + epsilon, freq_bins) - 1
            freq_binned = np.clip(freq_binned, 0, len(freq_bins) - 1)
            for j in range(len(amp)):
                marginal_spectrum[freq_binned[j]] += amp[j]
        self.marginal_spectrum = marginal_spectrum / np.max(marginal_spectrum) if np.max(marginal_spectrum) > 0 else marginal_spectrum

    def perform_stft(self):
        f, t_stft, Zxx = stft(self.signal, self.fs, nperseg=256, noverlap=128)
        return f, t_stft, Zxx

    def perform_fft(self):
        yf = fft(self.signal)
        xf = fftfreq(len(self.signal), 1 / self.fs)
        magnitude_spectrum = np.abs(yf)
        return xf, magnitude_spectrum
    def perform_fft_in(self, imfs):
        yf = fft(imfs)
        xf = np.abs(fftfreq(len(imfs), 1 / self.fs))
        magnitude_spectrum = np.abs(yf)
        return xf, magnitude_spectrum




