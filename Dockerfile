FROM python:3.12-slim

LABEL maintainer="Yash Agrawall <yashagrawall333@gmail.com>"
LABEL description="Standalone Zero-Subscription Content, 1080x1350 Design, /GHOST Caption & Email Engine for SOLE Bits & Bytes (IGIT Sarang)"

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    TZ=Asia/Kolkata

# Install fonts (Montserrat, Caladea, Liberation Serif) and Pillow dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    fonts-montserrat \
    fonts-crosextra-caladea \
    fonts-liberation2 \
    fontconfig \
    tzdata \
    ca-certificates \
    curl \
    && fc-cache -f -v \
    && rm -rf /var/lib/apt/lists/*

# Normalize font directory symlinks so paths match host Linux & Debian container paths
RUN mkdir -p /usr/share/fonts/julietaula-montserrat-fonts \
             /usr/share/fonts/google-crosextra-caladea-fonts \
             /usr/share/fonts/liberation-serif-fonts && \
    find /usr/share/fonts -iname "Montserrat-*.otf" -o -iname "Montserrat-*.ttf" | while read -r f; do \
        ln -sf "$f" "/usr/share/fonts/julietaula-montserrat-fonts/$(basename "${f%.*}").otf"; \
    done && \
    find /usr/share/fonts -iname "Caladea-*.ttf" | while read -r f; do \
        ln -sf "$f" "/usr/share/fonts/google-crosextra-caladea-fonts/$(basename "$f")"; \
    done && \
    find /usr/share/fonts -iname "LiberationSerif-*.ttf" | while read -r f; do \
        ln -sf "$f" "/usr/share/fonts/liberation-serif-fonts/$(basename "$f")"; \
    done

RUN pip install --no-cache-dir Pillow

WORKDIR /home/yashagrawall/bits-bytes-automation

COPY . /home/yashagrawall/bits-bytes-automation

EXPOSE 8765

CMD ["python3", "scripts/standalone_engine.py", "--daemon", "--port", "8765"]
