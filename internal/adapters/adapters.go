package adapters

import (
	"archive/tar"
	"archive/zip"
	"compress/gzip"
	"crypto/sha256"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"os"
	"os/exec"
	"path/filepath"
	"runtime"
	"strings"
	"time"

	"github.com/joeldevz/skynex/internal/assets"
	"github.com/joeldevz/skynex/internal/models"
	"github.com/joeldevz/skynex/internal/paths"
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
	var checkoutDir string
	var commit string

	// Use embedded assets if available (self-contained binary) and version is "latest"
	if assets.Available() && version == "latest" {
		fmt.Println("    Using embedded assets (self-contained mode)...")
		// Extract to temp dir
		tmpDir, err := os.MkdirTemp("", "skynex-assets-*")
		if err != nil {
			return nil, fmt.Errorf("create temp dir: %w", err)
		}
		// Don't defer removal — adapters need the dir during install
		// It will be cleaned by OS on next boot

		// Extract claude-code assets
		if claudeCodeFS, err := assets.ClaudeCodeFS(); err == nil {
			destClaude := filepath.Join(tmpDir, "claude-code")
			if err := assets.ExtractTo(claudeCodeFS, destClaude); err != nil {
				return nil, fmt.Errorf("extract claude-code assets: %w", err)
			}
		}

		// Extract opencode assets
		if opencodeFS, err := assets.OpencodeFS(); err == nil {
			destOpencode := filepath.Join(tmpDir, "opencode")
			if err := assets.ExtractTo(opencodeFS, destOpencode); err != nil {
				return nil, fmt.Errorf("extract opencode assets: %w", err)
			}
		}

		checkoutDir = tmpDir
		commit = "embedded"
	} else {
		// Clone or use workspace (fallback)
		var err error
		checkoutDir, commit, err = checkoutPackage(pkg, version)
		if err != nil {
			return nil, err
		}
	}

	timestamp := time.Now().UTC().Format(time.RFC3339)
	targets := make(map[string]*models.TargetResult)

	for _, target := range req.Targets {
		var artifacts []string
		switch target {
		case "claude":
			fmt.Println("    Installing Claude Code assets...")
			if err := InstallClaude(checkoutDir); err != nil {
				return nil, fmt.Errorf("install claude: %w", err)
			}
			artifacts = []string{
				paths.ClaudeDir(),
				filepath.Join(paths.ClaudeDir(), "agents"),
				filepath.Join(paths.ClaudeDir(), "skills"),
				filepath.Join(paths.ClaudeDir(), "CLAUDE.md"),
			}
		case "opencode":
			fmt.Println("    Installing OpenCode config...")
			if err := InstallOpencode(checkoutDir); err != nil {
				return nil, fmt.Errorf("install opencode: %w", err)
			}
			artifacts = []string{paths.OpencodeDir()}
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
	installDir := paths.NeuroxBinDir()
	installPath := filepath.Join(installDir, paths.NeuroxBinName())

	if err := os.MkdirAll(installDir, 0o755); err != nil {
		return nil, fmt.Errorf("create neurox dir: %w", err)
	}

	resolvedVersion, commit, err := downloadNeurox(installPath, version)
	if err != nil {
		return nil, err
	}

	// Verify
	fmt.Println("    Verifying neurox...")
	verifyCmd := exec.Command(installPath, "version")
	out, err := verifyCmd.Output()
	if err != nil {
		// Try "status" as fallback
		verifyCmd2 := exec.Command(installPath, "status")
		if err2 := verifyCmd2.Run(); err2 != nil {
			return nil, fmt.Errorf("neurox verification failed: %w", err)
		}
	} else {
		fmt.Printf("    neurox %s\n", strings.TrimSpace(string(out)))
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
		ResolvedVersion:  resolvedVersion,
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
	tmpDir, err := os.MkdirTemp("", "skynex-*")
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
	configPath := filepath.Join(paths.OpencodeDir(), "opencode.json")

	data, err := os.ReadFile(configPath)
	if err != nil {
		return // Silently skip if not installed
	}

	var config map[string]interface{}
	if err := json.Unmarshal(data, &config); err != nil {
		return
	}

	agents, ok := config["agent"].(map[string]interface{})
	if !ok {
		return
	}

	advisorAgent, ok := agents["advisor"].(map[string]interface{})
	if !ok {
		return
	}

	advisorAgent["model"] = model
	agents["advisor"] = advisorAgent
	config["agent"] = agents

	out, err := json.MarshalIndent(config, "", "  ")
	if err != nil {
		return
	}
	os.WriteFile(configPath, append(out, '\n'), 0o644)
}

// downloadNeurox fetches the neurox binary from GitHub Releases.
// Returns (resolvedVersion, commit, error).
func downloadNeurox(installPath, version string) (string, string, error) {
	const owner = "joeldevz"
	const repo = "neurox"

	// Resolve version
	resolvedVersion := version
	if version == "latest" {
		fmt.Println("    Fetching latest neurox release...")
		v, err := fetchLatestTag(owner, repo)
		if err != nil {
			return "", "", fmt.Errorf("fetch neurox version: %w", err)
		}
		resolvedVersion = v
	}
	fmt.Printf("    neurox version: %s\n", resolvedVersion)

	// Build archive name matching goreleaser output:
	// neurox_<version_without_v>_<os>_<arch>.tar.gz  (linux/darwin)
	// neurox_<version_without_v>_windows_<arch>.zip  (windows)
	versionNum := strings.TrimPrefix(resolvedVersion, "v")
	goos := runtime.GOOS
	goarch := runtime.GOARCH

	var archiveName string
	if goos == "windows" {
		archiveName = fmt.Sprintf("neurox_%s_%s_%s.zip", versionNum, goos, goarch)
	} else {
		archiveName = fmt.Sprintf("neurox_%s_%s_%s.tar.gz", versionNum, goos, goarch)
	}

	downloadURL := fmt.Sprintf("https://github.com/%s/%s/releases/download/%s/%s", owner, repo, resolvedVersion, archiveName)
	checksumsURL := fmt.Sprintf("https://github.com/%s/%s/releases/download/%s/checksums.txt", owner, repo, resolvedVersion)

	fmt.Printf("    Downloading %s...\n", archiveName)

	tmpDir, err := os.MkdirTemp("", "neurox-download-*")
	if err != nil {
		return "", "", err
	}
	defer os.RemoveAll(tmpDir)

	archivePath := filepath.Join(tmpDir, archiveName)
	if err := downloadFile(downloadURL, archivePath); err != nil {
		return "", "", fmt.Errorf("download neurox: %w", err)
	}

	// Verify file size
	info, err := os.Stat(archivePath)
	if err != nil || info.Size() < 1000 {
		return "", "", fmt.Errorf("downloaded file too small — archive may not exist for %s/%s", goos, goarch)
	}

	// Verify checksum (best-effort)
	if err := verifyChecksum(checksumsURL, archivePath, archiveName, tmpDir); err != nil {
		fmt.Printf("    Warning: checksum verification skipped: %v\n", err)
	} else {
		fmt.Println("    Checksum verified")
	}

	// Extract binary
	fmt.Println("    Extracting neurox...")
	binaryName := "neurox"
	if goos == "windows" {
		binaryName = "neurox.exe"
		if err := extractZip(archivePath, tmpDir, binaryName); err != nil {
			return "", "", fmt.Errorf("extract zip: %w", err)
		}
	} else {
		if err := extractTarGz(archivePath, tmpDir, binaryName); err != nil {
			return "", "", fmt.Errorf("extract tar.gz: %w", err)
		}
	}

	extractedBin := filepath.Join(tmpDir, binaryName)
	if _, err := os.Stat(extractedBin); err != nil {
		return "", "", fmt.Errorf("binary not found in archive after extraction")
	}

	// Install
	if err := copyFile(extractedBin, installPath); err != nil {
		return "", "", fmt.Errorf("install neurox binary: %w", err)
	}
	if err := os.Chmod(installPath, 0o755); err != nil {
		return "", "", fmt.Errorf("chmod neurox: %w", err)
	}

	fmt.Printf("    Installed neurox to %s\n", installPath)
	return resolvedVersion, resolvedVersion, nil
}

// fetchLatestTag returns the latest release tag from GitHub API.
func fetchLatestTag(owner, repo string) (string, error) {
	url := fmt.Sprintf("https://api.github.com/repos/%s/%s/releases/latest", owner, repo)
	req, err := http.NewRequest("GET", url, nil)
	if err != nil {
		return "", err
	}
	req.Header.Set("User-Agent", "skynex-installer")
	req.Header.Set("Accept", "application/vnd.github.v3+json")

	resp, err := http.DefaultClient.Do(req)
	if err != nil {
		return "", err
	}
	defer resp.Body.Close()

	if resp.StatusCode != 200 {
		return "", fmt.Errorf("GitHub API returned %d", resp.StatusCode)
	}

	var release struct {
		TagName string `json:"tag_name"`
	}
	if err := json.NewDecoder(resp.Body).Decode(&release); err != nil {
		return "", err
	}
	if release.TagName == "" {
		return "", fmt.Errorf("empty tag_name in response")
	}
	return release.TagName, nil
}

// downloadFile downloads url to destPath.
func downloadFile(url, destPath string) error {
	req, err := http.NewRequest("GET", url, nil)
	if err != nil {
		return err
	}
	req.Header.Set("User-Agent", "skynex-installer")

	resp, err := http.DefaultClient.Do(req)
	if err != nil {
		return err
	}
	defer resp.Body.Close()

	if resp.StatusCode != 200 {
		return fmt.Errorf("HTTP %d downloading %s", resp.StatusCode, url)
	}

	f, err := os.Create(destPath)
	if err != nil {
		return err
	}
	defer f.Close()

	_, err = io.Copy(f, resp.Body)
	return err
}

// verifyChecksum downloads checksums.txt and verifies archiveName matches.
func verifyChecksum(checksumsURL, archivePath, archiveName, tmpDir string) error {
	checksumsPath := filepath.Join(tmpDir, "checksums.txt")
	if err := downloadFile(checksumsURL, checksumsPath); err != nil {
		return fmt.Errorf("download checksums: %w", err)
	}

	data, err := os.ReadFile(checksumsPath)
	if err != nil {
		return err
	}

	var expectedHash string
	for _, line := range strings.Split(string(data), "\n") {
		fields := strings.Fields(line)
		if len(fields) == 2 && fields[1] == archiveName {
			expectedHash = strings.ToLower(fields[0])
			break
		}
	}
	if expectedHash == "" {
		return fmt.Errorf("archive not found in checksums.txt")
	}

	f, err := os.Open(archivePath)
	if err != nil {
		return err
	}
	defer f.Close()

	h := sha256.New()
	if _, err := io.Copy(h, f); err != nil {
		return err
	}
	actual := fmt.Sprintf("%x", h.Sum(nil))

	if actual != expectedHash {
		return fmt.Errorf("checksum mismatch: expected %s, got %s", expectedHash, actual)
	}
	return nil
}

// extractTarGz extracts targetFile from a .tar.gz archive into destDir.
func extractTarGz(archivePath, destDir, targetFile string) error {
	f, err := os.Open(archivePath)
	if err != nil {
		return err
	}
	defer f.Close()

	gz, err := gzip.NewReader(f)
	if err != nil {
		return err
	}
	defer gz.Close()

	tr := tar.NewReader(gz)
	for {
		hdr, err := tr.Next()
		if err == io.EOF {
			break
		}
		if err != nil {
			return err
		}

		// Match by exact name OR by prefix (e.g. neurox_darwin_arm64 matches "neurox")
		base := filepath.Base(hdr.Name)
		if hdr.Typeflag == tar.TypeReg && (base == targetFile || strings.HasPrefix(base, targetFile+"_") || strings.HasPrefix(base, targetFile+"-")) {
			destPath := filepath.Join(destDir, targetFile)
			out, err := os.Create(destPath)
			if err != nil {
				return err
			}
			if _, err := io.Copy(out, tr); err != nil {
				out.Close()
				return err
			}
			out.Close()
			return nil
		}
	}
	return fmt.Errorf("binary %q not found in archive", targetFile)
}

// extractZip extracts targetFile from a .zip archive into destDir.
func extractZip(archivePath, destDir, targetFile string) error {
	r, err := zip.OpenReader(archivePath)
	if err != nil {
		return err
	}
	defer r.Close()

	for _, f := range r.File {
		base := filepath.Base(f.Name)
		if base == targetFile || strings.HasPrefix(base, targetFile+"_") || strings.HasPrefix(base, targetFile+"-") {
			destPath := filepath.Join(destDir, targetFile)
			out, err := os.Create(destPath)
			if err != nil {
				return err
			}
			rc, err := f.Open()
			if err != nil {
				out.Close()
				return err
			}
			_, err = io.Copy(out, rc)
			rc.Close()
			out.Close()
			return err
		}
	}
	return fmt.Errorf("binary %q not found in zip archive", targetFile)
}
