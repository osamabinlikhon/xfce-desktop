FROM ubuntu:22.04

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive
ENV LANG=C.UTF-8
ENV LC_ALL=C.UTF-8
ENV PYTHONUNBUFFERED=1

# Set default shell
SHELL ["/bin/bash", "-c"]

# Install system dependencies
RUN apt-get update && apt-get install -y \
    # Python and Node.js
    python3.11 \
    python3-pip \
    python3.11-venv \
    nodejs \
    npm \
    # Core utilities
    curl \
    wget \
    git \
    vim \
    nano \
    htop \
    net-tools \
    sudo \
    dbus-x11 \
    # X11 and VNC dependencies
    xvfb \
    x11vnc \
    x11-utils \
    x11-xserver-utils \
    # Xfce4 desktop environment
    xfce4 \
    xfce4-goodies \
    # Terminal and utilities
    xfce4-terminal \
    thunar \
    mousepad \
    ristretto \
    # Web and networking
    websockify \
    nginx \
    # Clean up
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for HuggingFace Spaces
RUN useradd -m -u 1000 -s /bin/bash user && \
    echo "user:user" | chpasswd && \
    usermod -aG sudo user

# Set working directory
WORKDIR /workspace

# Copy application files
COPY . /workspace/

# Install Python dependencies
RUN pip3 install --upgrade pip && \
    pip3 install --ignore-installed blinker -r requirements.txt

# Set ownership
RUN chown -R user:user /workspace

# Make start script executable
RUN chmod +x /workspace/start.sh

# Switch to non-root user
USER user

# Expose ports
EXPOSE 7860 5900 6080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:7860/ || exit 1

# Start the application
CMD ["./start.sh"]
