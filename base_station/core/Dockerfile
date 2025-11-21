FROM python:3.11-slim AS builder

RUN apt-get update && apt-get install -y \
    --no-install-recommends \
    build-essential \
    libgl1 \
    libglib2.0-0 \
    libjpeg-dev \
    libpng-dev \
    libtiff-dev \
    protobuf-compiler python3-opencv ffmpeg \
    && rm -rf /var/lib/apt/lists/*

RUN pip install grpcio-tools
RUN pip install opencv-python
WORKDIR /app

# Copy your Python project
COPY . .

# Copy protos from the parent directory
# COPY ./protos ./protos

# Generate stubs

RUN python3 -m grpc_tools.protoc \
    -I=./protos \
    --python_out=./ \
    --grpc_python_out=./ \
    ./protos/ServerBaseStation.proto

# Runtime image
FROM python:3.11-slim
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY --from=builder /app /app

# RUN python -m grpc_tools.protoc \
#     -I./protos \
#     --python_out=. \
#     --grpc_python_out=. \
#     protos/ServerBaseStation.proto

CMD ["python3", "main.py"]  
