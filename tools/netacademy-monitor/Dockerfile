FROM python:3.12-slim
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN pip install --no-cache-dir uv==0.12.23 && uv sync --locked --python 3.12
ENV PLAYWRIGHT_BROWSERS_PATH=/opt/browsers
RUN uv run playwright install --with-deps chromium
COPY monitor/ ./monitor/
ENV STATE_PATH=/data/state.json
VOLUME ["/data"]
ENTRYPOINT ["/app/.venv/bin/python", "-m", "monitor"]
