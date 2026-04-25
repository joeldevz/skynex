.PHONY: build build-dev embed build-embedded test lint clean release-dry help

VERSION ?= $(shell git describe --tags --always --dirty 2>/dev/null || echo "dev")
BINARY  := .build/skilar
LDFLAGS := -s -w -X main.version=$(VERSION) -X main.commit=$(shell git rev-parse --short HEAD 2>/dev/null || echo unknown)

embed: ## Sync assets into internal/assets/data/ for go:embed
	go run ./cmd/tools/sync-assets/

build: ## Build production binary
	@mkdir -p .build
	CGO_ENABLED=0 go build -ldflags="$(LDFLAGS)" -o $(BINARY) ./cmd/skilar/

build-embedded: embed build ## Build self-contained binary with embedded assets

build-dev: ## Build dev binary (no trimpath)
	@mkdir -p .build
	go build -ldflags="-X main.version=$(VERSION)-dev" -o $(BINARY) ./cmd/skilar/

test: ## Run tests
	go test ./...

lint: ## Run linters
	go vet ./...
	@if command -v golangci-lint >/dev/null 2>&1; then golangci-lint run; fi

clean: ## Remove build artifacts
	rm -rf .build/

release-dry: ## Test goreleaser without releasing
	goreleaser release --snapshot --clean

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'
