package reporter

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"

	"github.com/joeldevz/skynex/internal/eval/runner"
)

// SaveResult marshals a SuiteResult to JSON and writes it to a file.
func SaveResult(result *runner.SuiteResult, path string) error {
	if result == nil {
		return fmt.Errorf("result is nil")
	}

	// Ensure directory exists
	dir := filepath.Dir(path)
	if dir != "." && dir != "" {
		if err := os.MkdirAll(dir, 0755); err != nil {
			return fmt.Errorf("create directory %s: %w", dir, err)
		}
	}

	// Marshal to JSON
	data, err := json.MarshalIndent(result, "", "  ")
	if err != nil {
		return fmt.Errorf("marshal JSON: %w", err)
	}

	// Write to file
	if err := os.WriteFile(path, data, 0644); err != nil {
		return fmt.Errorf("write file %s: %w", path, err)
	}

	return nil
}

// LoadResult reads a JSON file and unmarshals it into a SuiteResult.
func LoadResult(path string) (*runner.SuiteResult, error) {
	// Read file
	data, err := os.ReadFile(path)
	if err != nil {
		return nil, fmt.Errorf("read file %s: %w", path, err)
	}

	// Unmarshal JSON
	var result runner.SuiteResult
	if err := json.Unmarshal(data, &result); err != nil {
		return nil, fmt.Errorf("unmarshal JSON: %w", err)
	}

	return &result, nil
}
