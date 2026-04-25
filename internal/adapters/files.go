package adapters

import (
	"io"
	"io/fs"
	"os"
	"path/filepath"
	"strings"
)

// copyDir recursively copies src → dst, skipping nothing.
func copyDir(src, dst string) error {
	return copyDirExcluding(src, dst, nil)
}

// copyDirExcluding copies src → dst, skipping entries in exclude list.
func copyDirExcluding(src, dst string, exclude []string) error {
	excludeSet := make(map[string]bool)
	for _, e := range exclude {
		excludeSet[e] = true
	}

	return filepath.WalkDir(src, func(path string, d fs.DirEntry, err error) error {
		if err != nil {
			return err
		}

		// Check exclusions
		name := d.Name()
		if excludeSet[name] {
			if d.IsDir() {
				return filepath.SkipDir
			}
			return nil
		}

		rel, err := filepath.Rel(src, path)
		if err != nil {
			return err
		}

		// Skip hidden system dirs except .github
		if strings.HasPrefix(name, ".") && name != ".github" && d.IsDir() {
			return filepath.SkipDir
		}

		dstPath := filepath.Join(dst, rel)

		if d.IsDir() {
			return os.MkdirAll(dstPath, 0o755)
		}

		return copyFile(path, dstPath)
	})
}

// copyFile copies a single file from src to dst.
// If dst already exists with restrictive permissions, chmod it first.
func copyFile(src, dst string) error {
	if err := os.MkdirAll(filepath.Dir(dst), 0o755); err != nil {
		return err
	}

	// If destination exists with restrictive perms, make it writable first
	if _, err := os.Stat(dst); err == nil {
		_ = os.Chmod(dst, 0o644)
	}

	in, err := os.Open(src)
	if err != nil {
		return err
	}
	defer in.Close()

	out, err := os.OpenFile(dst, os.O_CREATE|os.O_WRONLY|os.O_TRUNC, 0o644)
	if err != nil {
		return err
	}
	defer out.Close()

	_, err = io.Copy(out, in)
	return err
}

// writeFile writes content to path, creating parent dirs.
func writeFile(path, content string) error {
	if err := os.MkdirAll(filepath.Dir(path), 0o755); err != nil {
		return err
	}
	return os.WriteFile(path, []byte(content), 0o644)
}
