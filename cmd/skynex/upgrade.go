package main

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
	"path/filepath"
	"runtime"
	"strings"
)

// GitHubRelease represents the minimal structure we need from the GitHub API
type GitHubRelease struct {
	TagName string `json:"tag_name"`
}

// selfUpgrade downloads and installs the latest skynex binary if a newer version is available.
// Returns nil if already up-to-date or if the current version is "dev" (running from source).
// Non-fatal errors log warnings and allow the package update to continue.
func selfUpgrade() error {
	// Dev builds skip upgrade
	if version == "dev" {
		fmt.Println("    Running dev build, skipping binary upgrade.")
		return nil
	}

	// Fetch latest release from GitHub
	latestTag, err := getLatestGitHubTag()
	if err != nil {
		return fmt.Errorf("failed to fetch latest GitHub release: %w", err)
	}

	// Strip 'v' prefix from tag (e.g., "v1.5.0" -> "1.5.0")
	latestVersion := strings.TrimPrefix(latestTag, "v")

	// Compare versions
	if version == latestVersion {
		fmt.Printf("    Already up to date (v%s).\n", version)
		return nil
	}

	// Detect platform
	osType := runtime.GOOS
	arch := runtime.GOARCH

	// Download the release archive
	tmpDir, err := os.MkdirTemp("", "skynex-upgrade-*")
	if err != nil {
		return fmt.Errorf("failed to create temp directory: %w", err)
	}
	defer os.RemoveAll(tmpDir)

	// Determine archive name and URL
	var archiveName, downloadURL string
	if osType == "windows" {
		archiveName = fmt.Sprintf("skynex_%s_%s_%s.zip", latestVersion, osType, arch)
	} else {
		archiveName = fmt.Sprintf("skynex_%s_%s_%s.tar.gz", latestVersion, osType, arch)
	}
	downloadURL = fmt.Sprintf("https://github.com/joeldevz/skynex/releases/download/v%s/%s", latestVersion, archiveName)

	// Download archive
	archivePath := filepath.Join(tmpDir, archiveName)
	if err := downloadFile(downloadURL, archivePath); err != nil {
		return fmt.Errorf("failed to download archive: %w", err)
	}

	// Verify checksum (optional but preferred)
	checksumURL := fmt.Sprintf("https://github.com/joeldevz/skynex/releases/download/v%s/checksums.txt", latestVersion)
	if err := verifyChecksum(archivePath, archiveName, checksumURL); err != nil {
		// Non-fatal: warn but continue
		fmt.Fprintf(os.Stderr, "    Warning: checksum verification failed: %v\n", err)
	}

	// Extract binary from archive
	binaryPath := filepath.Join(tmpDir, "skynex")
	if osType == "windows" {
		binaryPath = filepath.Join(tmpDir, "skynex.exe")
	}

	if err := extractBinary(archivePath, binaryPath, osType); err != nil {
		return fmt.Errorf("failed to extract binary: %w", err)
	}

	// Get current binary path
	currentBinary, err := os.Executable()
	if err != nil {
		return fmt.Errorf("failed to determine current binary path: %w", err)
	}

	// Resolve symlinks
	currentBinary, err = filepath.EvalSymlinks(currentBinary)
	if err != nil {
		return fmt.Errorf("failed to resolve symlinks: %w", err)
	}

	// Replace binary atomically
	if err := replaceBinary(currentBinary, binaryPath); err != nil {
		return fmt.Errorf("failed to replace binary: %w", err)
	}

	fmt.Printf("    Upgraded skynex from v%s to v%s — restart or re-run for changes to take effect.\n", version, latestVersion)
	return nil
}

// getLatestGitHubTag fetches the latest release tag from GitHub API
func getLatestGitHubTag() (string, error) {
	url := "https://api.github.com/repos/joeldevz/skynex/releases/latest"
	resp, err := http.Get(url)
	if err != nil {
		return "", err
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return "", fmt.Errorf("GitHub API returned HTTP %d", resp.StatusCode)
	}

	var release GitHubRelease
	if err := json.NewDecoder(resp.Body).Decode(&release); err != nil {
		return "", err
	}

	if release.TagName == "" {
		return "", fmt.Errorf("no tag_name found in response")
	}

	return release.TagName, nil
}

// downloadFile downloads a file from URL to destination
func downloadFile(url, dest string) error {
	resp, err := http.Get(url)
	if err != nil {
		return err
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return fmt.Errorf("HTTP %d", resp.StatusCode)
	}

	f, err := os.Create(dest)
	if err != nil {
		return err
	}
	defer f.Close()

	_, err = io.Copy(f, resp.Body)
	return err
}

