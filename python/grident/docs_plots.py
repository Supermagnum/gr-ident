"""Generate spectrogram and time-domain plots for gr-ident IQ captures (stdlib only)."""

from __future__ import annotations

import cmath
import math
import subprocess
from pathlib import Path

from .iq_samples import IqSamples

WATERFALL_WIDTH_HZ = 14000.0
DEFAULT_SAMPLE_RATE = 48000
WATERFALL_TARGET_HEIGHT = 480


def _next_pow2(n: int) -> int:
    p = 1
    while p < n:
        p <<= 1
    return p


def _fft(x: list[complex]) -> list[complex]:
    n = len(x)
    if n == 1:
        return x
    if n % 2:
        raise ValueError("FFT length must be a power of 2")
    even = _fft(x[0::2])
    odd = _fft(x[1::2])
    out = [0j] * n
    for k in range(n // 2):
        tw = cmath.exp(-2j * math.pi * k / n)
        t = tw * odd[k]
        out[k] = even[k] + t
        out[k + n // 2] = even[k] - t
    return out


def _fftshift(values: list[complex]) -> list[complex]:
    n = len(values)
    half = n // 2
    return values[half:] + values[:half]


def _hann(n: int) -> list[float]:
    if n <= 1:
        return [1.0] * n
    return [0.5 - 0.5 * math.cos(2.0 * math.pi * i / (n - 1)) for i in range(n)]


def _power_db(values: list[complex]) -> list[float]:
    floor = 1e-20
    return [10.0 * math.log10(abs(v) ** 2 + floor) for v in values]


def stft_power_db(
    samples: list[complex],
    sample_rate: int = DEFAULT_SAMPLE_RATE,
    nfft: int = 2048,
    hop: int | None = None,
) -> tuple[list[list[float]], list[float], list[float]]:
    """Return (power_db[time][freq], time_seconds, frequencies_hz)."""
    hop = hop or nfft // 4
    window = _hann(nfft)

    frames: list[list[float]] = []
    times: list[float] = []
    freqs = [((i - nfft // 2) * sample_rate / nfft) for i in range(nfft)]

    pos = 0
    while pos + nfft <= len(samples):
        chunk = samples[pos : pos + nfft]
        framed = [chunk[i] * window[i] for i in range(nfft)]
        spectrum = _fftshift(_fft(framed))
        frames.append(_power_db(spectrum))
        times.append((pos + nfft / 2) / sample_rate)
        pos += hop

    if not frames:
        padded = samples + [0j] * max(0, nfft - len(samples))
        framed = [padded[i] * window[i] for i in range(nfft)]
        spectrum = _fftshift(_fft(framed))
        frames.append(_power_db(spectrum))
        times.append(nfft / (2 * sample_rate))

    return frames, times, freqs


def _crop_waterfall(
    frames: list[list[float]],
    freqs: list[float],
    half_width_hz: float = WATERFALL_WIDTH_HZ / 2.0,
) -> tuple[list[list[float]], list[float]]:
    indices = [i for i, f in enumerate(freqs) if -half_width_hz <= f <= half_width_hz]
    if not indices:
        return frames, freqs
    lo, hi = indices[0], indices[-1] + 1
    return [row[lo:hi] for row in frames], freqs[lo:hi]


def _normalize_grid(grid: list[list[float]], floor_db: float, ceil_db: float) -> list[list[float]]:
    out: list[list[float]] = []
    for row in grid:
        norm_row: list[float] = []
        for value in row:
            if value < floor_db:
                value = floor_db
            if value > ceil_db:
                value = ceil_db
            norm_row.append((value - floor_db) / max(ceil_db - floor_db, 1e-9))
        out.append(norm_row)
    return out


def _colormap_jet(t: float) -> tuple[int, int, int]:
    t = max(0.0, min(1.0, t))
    if t < 0.25:
        s = t / 0.25
        return (0, int(255 * s), 255)
    if t < 0.5:
        s = (t - 0.25) / 0.25
        return (0, 255, int(255 * (1.0 - s)))
    if t < 0.75:
        s = (t - 0.5) / 0.25
        return (int(255 * s), 255, 0)
    s = (t - 0.75) / 0.25
    return (255, int(255 * (1.0 - s)), 0)


def _write_ppm(path: Path, width: int, height: int, rgb: bytes) -> None:
    header = f"P6\n{width} {height}\n255\n".encode("ascii")
    path.write_bytes(header + rgb)


def _grid_to_rgb(
    grid: list[list[float]],
    floor_db: float,
    ceil_db: float,
    flip_time: bool = True,
    target_height: int | None = WATERFALL_TARGET_HEIGHT,
) -> tuple[int, int, bytes]:
    norm = _normalize_grid(grid, floor_db, ceil_db)
    if flip_time:
        norm = list(reversed(norm))

    if target_height and len(norm) > 0 and len(norm) != target_height:
        norm = _resample_rows(norm, target_height)

    height = len(norm)
    width = len(norm[0]) if height else 0
    pixels = bytearray(width * height * 3)
    for y, row in enumerate(norm):
        for x, value in enumerate(row):
            r, g, b = _colormap_jet(value)
            idx = (y * width + x) * 3
            pixels[idx : idx + 3] = bytes((r, g, b))
    return width, height, bytes(pixels)


def _resample_rows(grid: list[list[float]], target_rows: int) -> list[list[float]]:
    if not grid or target_rows <= 0:
        return grid
    width = len(grid[0])
    if len(grid) == target_rows:
        return grid
    out: list[list[float]] = []
    for y in range(target_rows):
        src = y * (len(grid) - 1) / max(target_rows - 1, 1)
        lo = int(math.floor(src))
        hi = min(len(grid) - 1, lo + 1)
        frac = src - lo
        out.append(
            [
                grid[lo][x] * (1.0 - frac) + grid[hi][x] * frac
                for x in range(width)
            ]
        )
    return out


def _waterfall_view(
    signal_len: int,
    sample_rate: int,
    meta: dict | None,
) -> tuple[int, int, int, int]:
    """Return (seg_start, seg_end, nfft, hop) tuned for visible modulation."""
    meta = meta or {}
    mod_start = int(meta.get("modulation_start", 0))
    mod_len = int(meta.get("modulated_samples", signal_len))
    guard = int(meta.get("lead_silence_samples", sample_rate))

    body_sec = mod_len / sample_rate

    if body_sec < 0.25:
        margin = max(int(0.08 * sample_rate), mod_len * 12)
        seg_start = max(0, mod_start - margin)
        seg_end = min(signal_len, mod_start + mod_len + margin)
        seg_len = seg_end - seg_start
        nfft = 2048 if seg_len >= 2048 else _next_pow2(max(256, seg_len))
        hop = max(4, min(32, mod_len // 12 or 4))
    elif body_sec < 1.0:
        margin = max(int(0.15 * sample_rate), int(mod_len * 0.5))
        seg_start = max(0, mod_start - margin)
        seg_end = min(signal_len, mod_start + mod_len + margin)
        seg_len = seg_end - seg_start
        nfft = 2048 if seg_len >= 2048 else _next_pow2(max(512, seg_len))
        hop = max(8, min(64, mod_len // 16 or 8))
    else:
        seg_start = 0
        seg_end = signal_len
        if guard and mod_start:
            seg_end = min(signal_len, mod_start + mod_len + guard)
        nfft = 2048
        hop = 128

    if seg_end <= seg_start:
        seg_start, seg_end = 0, signal_len

    return seg_start, seg_end, nfft, hop


def _body_slice(signal: IqSamples, meta: dict | None) -> list[complex]:
    meta = meta or {}
    mod_start = int(meta.get("modulation_start", 0))
    mod_len = int(meta.get("modulated_samples", len(signal)))
    return signal.data[mod_start : mod_start + mod_len]


def _time_series_magnitude(samples: list[complex], max_points: int = 1200) -> list[float]:
    mags = [abs(s) for s in samples]
    if len(mags) <= max_points:
        return mags
    step = len(mags) / max_points
    return [mags[int(i * step)] for i in range(max_points)]


def _line_plot_rgb(
    values: list[float],
    width: int,
    height: int,
    rgb: tuple[int, int, int] = (80, 200, 255),
) -> bytes:
    if not values:
        values = [0.0]
    peak = max(values) or 1.0
    pixels = bytearray(width * height * 3)
    for x in range(width):
        idx = int(x * (len(values) - 1) / max(width - 1, 1))
        y = int((1.0 - values[idx] / peak) * (height - 1))
        y = max(0, min(height - 1, y))
        for yy in range(max(0, y - 1), min(height, y + 2)):
            off = (yy * width + x) * 3
            pixels[off : off + 3] = bytes(rgb)
    return bytes(pixels)


def _ppm_to_png(ppm_path: Path, png_path: Path) -> None:
    png_path.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["convert", str(ppm_path), str(png_path)],
        check=True,
        capture_output=True,
    )
    ppm_path.unlink(missing_ok=True)


def _render_stft_png(
    samples: list[complex],
    output_png: Path,
    *,
    sample_rate: int,
    nfft: int,
    hop: int,
    floor_db: float,
    ceil_db: float,
) -> None:
    frames, _times, freqs = stft_power_db(
        samples,
        sample_rate=sample_rate,
        nfft=nfft,
        hop=hop,
    )
    cropped, _freq_axis = _crop_waterfall(frames, freqs)
    width, height, rgb = _grid_to_rgb(cropped, floor_db, ceil_db)
    ppm = output_png.with_suffix(".ppm")
    _write_ppm(ppm, width, height, rgb)
    _ppm_to_png(ppm, output_png)


def render_waterfall(
    signal: IqSamples,
    output_png: Path,
    *,
    sample_rate: int = DEFAULT_SAMPLE_RATE,
    floor_db: float = -60.0,
    ceil_db: float = 0.0,
    meta: dict | None = None,
) -> None:
    """Waterfall zoomed to the modulated body with guard context."""
    seg_start, seg_end, nfft, hop = _waterfall_view(len(signal), sample_rate, meta)
    segment = signal.data[seg_start:seg_end]
    _render_stft_png(
        segment,
        output_png,
        sample_rate=sample_rate,
        nfft=nfft,
        hop=hop,
        floor_db=floor_db,
        ceil_db=ceil_db,
    )


def render_waterfall_context(
    signal: IqSamples,
    output_png: Path,
    *,
    sample_rate: int = DEFAULT_SAMPLE_RATE,
    floor_db: float = -60.0,
    ceil_db: float = 0.0,
) -> None:
    """Full capture overview showing guard silence and modulated body."""
    _render_stft_png(
        signal.data,
        output_png,
        sample_rate=sample_rate,
        nfft=2048,
        hop=256,
        floor_db=floor_db,
        ceil_db=ceil_db,
    )


def render_time_plot(
    signal: IqSamples,
    output_png: Path,
    *,
    sample_rate: int = DEFAULT_SAMPLE_RATE,
    width: int = 960,
    height: int = 240,
    meta: dict | None = None,
) -> None:
    seg_start, seg_end, _, _ = _waterfall_view(len(signal), sample_rate, meta)
    mags = _time_series_magnitude(signal.data[seg_start:seg_end])
    rgb = _line_plot_rgb(mags, width, height)
    ppm = output_png.with_suffix(".ppm")
    _write_ppm(ppm, width, height, rgb)
    _ppm_to_png(ppm, output_png)


def render_spectrum(
    signal: IqSamples,
    output_png: Path,
    *,
    sample_rate: int = DEFAULT_SAMPLE_RATE,
    floor_db: float = -60.0,
    ceil_db: float = 0.0,
    width: int = 960,
    height: int = 240,
    meta: dict | None = None,
) -> None:
    body = _body_slice(signal, meta)
    nfft = _next_pow2(max(2048, len(body)))
    window = _hann(len(body))
    framed = [body[i] * window[i] for i in range(len(body))]
    framed += [0j] * (nfft - len(framed))
    spectrum = _fftshift(_fft(framed))
    freqs = [((i - nfft // 2) * sample_rate / nfft) for i in range(nfft)]
    power = _power_db(spectrum)
    half = WATERFALL_WIDTH_HZ / 2.0
    indices = [i for i, f in enumerate(freqs) if -half <= f <= half]
    if not indices:
        indices = list(range(nfft))
    values = [power[i] for i in indices]
    norm = _normalize_grid([values], floor_db, ceil_db)[0]
    rgb = _line_plot_rgb(norm, width, height, rgb=(120, 255, 120))
    ppm = output_png.with_suffix(".ppm")
    _write_ppm(ppm, width, height, rgb)
    _ppm_to_png(ppm, output_png)
