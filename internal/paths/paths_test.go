package paths_test

import (
	"os"
	"runtime"
	"strings"
	"testing"

	"github.com/joeldevz/skilar/internal/paths"
)

func TestClaudeDir_Unix(t *testing.T) {
	if runtime.GOOS == "windows" {
		t.Skip("Unix-only test")
	}
	home, _ := os.UserHomeDir()
	got := paths.ClaudeDir()
	if !strings.HasSuffix(got, ".claude") {
		t.Errorf("ClaudeDir() = %q, want suffix .claude", got)
	}
	if !strings.HasPrefix(got, home) {
		t.Errorf("ClaudeDir() = %q, should be under home %q", got, home)
	}
}

func TestOpencodeDir_Unix(t *testing.T) {
	if runtime.GOOS == "windows" {
		t.Skip("Unix-only test")
	}
	got := paths.OpencodeDir()
	if !strings.Contains(got, "opencode") {
		t.Errorf("OpencodeDir() = %q, want to contain 'opencode'", got)
	}
}

func TestStateDir_Unix(t *testing.T) {
	if runtime.GOOS == "windows" {
		t.Skip("Unix-only test")
	}
	got := paths.StateDir()
	if !strings.Contains(got, "skilar") {
		t.Errorf("StateDir() = %q, want to contain 'skilar'", got)
	}
}

func TestNeuroxBinDir_Unix(t *testing.T) {
	if runtime.GOOS == "windows" {
		t.Skip("Unix-only test")
	}
	got := paths.NeuroxBinDir()
	if got == "" {
		t.Error("NeuroxBinDir() returned empty string")
	}
}

func TestNeuroxBinName(t *testing.T) {
	got := paths.NeuroxBinName()
	if runtime.GOOS == "windows" {
		if got != "neurox.exe" {
			t.Errorf("NeuroxBinName() = %q, want neurox.exe on Windows", got)
		}
	} else {
		if got != "neurox" {
			t.Errorf("NeuroxBinName() = %q, want neurox on non-Windows", got)
		}
	}
}

func TestNoDirEmpty(t *testing.T) {
	// All dirs must be non-empty
	fns := map[string]func() string{
		"ClaudeDir":    paths.ClaudeDir,
		"OpencodeDir":  paths.OpencodeDir,
		"StateDir":     paths.StateDir,
		"NeuroxBinDir": paths.NeuroxBinDir,
	}
	for name, fn := range fns {
		if got := fn(); got == "" {
			t.Errorf("%s() returned empty string", name)
		}
	}
}