// verifyChecksum downloads checksums.txt and verifies the archive
func verifyChecksum(archivePath, archiveName, checksumURL string) error {
	// Download checksums.txt
	checksumResp, err := http.Get(checksumURL)
	if err != nil {
		return fmt.Errorf("failed to download checksums.txt: %w", err)
	}
	defer checksumResp.Body.Close()

	if checksumResp.StatusCode != http.StatusOK {
		return fmt.Errorf("checksums.txt not found (HTTP %d)", checksumResp.StatusCode)
	}

	checksumData, err := io.ReadAll(checksumResp.Body)
	if err != nil {
		return err
	}

	// Find the checksum line for this archive
	var expectedChecksum string
	for _, line := range strings.Split(string(checksumData), "\n") {
		if strings.Contains(line, archiveName) {
			fields := strings.Fields(line)
			if len(fields) > 0 {
				expectedChecksum = fields[0]
				break
			}
		}
	}

	if expectedChecksum == "" {
		return fmt.Errorf("archive %s not found in checksums.txt", archiveName)
	}

	// Compute SHA256 of the archive
	f, err := os.Open(archivePath)
	if err != nil {
		return err
	}
	defer f.Close()

	hash := sha256.New()
	if _, err := io.Copy(hash, f); err != nil {
		return err
	}

	actualChecksum := fmt.Sprintf("%x", hash.Sum(nil))

	if actualChecksum != expectedChecksum {
		return fmt.Errorf("checksum mismatch: expected %s, got %s", expectedChecksum, actualChecksum)
	}

	return nil
}

// extractBinary extracts the skynex binary from the archive (tar.gz or zip)
func extractBinary(archivePath, outputPath string, osType string) error {
	if osType == "windows" {
		return extractBinaryFromZip(archivePath, outputPath)
	}
	return extractBinaryFromTarGz(archivePath, outputPath)
}

// extractBinaryFromTarGz extracts the skynex binary from a tar.gz archive
func extractBinaryFromTarGz(archivePath, outputPath string) error {
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
		header, err := tr.Next()
		if err == io.EOF {
			break
		}
		if err != nil {
			return err
		}

		// Look for the skynex binary
		if header.Name == "skynex" || strings.HasSuffix(header.Name, "/skynex") {
			out, err := os.Create(outputPath)
			if err != nil {
				return err
			}
			defer out.Close()

			if _, err := io.Copy(out, tr); err != nil {
				return err
			}

			// Make executable
			if err := os.Chmod(outputPath, 0755); err != nil {
				return err
			}

			return nil
		}
	}

	return fmt.Errorf("skynex binary not found in archive")
}

// extractBinaryFromZip extracts the skynex.exe binary from a zip archive
func extractBinaryFromZip(archivePath, outputPath string) error {
	r, err := zip.OpenReader(archivePath)
	if err != nil {
		return err
	}
	defer r.Close()

	for _, zf := range r.File {
		// Look for skynex.exe
		if zf.Name == "skynex.exe" || strings.HasSuffix(zf.Name, "/skynex.exe") {
			rc, err := zf.Open()
			if err != nil {
				return err
			}
			defer rc.Close()

			out, err := os.Create(outputPath)
			if err != nil {
				return err
			}
			defer out.Close()

			if _, err := io.Copy(out, rc); err != nil {
				return err
			}

			return nil
		}
	}

	return fmt.Errorf("skynex.exe not found in archive")
}

// replaceBinary replaces the current binary with a new one atomically
func replaceBinary(currentPath, newPath string) error {
	// Create backup path
	backupPath := currentPath + ".backup"

	// Read new binary
	newBinary, err := os.ReadFile(newPath)
	if err != nil {
		return err
	}

	// Try atomic replacement on Unix-like systems
	// On Windows, this may require special handling, but Rename generally works
	tempPath := currentPath + ".new"

	// Write to temp file
	if err := os.WriteFile(tempPath, newBinary, 0755); err != nil {
		return err
	}

	// Backup current binary if it exists
	if err := os.Rename(currentPath, backupPath); err != nil && !os.IsNotExist(err) {
		os.Remove(tempPath) // cleanup temp
		return err
	}

	// Move new binary into place
	if err := os.Rename(tempPath, currentPath); err != nil {
		// Try to restore backup if move failed
		os.Rename(backupPath, currentPath)
		return err
	}

	return nil
}
