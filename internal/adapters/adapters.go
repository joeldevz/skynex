package adapters

import (
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"time"

	"github.com/joeldevz/skills/internal/models"
)

// InstallAll installs all packages in the request.
func InstallAll(req *models.InstallRequest, cat *models.Catalog) ([]*models.InstallResult, error) {
	var results []*models.InstallResult

	for _, pkgID := range req.Packages {
		pkg := cat.Packages[pkgID]
		version := req.Versions[pkgID]

		fmt.Printf("\n  Installing %s (%s)...\n", pkgID, version)

		var result *models.InstallResult
		var err error

		switch pkg.Adapter {
		case "skills_repo":
			result, err = installSkillsRepo(pkg, req, version)
		case "neurox_binary":
			result, err = installNeurox(pkg, req, version)
		default:
			return nil, fmt.Errorf("unknown adapter: %s", pkg.Adapter)
		}

		if err != nil {
			return nil, fmt.Errorf("install %s: %w", pkgID, err)
		}
		results = append(results, result)
	}

	return results, nil
}

func installSkillsRepo(pkg *models.PackageDefinition, req *models.InstallRequest, version string) (*models.InstallResult, error) {
	// Clone or use workspace
	checkoutDir, commit, err := checkoutPackage(pkg, version)
	if err != nil {
		return nil, err
	}

	setupScript := filepath.Join(checkoutDir, "scripts", "setup.sh")
	if _, err := os.Stat(setupScript); err != nil {
		return nil, fmt.Errorf("setup.sh not found at %s", setupScript)
	}

	timestamp := time.Now().UTC().Format(time.RFC3339)
	targets := make(map[string]*models.TargetResult)

	for _, target := range req.Targets {
		var flag string
		var artifacts []string
		switch target {
		case "claude":
			flag = "--claude"
			home, _ := os.UserHomeDir()
			artifacts = []string{
				filepath.Join(home, ".claude"),
				filepath.Join(home, ".claude", "agents"),
				filepath.Join(home, ".claude", "skills"),
				filepath.Join(home, ".claude", "CLAUDE.md"),
			}
		case "opencode":
			flag = "--opencode"
			home, _ := os.UserHomeDir()
			artifacts = []string{filepath.Join(home, ".config", "opencode")}
		}

		fmt.Printf("    Running setup.sh %s...\n", flag)
		cmd := exec.Command("bash", setupScript, flag)
		cmd.Dir = checkoutDir
		cmd.Stdout = os.Stdout
		cmd.Stderr = os.Stderr
		if err := cmd.Run(); err != nil {
			return nil, fmt.Errorf("setup.sh %s failed: %w", flag, err)
		}

		targets[target] = &models.TargetResult{
			Status:      "installed",
			InstalledAt: timestamp,
			Artifacts:   artifacts,
		}
	}

	// Inject advisor model into opencode.json if configured
	if req.Advisor != nil && req.Advisor.Enabled {
		injectAdvisorModel(req.Advisor.Model)
	}

	return &models.InstallResult{
		PackageID:        pkg.ID,
		RequestedVersion: version,
		ResolvedVersion:  version,
		Commit:           commit,
		Targets:          targets,
	}, nil
}

func installNeurox(pkg *models.PackageDefinition, req *models.InstallRequest, version string) (*models.InstallResult, error) {
	checkoutDir, commit, err := checkoutPackage(pkg, version)
	if err != nil {
		return nil, err
	}

	home, _ := os.UserHomeDir()
	installDir := filepath.Join(home, ".local", "bin")
	installPath := filepath.Join(installDir, "neurox")
	os.MkdirAll(installDir, 0o755)

	// Build
	fmt.Println("    Building neurox...")
	cmd := exec.Command("go", "build", "-tags", "fts5", "-o", installPath, ".")
	cmd.Dir = checkoutDir
	cmd.Env = append(os.Environ(), "CGO_ENABLED=1")
	cmd.Stdout = os.Stdout
	cmd.Stderr = os.Stderr
	if err := cmd.Run(); err != nil {
		return nil, fmt.Errorf("go build failed: %w", err)
	}

	// Verify
	fmt.Println("    Verifying neurox...")
	verifyCmd := exec.Command(installPath, "status")
	if err := verifyCmd.Run(); err != nil {
		return nil, fmt.Errorf("neurox verification failed: %w", err)
	}

	timestamp := time.Now().UTC().Format(time.RFC3339)
	targets := make(map[string]*models.TargetResult)
	for _, target := range req.Targets {
		targets[target] = &models.TargetResult{
			Status:      "installed",
			InstalledAt: timestamp,
			Artifacts:   []string{installPath},
		}
	}

	return &models.InstallResult{
		PackageID:        pkg.ID,
		RequestedVersion: version,
		ResolvedVersion:  version,
		Commit:           commit,
		Targets:          targets,
	}, nil
}

