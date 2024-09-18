FROM python:3.9-slim

# 安装系统依赖和 Chrome
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget gnupg tesseract-ocr libtesseract-dev tesseract-ocr-chi-sim \
    libjpeg-dev zlib1g-dev unzip curl libgconf-2-4 libxss1 \
    libappindicator1 libnss3 libgdk-pixbuf2.0-0 libgtk-3-0 libasound2 \
    fonts-wqy-zenhei locales libgl1-mesa-glx \
    && curl -sSL https://dl.google.com/linux/linux_signing_key.pub | gpg --dearmor -o /usr/share/keyrings/google-chrome.gpg \
    && echo "deb [arch=amd64 signed-by=/usr/share/keyrings/google-chrome.gpg] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update \
    && apt-get install -y --no-install-recommends google-chrome-stable \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# 设置中文本地化
RUN locale-gen zh_CN.UTF-8
ENV LANG zh_CN.UTF-8
ENV LANGUAGE zh_CN:zh
ENV LC_ALL zh_CN.UTF-8

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app

CMD ["python", "monitor_script.py"]