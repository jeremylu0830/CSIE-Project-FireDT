FROM python:3.10

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    cmake \
    g++ \
    libeigen3-dev \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libusb-1.0-0 \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .

RUN pip install --upgrade pip && pip install --no-cache-dir --use-deprecated=legacy-resolver -r requirements.txt
RUN pip install git+https://github.com/lucasb-eyer/pydensecrf.git

COPY . .

EXPOSE 5000

CMD ["python", "-m", "demo_web.app"]
