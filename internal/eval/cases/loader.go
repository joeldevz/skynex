package cases

import (
	"fmt"
	"io/fs"
	"os"
	"path/filepath"

	"gopkg.in/yaml.v3"
)

// TestCase represents a single evaluation test case loaded from YAML
type TestCase struct {
	ID          string    `yaml:"id"`
	Item        string    `yaml:"item"`
	Type        string    `yaml:"type"`        // "positive" or "negative"
	Agent       string    `yaml:"agent"`       // which agent to send to
	Input       string    `yaml:"input"`       // initial prompt
	Turns       []Turn    `yaml:"turns"`       // multi-turn auto-responses
	MaxTurns    int       `yaml:"max_turns"`   // default 10
	Fixture     string    `yaml:"fixture"`     // relative path in eval/fixtures/
	SetupCmd    string    `yaml:"setup_cmd"`   // command to run in fixture before test
	Checks      []Check   `yaml:"checks"`      // deterministic judges
	LLMJudge    *LLMJudge `yaml:"llm_judge"`   // optional LLM judge config
	NRuns       int       `yaml:"n_runs"`      // number of reruns (default 1)
	Aggregation string    `yaml:"aggregation"` // "min", "median", "mean"
	Metrics     []string  `yaml:"metrics"`     // metrics to capture
}

// Turn represents a single turn in a multi-turn conversation
type Turn struct {
	Answer string `yaml:"answer"`
}

// Check represents a single deterministic check to perform on a test result
type Check struct {
	Name     string      `yaml:"name"`
	Type     string      `yaml:"type"` // regex_count, regex_count_max_per_msg, contains_any, contains_all, not_contains, not_contains_pattern, regex_match, tool_called, tool_called_min, file_written, tool_call_order, bash_output_contains
	Pattern  string      `yaml:"pattern"`
	Patterns []string    `yaml:"patterns"`
	Value    interface{} `yaml:"value"` // int or string depending on type
	Tool     string      `yaml:"tool"`  // for tool_called checks
}

// LLMJudge represents optional LLM-based judging configuration
type LLMJudge struct {
	Enabled       bool    `yaml:"enabled"`
	Model         string  `yaml:"model"`
	Rubric        string  `yaml:"rubric"`
	PassThreshold float64 `yaml:"pass_threshold"`
}

// LoadSuite loads all .yaml files from a directory
func LoadSuite(dir string) ([]TestCase, error) {
	var cases []TestCase

	entries, err := os.ReadDir(dir)
	if err != nil {
		return nil, fmt.Errorf("read directory %s: %w", dir, err)
	}

	for _, entry := range entries {
		if entry.IsDir() {
			continue
		}
		if filepath.Ext(entry.Name()) != ".yaml" && filepath.Ext(entry.Name()) != ".yml" {
			continue
		}

		path := filepath.Join(dir, entry.Name())
		tc, err := LoadCase(path)
		if err != nil {
			return nil, fmt.Errorf("load case %s: %w", path, err)
		}

		cases = append(cases, *tc)
	}

	return cases, nil
}

// LoadCase loads a single test case from a YAML file
func LoadCase(path string) (*TestCase, error) {
	data, err := os.ReadFile(path)
	if err != nil {
		return nil, fmt.Errorf("read file %s: %w", path, err)
	}

	var tc TestCase
	if err := yaml.Unmarshal(data, &tc); err != nil {
		return nil, fmt.Errorf("unmarshal YAML %s: %w", path, err)
	}

	// Validate required fields
	if tc.ID == "" {
		return nil, fmt.Errorf("validate %s: field 'id' is required and cannot be empty", path)
	}
	if tc.Item == "" {
		return nil, fmt.Errorf("validate %s: field 'item' is required and cannot be empty", path)
	}
	if tc.Input == "" {
		return nil, fmt.Errorf("validate %s: field 'input' is required and cannot be empty", path)
	}

	// Set defaults
	if tc.MaxTurns == 0 {
		tc.MaxTurns = 10
	}
	if tc.NRuns == 0 {
		tc.NRuns = 1
	}
	if tc.Aggregation == "" {
		tc.Aggregation = "min"
	}

	return &tc, nil
}

// LoadAll recursively loads all test cases from a base directory
func LoadAll(baseDir string) ([]TestCase, error) {
	var allCases []TestCase

	err := filepath.WalkDir(baseDir, func(path string, d fs.DirEntry, err error) error {
		if err != nil {
			return err
		}

		// Skip directories
		if d.IsDir() {
			return nil
		}

		// Check if file is a YAML file
		ext := filepath.Ext(path)
		if ext != ".yaml" && ext != ".yml" {
			return nil
		}

		tc, err := LoadCase(path)
		if err != nil {
			return fmt.Errorf("load case %s: %w", path, err)
		}

		allCases = append(allCases, *tc)
		return nil
	})

	if err != nil {
		return nil, fmt.Errorf("walk directory %s: %w", baseDir, err)
	}

	return allCases, nil
}
