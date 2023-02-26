FROM python

RUN apt-get update \
    && apt-get install -y gcc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY telegram-bot/ .
ENV TELEGRAM_BOT="yout bot token"
RUN pip install --no-cache-dir -r requirements.txt



CMD [ "python", "open_world.py" ]
