package adapters

import (
	"fmt"
	"os"
	"path/filepath"
	"strings"
)

// DeprecatedFile is a single deprecated file to potentially remove.
type DeprecatedFile struct {
	Path   string // absolute path
	Target string // "opencode" or "claude"
}

// DeprecatedManifest defines all deprecated skynex-managed files.
// Maps target → list of relative paths (relative to ~/.config/opencode or ~/.claude).
var DeprecatedManifest = map[string][]string{
	"opencode": {
		"commands/onboard.md",
		"tools/advisor.ts",
	},
	"claude": {
		"skills/onboard/SKILL.md",
		"agents/product-planner.md",
	},
}

// FindDeprecatedFiles scans target directories for deprecated files.
// Returns a grouped map: target → []DeprecatedFile (only existing files).
func FindDeprecatedFiles() map[string][]DeprecatedFile {
	result := make(map[string][]DeprecatedFile)

	for target, paths := range DeprecatedManifest {
		var existing []DeprecatedFile
		var baseDir string

		switch target {
		case "opencode":
			baseDir = opencodeDir()
		case "claude":
			baseDir = claudeDir()
		default:
			continue
		}

		for _, relPath := range paths {
			absPath := filepath.Join(baseDir, relPath)
			if _, err := os.Stat(absPath); err == nil {
				existing = append(existing, DeprecatedFile{
					Path:   absPath,
					Target: target,
				})
			}
		}

		if len(existing) > 0 {
			result[target] = existing
		}
	}

	return result
}

// RemoveDeprecatedFiles removes the given deprecated files.
// Returns count removed and any errors.
func RemoveDeprecatedFiles(files []DeprecatedFile) (int, error) {
	count := 0
	for _, f := range files {
		err := os.Remove(f.Path)
		if err != nil && !os.IsNotExist(err) {
			return count, fmt.Errorf("remove %s: %w", f.Path, err)
		}
		if err == nil {
			count++
		}
	}
	return count, nil
}

// PromptCleanupDeprecated asks the user interactively if they want to remove deprecated files.
// Returns true if user confirms, false otherwise.
func PromptCleanupDeprecated(grouped map[string][]DeprecatedFile) bool {
	if len(grouped) == 0 {
		return false
	}

	fmt.Println("\n  Deprecated skynex-managed files detected:")
	for target, files := range grouped {
		fmt.Printf("\n    [%s]\n", target)
		for _, f := range files {
			// Display relative path for clarity
			rel, _ := filepath.Rel(filepath.Dir(f.Path), f.Path)
			if rel == "" {
				rel = filepath.Base(f.Path)
			}
			fmt.Printf("      • %s\n", rel)
		}
	}

	fmt.Print("\n  Remove these deprecated files? [y/N] ")
	var input string
	fmt.Scanln(&input)
	return strings.ToLower(strings.TrimSpace(input)) == "y"
}