func checkoutPackage(pkg *models.PackageDefinition, version string) (string, string, error) {
	if version == "workspace" {
		// Use current directory
		cwd, err := os.Getwd()
		if err != nil {
			return "", "", err
		}
		commit := getCommit(cwd)
		return cwd, commit, nil
	}

	// Clone to temp dir
	tmpDir, err := os.MkdirTemp("", "clasing-skill-*")
	if err != nil {
		return "", "", err
	}

	fmt.Printf("    Cloning %s...\n", pkg.RepoURL)
	cmd := exec.Command("git", "clone", "--depth", "1", pkg.RepoURL, tmpDir)
	cmd.Stdout = os.Stdout
	cmd.Stderr = os.Stderr
	if err := cmd.Run(); err != nil {
		return "", "", fmt.Errorf("git clone failed: %w", err)
	}

	// If version is a specific tag, checkout
	if version != "latest" {
		checkoutCmd := exec.Command("git", "checkout", version)
		checkoutCmd.Dir = tmpDir
		if err := checkoutCmd.Run(); err != nil {
			return "", "", fmt.Errorf("git checkout %s failed: %w", version, err)
		}
	}

	commit := getCommit(tmpDir)
	return tmpDir, commit, nil
}

func getCommit(dir string) string {
	cmd := exec.Command("git", "rev-parse", "HEAD")
	cmd.Dir = dir
	out, err := cmd.Output()
	if err != nil {
		return "unknown"
	}
	return trimNewline(string(out))
}

func trimNewline(s string) string {
	for len(s) > 0 && (s[len(s)-1] == '\n' || s[len(s)-1] == '\r') {
		s = s[:len(s)-1]
	}
	return s
}

// injectAdvisorModel updates the installed opencode.json with the chosen advisor model.
func injectAdvisorModel(model string) {
	home, _ := os.UserHomeDir()
	configPath := filepath.Join(home, ".config", "opencode", "opencode.json")

	data, err := os.ReadFile(configPath)
	if err != nil {
		return // Silently skip if not installed
	}

	// Simple string replacement for the advisor model
	// The default in the repo is "anthropic/claude-opus-4-6"
	old := `"model": "anthropic/claude-opus-4-6"`
	replacement := fmt.Sprintf(`"model": "%s"`, model)

	// Only replace within the advisor agent block — find it by context
	result := string(data)
	// Find the advisor agent section and replace model there
	if idx := findAdvisorModelIndex(result); idx >= 0 {
		before := result[:idx]
		after := result[idx+len(old):]
		result = before + replacement + after
	}

	os.WriteFile(configPath, []byte(result), 0o644)
}

func findAdvisorModelIndex(content string) int {
	// Look for "advisor" agent section, then find its model field
	advisorIdx := 0
	for {
		idx := indexOf(content[advisorIdx:], `"advisor"`)
		if idx < 0 {
			return -1
		}
		advisorIdx += idx

		// Check if this is the agent definition (has "description" nearby)
		section := content[advisorIdx:min(advisorIdx+500, len(content))]
		if indexOf(section, `"Strategic advisor"`) >= 0 || indexOf(section, `"description"`) >= 0 {
			modelIdx := indexOf(section, `"model": "anthropic/claude-opus-4-6"`)
			if modelIdx >= 0 {
				return advisorIdx + modelIdx
			}
		}
		advisorIdx += len(`"advisor"`)
	}
}

func indexOf(s, sub string) int {
	for i := 0; i <= len(s)-len(sub); i++ {
		if s[i:i+len(sub)] == sub {
			return i
		}
	}
	return -1
}

func min(a, b int) int {
	if a < b {
		return a
	}
	return b
}
