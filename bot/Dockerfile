FROM python:3.10.5-alpine3.16
WORKDIR /usr/src/bot
RUN apk update && \
    apk add --no-cache gcc postgresql-dev libc-dev libffi-dev g++ \
    tiff-dev jpeg-dev openjpeg-dev zlib-dev freetype-dev lcms2-dev \
    libwebp-dev tcl-dev tk-dev harfbuzz-dev fribidi-dev libimagequant-dev \
    libxcb-dev libpng-dev
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt