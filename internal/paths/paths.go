package paths

import (
	"os"
	"path/filepath"
	"runtime"
)

// ClaudeDir returns ~/.claude on Unix, %LOCALAPPDATA%\claude on Windows
func ClaudeDir() string {
	if runtime.GOOS == "windows" {
		if local := os.Getenv("LOCALAPPDATA"); local != "" {
			return filepath.Join(local, "claude")
		}
	}
	home, _ := os.UserHomeDir()
	return filepath.Join(home, ".claude")
}

// OpencodeDir returns ~/.config/opencode on Unix, %APPDATA%\opencode on Windows
func OpencodeDir() string {
	if runtime.GOOS == "windows" {
		if appdata := os.Getenv("APPDATA"); appdata != "" {
			return filepath.Join(appdata, "opencode")
		}
	}
	home, _ := os.UserHomeDir()
	return filepath.Join(home, ".config", "opencode")
}

// StateDir returns ~/.config/skilar on Unix, %LOCALAPPDATA%\skilar on Windows
func StateDir() string {
	if runtime.GOOS == "windows" {
		if local := os.Getenv("LOCALAPPDATA"); local != "" {
			return filepath.Join(local, "skilar")
		}
	}
	home, _ := os.UserHomeDir()
	return filepath.Join(home, ".config", "skilar")
}

// NeuroxBinDir returns ~/.local/bin on Unix, %LOCALAPPDATA%\neurox on Windows
func NeuroxBinDir() string {
	if runtime.GOOS == "windows" {
		if local := os.Getenv("LOCALAPPDATA"); local != "" {
			return filepath.Join(local, "neurox")
		}
	}
	home, _ := os.UserHomeDir()
	return filepath.Join(home, ".local", "bin")
}

// NeuroxBinName returns "neurox" on Unix, "neurox.exe" on Windows
func NeuroxBinName() string {
	if runtime.GOOS == "windows" {
		return "neurox.exe"
	}
	return "neurox"
}
