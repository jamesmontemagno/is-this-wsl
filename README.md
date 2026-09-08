# Is this WSL?

A tiny, friendly environment report for the operating system and browser powering the page.

## Run locally

Requires Python 3:

```sh
python3 server.py
```

Then open [http://localhost:3000](http://localhost:3000). Set `PORT=3001` to use a different port.

The server detects WSL, WSL version, Linux distribution, kernel, architecture, and browser details without any runtime dependencies.
