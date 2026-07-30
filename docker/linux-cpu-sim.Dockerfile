FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        ca-certificates \
        cmake \
        python3 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace

CMD ["bash", "scripts/validate_linux_cpu_sim.sh"]
