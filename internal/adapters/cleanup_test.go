package adapters

import (
	"os"
	"path/filepath"
	"testing"
)

func TestDeprecatedManifest(t *testing.T) {
	// Verify manifest structure is correct
	if len(DeprecatedManifest) != 2 {
		t.Fatalf("expected 2 targets in manifest, got %d", len(DeprecatedManifest))
	}

	if _, ok := DeprecatedManifest["opencode"]; !ok {
		t.Error("missing 'opencode' target in manifest")
	}
	if _, ok := DeprecatedManifest["claude"]; !ok {
		t.Error("missing 'claude' target in manifest")
	}

	if len(DeprecatedManifest["opencode"]) < 1 {
		t.Error("opencode target should have deprecated files")
	}
	if len(DeprecatedManifest["claude"]) < 1 {
		t.Error("claude target should have deprecated files")
	}
}

func TestRemoveDeprecatedFiles(t *testing.T) {
	tmpDir := t.TempDir()

	// Create test files
	file1 := filepath.Join(tmpDir, "file1.txt")
	file2 := filepath.Join(tmpDir, "file2.txt")
	os.WriteFile(file1, []byte("test"), 0o644)
	os.WriteFile(file2, []byte("test"), 0o644)

	files := []DeprecatedFile{
		{Path: file1, Target: "test"},
		{Path: file2, Target: "test"},
	}

	removed, err := RemoveDeprecatedFiles(files)
	if err != nil {
		t.Fatalf("RemoveDeprecatedFiles failed: %v", err)
	}

	if removed != 2 {
		t.Fatalf("expected 2 removed, got %d", removed)
	}

	// Verify files are gone
	if _, err := os.Stat(file1); err == nil {
		t.Error("file1 still exists after removal")
	}
	if _, err := os.Stat(file2); err == nil {
		t.Error("file2 still exists after removal")
	}
}

func TestRemoveDeprecatedFilesNonexistent(t *testing.T) {
	files := []DeprecatedFile{
		{Path: "/nonexistent/path/file.txt", Target: "test"},
	}

	removed, err := RemoveDeprecatedFiles(files)
	if err != nil {
		t.Fatalf("RemoveDeprecatedFiles should not error on nonexistent files: %v", err)
	}

	if removed != 0 {
		t.Fatalf("expected 0 removed for nonexistent file, got %d", removed)
	}
}
