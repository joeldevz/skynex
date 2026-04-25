package doctor

import (
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"runtime"
	"strings"

	"github.com/joeldevz/skilar/internal/paths"
)

// Check represents the result of an individual check.
type Check struct {
	Name    string
	Status  string // "ok", "warn", "error", "skip"
	Detail  string
	FixHint string
}

// Report is the complete result of the doctor.
type Report struct {
	Checks     []*Check
	CanInstall map[string]bool // target -> can install
}

// Run executes all checks and returns the report.
func Run() *Report {
	r := &Report{
		CanInstall: map[string]bool{
			"claude":   true,
			"opencode": true,
		},
	}

	// Core tools
	r.checkTool("git", "git", "--version", "https://git-scm.com/downloads", true)
	r.checkTool("neurox", "neurox", "version", "Run: skilar --package neurox", true)

	// AI tools (optional — detect what's installed)
	r.checkTool("claude", "claude", "--version", "https://claude.ai/download", false)
	r.checkTool("opencode", "opencode", "--version", "https://opencode.ai", false)

	// JS runtime (needed for opencode target)
	hasBun := r.checkToolAny("bun / npm", []string{"bun", "npm"}, "Install bun: https://bun.sh", false)
	if !hasBun {
		r.CanInstall["opencode"] = false
	}

	// Writable dirs
	r.checkWritable("~/.claude", paths.ClaudeDir(), "claude")
	r.checkWritable("~/.config/opencode", paths.OpencodeDir(), "opencode")

	// Platform info
	r.addInfo(fmt.Sprintf("Platform: %s/%s", runtime.GOOS, runtime.GOARCH))

	return r
}

func (r *Report) checkTool(name, binary, versionFlag, fixHint string, required bool) bool {
	path, err := exec.LookPath(binary)
	if err != nil {
		status := "warn"
		if required {
			status = "error"
		}
		r.Checks = append(r.Checks, &Check{
			Name:    name,
			Status:  status,
			Detail:  "not found in PATH",
			FixHint: fixHint,
		})
		return false
	}

	// Get version
	out, err := exec.Command(binary, versionFlag).Output()
	version := ""
	if err == nil {
		version = strings.TrimSpace(strings.Split(string(out), "\n")[0])
		// Truncate long version strings
		if len(version) > 60 {
			version = version[:60] + "..."
		}
	}

	detail := path
	if version != "" {
		detail = fmt.Sprintf("%s (%s)", path, version)
	}

	r.Checks = append(r.Checks, &Check{
		Name:   name,
		Status: "ok",
		Detail: detail,
	})
	return true
}

func (r *Report) checkToolAny(name string, binaries []string, fixHint string, required bool) bool {
	for _, b := range binaries {
		if path, err := exec.LookPath(b); err == nil {
			r.Checks = append(r.Checks, &Check{
				Name:   name,
				Status: "ok",
				Detail: path,
			})
			return true
		}
	}
	status := "warn"
	if required {
		status = "error"
	}
	r.Checks = append(r.Checks, &Check{
		Name:    name,
		Status:  status,
		Detail:  fmt.Sprintf("none of %s found in PATH", strings.Join(binaries, ", ")),
		FixHint: fixHint,
	})
	return false
}

func (r *Report) checkWritable(name, dir, target string) {
	// Try to create dir if not exists
	if err := os.MkdirAll(dir, 0o755); err != nil {
		r.Checks = append(r.Checks, &Check{
			Name:    name,
			Status:  "error",
			Detail:  fmt.Sprintf("cannot create directory: %v", err),
			FixHint: fmt.Sprintf("Check permissions on %s", filepath.Dir(dir)),
		})
		r.CanInstall[target] = false
		return
	}

	// Try write
	tmp := filepath.Join(dir, ".skilar-doctor-check")
	if err := os.WriteFile(tmp, []byte("test"), 0o644); err != nil {
		r.Checks = append(r.Checks, &Check{
			Name:    name,
			Status:  "error",
			Detail:  fmt.Sprintf("not writable: %v", err),
			FixHint: fmt.Sprintf("Run: chmod u+w %s", dir),
		})
		r.CanInstall[target] = false
		return
	}
	os.Remove(tmp)

	r.Checks = append(r.Checks, &Check{
		Name:   name,
		Status: "ok",
		Detail: fmt.Sprintf("%s (writable)", dir),
	})
}

func (r *Report) addInfo(detail string) {
	r.Checks = append(r.Checks, &Check{
		Name:   "platform",
		Status: "ok",
		Detail: detail,
	})
}

// Print prints the report to stdout with colors if available.
func (r *Report) Print() {
	useColors := isTerminal()

	green := colorFn(useColors, "\033[0;32m")
	yellow := colorFn(useColors, "\033[1;33m")
	red := colorFn(useColors, "\033[0;31m")
	dim := colorFn(useColors, "\033[2m")
	bold := colorFn(useColors, "\033[1m")
	reset := colorFn(useColors, "\033[0m")

	fmt.Println()
	fmt.Printf("%skilar doctor%s\n", bold, reset)
	fmt.Println(strings.Repeat("─", 50))

	for _, c := range r.Checks {
		var icon, color string
		switch c.Status {
		case "ok":
			icon = "✓"
			color = green
		case "warn":
			icon = "⚠"
			color = yellow
		case "error":
			icon = "✗"
			color = red
		default:
			icon = "·"
			color = dim
		}

		fmt.Printf("  %s%s%s  %-20s %s%s%s\n",
			color, icon, reset,
			c.Name,
			dim, c.Detail, reset,
		)

		if c.FixHint != "" {
			fmt.Printf("     %s   Fix: %s%s\n", "", c.FixHint, reset)
		}
	}

	fmt.Println(strings.Repeat("─", 50))

	// Summary
	fmt.Println()
	for target, ok := range r.CanInstall {
		if ok {
			fmt.Printf("  %s✓%s  Ready for %starget: %s%s\n", green, reset, bold, target, reset)
		} else {
			fmt.Printf("  %s✗%s  Missing deps for %starget: %s%s\n", red, reset, bold, target, reset)
		}
	}
	fmt.Println()
}

func isTerminal() bool {
	fi, err := os.Stdout.Stat()
	if err != nil {
		return false
	}
	return (fi.Mode() & os.ModeCharDevice) != 0
}

func colorFn(active bool, code string) string {
	if active {
		return code
	}
	return ""
}

// HasErrors returns true if any check has status "error".
func (r *Report) HasErrors() bool {
	for _, c := range r.Checks {
		if c.Status == "error" {
			return true
		}
	}
	return false
}
