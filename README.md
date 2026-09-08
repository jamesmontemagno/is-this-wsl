# Is this WSL?

A tiny, friendly environment report for the operating system and browser powering the page.

## Run locally

Requires Python 3:

```sh
python3 server.py
```

Then open [http://localhost:3000](http://localhost:3000). Set `PORT=3001` to use a different port.

The server detects WSL, WSL version, Linux distribution, kernel, architecture, and browser details without any runtime dependencies.

## How the checks work

All host checks live in [`server.py`](server.py). The browser calls `/api/environment`, and the server returns one JSON snapshot for the page to render.

### WSL and WSL version

`detect_wsl()` checks both WSL-provided environment variables and the kernel string. A `microsoft-standard` or `wsl2` kernel is treated as WSL 2; other WSL matches are treated as WSL 1.

```python
kernel = f"{platform.release()} {platform.version()}"
is_wsl = bool(
    os.environ.get("WSL_INTEROP")
    or os.environ.get("WSL_DISTRO_NAME")
    or re.search(r"microsoft|wsl", kernel, re.IGNORECASE)
)
version = 2 if is_wsl and re.search(
    r"microsoft-standard|wsl2", kernel, re.IGNORECASE
) else (1 if is_wsl else None)
```

### Distro

The distro name comes from `WSL_DISTRO_NAME` when available. Otherwise, `read_os_release()` reads `/etc/os-release` and uses `PRETTY_NAME`, then `NAME`, with `Linux` as the final fallback.

```python
distro = (
    wsl["distro"]
    or os_release.get("PRETTY_NAME")
    or os_release.get("NAME")
    or "Linux"
)
```

### OS, version, architecture, and kernel

These values use Python's standard `platform` module, with the Linux version ID read from `/etc/os-release`.

```python
"os": {
    "name": "Linux (WSL)" if wsl["isWsl"]
        else os_release.get("PRETTY_NAME", platform.system()),
    "platform": platform.system().lower(),
    "version": os_release.get("VERSION_ID", ""),
    "architecture": platform.machine(),
},
"kernel": platform.release(),
```

### Browser

The server identifies the browser from the request's `User-Agent` header. The patterns are checked in order so Edge and Opera are recognized before their Chromium user-agent tokens.

```python
patterns = (
    ("Edge", r"Edg(?:e|A|iOS)?/([\d.]+)"),
    ("Opera", r"OPR/([\d.]+)"),
    ("Chrome", r"(?:Chrome|CriOS)/([\d.]+)"),
    ("Firefox", r"(?:Firefox|FxiOS)/([\d.]+)"),
    ("Safari", r"Version/([\d.]+).*Safari"),
)
```

Language and timezone are the two browser-only details. They are read in [`script.js`](script.js) with `navigator.language` and `Intl.DateTimeFormat().resolvedOptions().timeZone`.
