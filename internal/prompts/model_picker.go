package prompts

import (
	"os/exec"
	"strings"
)

const maxVisible = 12

// LoadOpencodeModels executes "opencode models" and returns map[provider][]fullModelID.
// Falls back to defaultModels() if the binary is unavailable or returns nothing.
func LoadOpencodeModels() (map[string][]string, error) {
	out, err := exec.Command("opencode", "models").Output()
	if err != nil {
		return defaultModels(), nil
	}
	result := make(map[string][]string)
	for _, line := range strings.Split(string(out), "\n") {
		line = strings.TrimSpace(line)
		if line == "" {
			continue
		}
		parts := strings.SplitN(line, "/", 2)
		if len(parts) == 2 {
			result[parts[0]] = append(result[parts[0]], line)
		}
	}
	if len(result) == 0 {
		return defaultModels(), nil
	}
	return result, nil
}

func defaultModels() map[string][]string {
	return map[string][]string{
		"anthropic": {
			"anthropic/claude-opus-4-6",
			"anthropic/claude-sonnet-4-6",
			"anthropic/claude-haiku-4-5",
		},
		"openai": {"openai/gpt-4o", "openai/o3"},
		"google": {
			"google/gemini-2.5-pro",
		},
	}
}
