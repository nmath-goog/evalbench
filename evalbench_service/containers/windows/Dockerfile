# evalbench_service/containers/windows/Dockerfile
FROM python:3.11-windowsservercore-ltsc2022

# Set shell to powershell
SHELL ["powershell", "-Command", "$ErrorActionPreference = 'Stop'; $ProgressPreference = 'SilentlyContinue';"]

# Install Git (Full Git for Windows to get bash and unix tools)
RUN Write-Host "Downloading Git..."; \
    Invoke-WebRequest -Uri "https://github.com/git-for-windows/git/releases/download/v2.43.0.windows.1/Git-2.43.0-64-bit.exe" -OutFile "git-installer.exe"; \
    Write-Host "Installing Git..."; \
    Start-Process -FilePath ".\git-installer.exe" -ArgumentList '/SILENT', '/NORESTART', '/NOCANCEL', '/SP-' -Wait; \
    Remove-Item -Force "git-installer.exe"

# Install Node.js
RUN Write-Host "Downloading Node.js..."; \
    Invoke-WebRequest -Uri "https://nodejs.org/dist/v20.11.0/node-v20.11.0-win-x64.zip" -OutFile "node.zip"; \
    Write-Host "Extracting Node.js..."; \
    Expand-Archive -Path "node.zip" -DestinationPath "C:\"; \
    Rename-Item -Path "C:\node-v20.11.0-win-x64" -NewName "Nodejs"; \
    Remove-Item -Force "node.zip"

# Install Google Cloud CLI
RUN Write-Host "Downloading Google Cloud CLI..."; \
    Invoke-WebRequest -Uri "https://dl.google.com/dl/cloudsdk/channels/rapid/google-cloud-sdk-windows-x86_64-packaged.zip" -OutFile "gcloud.zip"; \
    Write-Host "Extracting Google Cloud CLI..."; \
    Expand-Archive -Path "gcloud.zip" -DestinationPath "C:\"; \
    Remove-Item -Force "gcloud.zip"

# Install uv
RUN Write-Host "Installing uv..."; \
    pip install uv

# Set up PATH and environment variables
# Git is installed to C:\Program Files\Git by default.
# Git's usr\bin contains bash, sh, and other unix utilities (tar, gzip, etc.) which are useful.
ENV PATH="C:\evalbench\.venv\Scripts;C:\Program Files\Git\bin;C:\Program Files\Git\usr\bin;C:\Nodejs;C:\google-cloud-sdk\bin;${PATH}"
ENV CLOUDSDK_PYTHON=python
ENV PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=python
ENV PYTHONPATH="C:\evalbench;C:\evalbench\evalbench\evalproto;."
ENV AGY_CLI_DISABLE_AUTO_UPDATE=true

# Install dataform cli
RUN Write-Host "Installing Dataform CLI..."; \
    npm install -g @dataform/cli

WORKDIR C:\evalbench

# Copy dependency files first for caching
COPY pyproject.toml uv.lock ./
COPY viewer/pyproject.toml viewer/

# Sync dependencies
RUN Write-Host "Syncing dependencies (phase 1)..."; \
    uv sync --frozen --all-packages

# Copy the rest of the code
COPY . .

# Sync again to install the local packages
RUN Write-Host "Syncing dependencies (phase 2)..."; \
    uv sync --frozen --all-packages

# Install waitress for Windows frontend support (combined mode)
RUN Write-Host "Installing waitress..."; \
    uv pip install waitress

# Compile protos
RUN Write-Host "Compiling protobufs..."; \
    python -m grpc_tools.protoc --proto_path=evalbench/evalproto --python_out=evalbench/evalproto --pyi_out=evalbench/evalproto --grpc_python_out=evalbench/evalproto --experimental_editions evalbench/evalproto/*.proto

# Create directories for sessions
RUN New-Item -ItemType Directory -Force -Path C:\tmp_session_files; \
    New-Item -ItemType Directory -Force -Path C:\tmp_sessions; \
    New-Item -ItemType Directory -Force -Path C:\evalbench\results

# Set up entrypoint
RUN Copy-Item -Path C:\evalbench\evalbench_service\containers\windows\entrypoint.ps1 -Destination C:\evalbench\entrypoint.ps1

CMD ["powershell", "-File", "C:\\evalbench\\entrypoint.ps1"]
EXPOSE 50051
