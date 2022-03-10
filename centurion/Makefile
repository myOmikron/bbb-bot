# Go compiler
GO = go

# Directory containing Go source files
FILE_DIR = cmd/centurion/centurion.go

# Directory containing compiled executables
OUT_DIR = bin/

# File suffix for Go source files
FILE_SUFFIX = go

.PHONY: build
build: clean
	CGO_ENABLED=0 ${GO} build -ldflags=-w -o ${OUT_DIR}/centurion ${FILE_DIR}

.PHONY: clean
clean:
	rm -rf ${OUT_DIR}

.PHONY: install
install:
	cp bin/centurion /usr/local/bin/
	mkdir -p /etc/centurion/
	cp example.config.json /etc/centurion/

.PHONY: uninstall
uninstall:
	rm /usr/local/bin/centurion
