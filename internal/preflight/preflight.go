package preflight

import (
	"fmt"
	"os"
	"os/exec"
	"path/filepath"

	"github.com/joeldevz/skilar/internal/models"
	"github.com/joeldevz/skilar/internal/paths"
)

// Run executes all preflight validations.
func Run(req *models.InstallRequest, cat *models.Catalog) []*models.ValidationIssue {
	var issues []*models.ValidationIssue

	// Global: git must exist
	if _, err := exec.LookPath("git"); err != nil {
		issues = append(issues, &models.ValidationIssue{
			Level:   "error",
			Message: "git not found in PATH",
			FixHint: "Install git: https://git-scm.com/downloads",
		})
	}

	for _, pkgID := range req.Packages {
		pkg, ok := cat.Packages[pkgID]
		if !ok {
			issues = append(issues, &models.ValidationIssue{
				Level:     "error",
				PackageID: pkgID,
				Message:   fmt.Sprintf("unknown package: %s", pkgID),
			})
			continue
		}

		// Validate targets
		supported := make(map[string]bool)
		for _, t := range pkg.SupportedTargets {
			supported[t] = true
		}
		for _, target := range req.Targets {
			if !supported[target] {
				issues = append(issues, &models.ValidationIssue{
					Level:     "error",
					PackageID: pkgID,
					Target:    target,
					Message:   fmt.Sprintf("package %s does not support target %s", pkgID, target),
					FixHint:   fmt.Sprintf("Supported targets: %v", pkg.SupportedTargets),
				})
			}
		}

		// Neurox requirement
		if pkg.RequiresNeurox {
			if _, err := exec.LookPath("neurox"); err != nil {
				issues = append(issues, &models.ValidationIssue{
					Level:     "error",
					PackageID: pkgID,
					Message:   "neurox not found in PATH (required by this package)",
					FixHint:   "Install neurox first: skilar --package neurox",
				})
			}
		}

		// Target-specific checks
		for _, target := range req.Targets {
			switch {
			case pkgID == "skills" && target == "opencode":
				if _, err := exec.LookPath("bun"); err != nil {
					if _, err := exec.LookPath("npm"); err != nil {
						issues = append(issues, &models.ValidationIssue{
							Level:     "error",
							PackageID: pkgID,
							Target:    target,
							Message:   "neither bun nor npm found in PATH",
							FixHint:   "Install bun (https://bun.sh) or npm",
						})
					}
				}
			case pkgID == "skills" && target == "claude":
				claudeDir := paths.ClaudeDir()
				if err := ensureWritable(claudeDir); err != nil {
					issues = append(issues, &models.ValidationIssue{
						Level:     "error",
						PackageID: pkgID,
						Target:    target,
						Message:   fmt.Sprintf("cannot write to %s", claudeDir),
						FixHint:   "Check permissions on " + claudeDir,
					})
				}
			case pkgID == "neurox":
				if _, err := exec.LookPath("go"); err != nil {
					issues = append(issues, &models.ValidationIssue{
						Level:     "error",
						PackageID: pkgID,
						Target:    target,
						Message:   "go not found in PATH (required to build neurox)",
						FixHint:   "Install Go: https://go.dev/dl/",
					})
				}
			}
		}
	}

	return issues
}

// HasErrors returns true if any issue is an error.
func HasErrors(issues []*models.ValidationIssue) bool {
	for _, i := range issues {
		if i.Level == "error" {
			return true
		}
	}
	return false
}

// PrintIssues displays validation issues to stderr.
func PrintIssues(issues []*models.ValidationIssue) {
	fmt.Fprintln(os.Stderr, "\nPreflight validation:")
	for _, i := range issues {
		prefix := ""
		if i.PackageID != "" {
			prefix += "[" + i.PackageID + "]"
		}
		if i.Target != "" {
			prefix += "[" + i.Target + "]"
		}
		if prefix != "" {
			prefix += " "
		}
		fmt.Fprintf(os.Stderr, "  %s%s: %s\n", prefix, i.Level, i.Message)
		if i.FixHint != "" {
			fmt.Fprintf(os.Stderr, "    Fix: %s\n", i.FixHint)
		}
	}
}

func ensureWritable(dir string) error {
	if _, err := os.Stat(dir); os.IsNotExist(err) {
		return os.MkdirAll(dir, 0o755)
	}
	// Try to create a temp file to check writability
	tmp := filepath.Join(dir, ".skilar-preflight-check")
	f, err := os.Create(tmp)
	if err != nil {
		return err
	}
	f.Close()
	os.Remove(tmp)
	return nil
}
