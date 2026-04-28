package config

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"time"

	"github.com/joeldevz/skynex/internal/models"
)

// LoadOrDefault loads config from path or returns a default.
func LoadOrDefault(path string) map[string]interface{} {
	data, err := os.ReadFile(path)
	if err != nil {
		return map[string]interface{}{
			"version":  1,
			"defaults": map[string]interface{}{},
			"packages": map[string]interface{}{},
		}
	}
	var cfg map[string]interface{}
	if err := json.Unmarshal(data, &cfg); err != nil {
		return map[string]interface{}{
			"version":  1,
			"defaults": map[string]interface{}{},
			"packages": map[string]interface{}{},
		}
	}
	return cfg
}

// SaveConfig writes the config file with the user's install request.
func SaveConfig(path string, req *models.InstallRequest, existing map[string]interface{}) {
	cfg := map[string]interface{}{
		"version": 1,
		"defaults": map[string]interface{}{
			"interactive": req.Interactive,
			"targets":     req.Targets,
		},
		"packages": map[string]interface{}{},
	}

	pkgs := cfg["packages"].(map[string]interface{})

	// Preserve existing package configs
	if ep, ok := existing["packages"].(map[string]interface{}); ok {
		for k, v := range ep {
			pkgs[k] = v
		}
	}

	// Update with current request
	for _, pkgID := range req.Packages {
		pkgs[pkgID] = map[string]interface{}{
			"version": req.Versions[pkgID],
			"targets": req.Targets,
		}
	}

	// Add advisor config if set
	if req.Advisor != nil && req.Advisor.Enabled {
		cfg["advisor"] = map[string]interface{}{
			"enabled": true,
			"model":   req.Advisor.Model,
			"maxUses": req.Advisor.MaxUses,
		}
	}

	atomicWrite(path, cfg)
}

// SaveLock writes the lock file with resolved install results.
func SaveLock(path string, results []*models.InstallResult, req *models.InstallRequest) {
	lock := map[string]interface{}{
		"version":     1,
		"generatedAt": time.Now().UTC().Format(time.RFC3339),
		"packages":    map[string]interface{}{},
	}

	pkgs := lock["packages"].(map[string]interface{})

	for _, r := range results {
		targets := map[string]interface{}{}
		for target, tr := range r.Targets {
			targets[target] = map[string]interface{}{
				"status":      tr.Status,
				"installedAt": tr.InstalledAt,
				"artifacts":   tr.Artifacts,
			}
		}

		pkgs[r.PackageID] = map[string]interface{}{
			"requestedVersion": r.RequestedVersion,
			"resolvedVersion":  r.ResolvedVersion,
			"resolvedRef":      r.ResolvedRef,
			"commit":           r.Commit,
			"targets":          targets,
		}
	}

	// Add advisor to lock if configured
	if req.Advisor != nil && req.Advisor.Enabled {
		lock["advisor"] = map[string]interface{}{
			"enabled":     true,
			"model":       req.Advisor.Model,
			"installedAt": time.Now().UTC().Format(time.RFC3339),
		}
	}

	atomicWrite(path, lock)
}

func atomicWrite(path string, data map[string]interface{}) {
	dir := filepath.Dir(path)
	if err := os.MkdirAll(dir, 0o755); err != nil {
		fmt.Fprintf(os.Stderr, "Error creating state dir %s: %v\n", dir, err)
		return
	}

	b, err := json.MarshalIndent(data, "", "  ")
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error marshaling JSON: %v\n", err)
		return
	}

	tmp := path + ".tmp"
	if err := os.WriteFile(tmp, append(b, '\n'), 0o644); err != nil {
		fmt.Fprintf(os.Stderr, "Error writing %s: %v\n", tmp, err)
		return
	}
	if err := os.Rename(tmp, path); err != nil {
		fmt.Fprintf(os.Stderr, "Error renaming %s -> %s: %v\n", tmp, path, err)
		os.Remove(tmp)
	}
}
