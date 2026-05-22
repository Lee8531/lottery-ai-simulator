FROM mcr.microsoft.com/powershell:7.5-ubuntu-24.04

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONUTF8=1 \
    PYTHONPATH=/app/src \
    LOTTERY_POWERSHELL=pwsh \
    TZ=Asia/Shanghai

RUN apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends python3 python3-pip python3-venv ca-certificates tzdata \
    && ln -snf /usr/share/zoneinfo/$TZ /etc/localtime \
    && echo $TZ > /etc/timezone \
    && ln -sf /usr/bin/python3 /usr/local/bin/python \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN python -m pip install --break-system-packages --no-cache-dir -r requirements.txt

COPY src ./src
COPY scripts ./scripts
COPY README.md LICENSE ./

RUN mkdir -p data/normalized data/users reports/latest reports/users

EXPOSE 8765

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8765/health', timeout=3).read()" || exit 1

CMD ["python", "-m", "lottery_sim.cli", "dashboard", "--server", "fastapi", "--reports", "reports/latest", "--host", "0.0.0.0", "--port", "8765"]
