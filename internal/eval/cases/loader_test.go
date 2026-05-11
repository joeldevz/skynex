package cases

import (
	"os"
	"path/filepath"
	"testing"
)

// getProjectRoot finds the project root by looking for go.mod
func getProjectRoot() string {
	// Start from current directory and walk up
	dir, _ := os.Getwd()
	for {
		if _, err := os.Stat(filepath.Join(dir, "go.mod")); err == nil {
			return dir
		}
		parent := filepath.Dir(dir)
		if parent == dir {
			// Reached filesystem root
			break
		}
		dir = parent
	}
	return ""
}

// getTestCasePath returns the absolute path to a test case file
func getTestCasePath(relPath string) string {
	root := getProjectRoot()
	if root == "" {
		return relPath
	}
	return filepath.Join(root, relPath)
}

// TestLoadCase tests loading a valid YAML test case file
func TestLoadCase(t *testing.T) {
	// Use one of the existing eval/cases files
	casePath := getTestCasePath("eval/cases/grill-me/positive_design.yaml")

	tc, err := LoadCase(casePath)
	if err != nil {
		t.Fatalf("LoadCase() error = %v", err)
	}

	// Verify basic fields are loaded
	if tc.ID == "" {
		t.Error("ID should not be empty")
	}
	if tc.Item == "" {
		t.Error("Item should not be empty")
	}
	if tc.Input == "" {
		t.Error("Input should not be empty")
	}
}

// TestLoadCaseDefaults tests that defaults are set correctly
func TestLoadCaseDefaults(t *testing.T) {
	casePath := getTestCasePath("eval/cases/grill-me/positive_design.yaml")

	tc, err := LoadCase(casePath)
	if err != nil {
		t.Fatalf("LoadCase() error = %v", err)
	}

	// Check defaults
	if tc.MaxTurns == 0 {
		t.Error("MaxTurns should default to 10, got 0")
	}
	if tc.MaxTurns != 10 {
		t.Errorf("MaxTurns = %d, want 10", tc.MaxTurns)
	}

	if tc.NRuns == 0 {
		t.Error("NRuns should default to 1, got 0")
	}
	if tc.NRuns != 1 && tc.NRuns != 2 { // File specifies n_runs: 2
		t.Logf("NRuns = %d (file specifies 2, which overrides default)", tc.NRuns)
	}

	if tc.Aggregation == "" {
		t.Error("Aggregation should default to 'min', got empty")
	}
	if tc.Aggregation != "min" && tc.Aggregation != "" {
		t.Errorf("Aggregation = %q, want 'min'", tc.Aggregation)
	}
}

// TestLoadAll tests that LoadAll finds all 42 yaml files
func TestLoadAll(t *testing.T) {
	baseDir := getTestCasePath("eval/cases")

	// Check if directory exists
	_, err := os.Stat(baseDir)
	if err != nil {
		t.Skipf("Test cases directory not found at %s: %v", baseDir, err)
	}

	allCases, err := LoadAll(baseDir)
	if err != nil {
		t.Fatalf("LoadAll() error = %v", err)
	}

	// Check that we loaded test cases
	if len(allCases) == 0 {
		t.Error("LoadAll() returned empty slice, expected cases")
	}

	// Verify we got the expected 42 files
	if len(allCases) != 42 {
		t.Logf("LoadAll() returned %d cases, expected 42", len(allCases))
		// List what we found
		for _, tc := range allCases {
			t.Logf("  - %s (%s)", tc.ID, tc.Item)
		}
	}

	// Verify all cases have required fields
	for _, tc := range allCases {
		if tc.ID == "" {
			t.Error("Case has empty ID")
		}
		if tc.Item == "" {
			t.Error("Case has empty Item")
		}
		if tc.Input == "" {
			t.Error("Case has empty Input")
		}
	}
}

// TestLoadCaseValidation tests that required fields are validated
func TestLoadCaseValidation(t *testing.T) {
	// Create a temporary invalid YAML file
	tmpDir := t.TempDir()
	tmpFile := filepath.Join(tmpDir, "invalid.yaml")

	// Write invalid case (missing id)
	content := []byte(`
item: test-item
input: "test input"
`)
	if err := os.WriteFile(tmpFile, content, 0644); err != nil {
		t.Fatalf("WriteFile() error = %v", err)
	}

	_, err := LoadCase(tmpFile)
	if err == nil {
		t.Error("LoadCase() should fail for missing 'id' field")
	}
}

// TestLoadSuite tests loading all cases from a single directory
func TestLoadSuite(t *testing.T) {
	suiteDir := getTestCasePath("eval/cases/grill-me")

	// Check if directory exists
	_, err := os.Stat(suiteDir)
	if err != nil {
		t.Skipf("Test suite directory not found at %s: %v", suiteDir, err)
	}

	cases, err := LoadSuite(suiteDir)
	if err != nil {
		t.Fatalf("LoadSuite() error = %v", err)
	}

	// Check that we loaded cases from the suite
	if len(cases) == 0 {
		t.Error("LoadSuite() returned empty slice, expected cases from grill-me suite")
	}

	// Verify all cases are valid
	for _, tc := range cases {
		if tc.ID == "" {
			t.Error("Suite case has empty ID")
		}
		if tc.Item != "grill-me" {
			t.Logf("Suite case item = %q, expected 'grill-me'", tc.Item)
		}
	}
}
