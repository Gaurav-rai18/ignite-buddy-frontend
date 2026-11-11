.PHONY: help install install-server install-client install-desktop install-dev \
	build-ui build-admin install-electron desktop desktop-qt desktop-electron \
	test test-server test-client server agent doctor kb clean

help:
	@echo "Trainee Assistant – common targets"
	@echo ""
	@echo "  make install-server   # server + DRF + optional postgres/redis"
	@echo "  make install-client   # thin client libraries"
	@echo "  make install-desktop  # client + PySide6 overlay"
	@echo "  make install-dev      # pytest etc."
	@echo "  make build-ui         # desktop React UI → agent/static"
	@echo "  make build-admin      # admin React app → frontend-admin/dist"
	@echo "  make test             # all tests"
	@echo "  make server           # trainee-server"
	@echo "  make desktop          # auto shell (Electron if installed, else PySide6)"
	@echo "  make desktop-qt       # force PySide6"
	@echo "  make desktop-electron # force Electron (needs make install-electron)"
	@echo "  make install-electron # npm install in desktop-electron/"
	@echo "  make agent            # headless agent (browser UI)"
	@echo "  make doctor           # trainee-doctor"
	@echo "  make kb               # trainee-kb --help"
	@echo "  make clean"

install-server:
	pip install -e ".[server]"

install-client:
	pip install -e ".[client]"

install-desktop:
	pip install -e ".[client,desktop]"

install-dev:
	pip install -e ".[dev]"

build-ui:
	cd frontend && npm install && npm run build

build-admin:
	cd frontend-admin && npm install && npm run build

test:
	pytest

test-server:
	pytest tests/server tests/integration

test-client:
	pytest tests/client
	cd frontend && npm test

server:
	trainee-server

desktop:
	trainee-desktop

desktop-qt:
	ASSISTANT_SHELL=pyside6 trainee-desktop

desktop-electron:
	ASSISTANT_SHELL=electron trainee-desktop

install-electron:
	cd desktop-electron && npm install

agent:
	trainee-agent

doctor:
	trainee-doctor

kb:
	trainee-kb --help

# Remove build artifacts, bytecode caches, and node_modules across Windows and POSIX environments
clean:
	python -c "import shutil, pathlib; [shutil.rmtree(p, ignore_errors=True) for p in pathlib.Path('.').rglob('__pycache__')]; [shutil.rmtree(p, ignore_errors=True) for p in ['.pytest_cache', 'frontend/node_modules', 'frontend-admin/node_modules', 'frontend-admin/dist']]"
