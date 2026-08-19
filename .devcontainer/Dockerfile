# Base image: Microsoft's Python dev container (Debian bookworm) — it ships git,
# a non-root `vscode` user with passwordless sudo, and the usual build tooling.
FROM mcr.microsoft.com/devcontainers/python:1-3.12-bookworm

# uv is copied straight from the official distroless image: no `curl | sh`, no
# pip bootstrap, and the version is pinned by tag so rebuilds are reproducible.
# Bump this tag to upgrade uv.
COPY --from=ghcr.io/astral-sh/uv:0.8.17 /uv /uvx /usr/local/bin/

# Install the OS packages Chromium needs (fonts, X/GTK libs, codecs) at *build*
# time, as root — `playwright install-deps` is an apt-get wrapper, so running it
# through uvx keeps Playwright itself out of the project environment. The browser
# binaries are downloaded per-user in post-create.sh.
RUN uvx --from playwright playwright install-deps chromium \
    && rm -rf /var/lib/apt/lists/*

# Bind-mounted workspaces don't support hardlinks from the uv cache, and
# bytecode compilation makes the first test run noticeably faster.
ENV UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1

# Pre-create the cache directories with the right ownership: a named volume
# inherits the ownership of the image path it covers, so without this the
# mounts in devcontainer.json would land root-owned and uv could not write.
RUN mkdir -p /home/vscode/.cache/uv /home/vscode/.cache/ms-playwright \
    && chown -R vscode:vscode /home/vscode/.cache
