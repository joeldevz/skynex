package runner

import (
	"fmt"
	"os"
	"os/exec"

	"github.com/joeldevz/skynex/internal/profiles"
)

// Options configures how to launch OpenCode.
type Options struct {
	Profile string // profile name or builtin tier ("cheap", "balanced", "premium")
	Web     bool   // use "opencode web" instead of "opencode"
	Port    int    // port (0 = default)
}

// Run launches OpenCode with the given profile.
// If profile is empty, launches OpenCode without modifying env.
func Run(opts Options) error {
	var configContent string

	if opts.Profile != "" {
		// 1. Check builtin tiers first
		p, ok := profiles.BuiltinTiers[opts.Profile]
		if !ok {
			// 2. Check saved profiles
			var err error
			p, err = profiles.Load(opts.Profile)
			if err != nil {
				return fmt.Errorf("profile %q not found (builtin tiers: cheap, balanced, premium)", opts.Profile)
			}
		}

		content, err := profiles.ToEnvContent(p)
		if err != nil {
			return fmt.Errorf("build config: %w", err)
		}
		configContent = content
		fmt.Printf("  Profile: %s\n", opts.Profile)
	}

	// Build command
	subcommand := "opencode"
	args := []string{}

	if opts.Web {
		args = append(args, "web")
	}

	if opts.Port > 0 {
		args = append(args, "--port", fmt.Sprintf("%d", opts.Port))
	}

	cmd := exec.Command(subcommand, args...)
	cmd.Stdin = os.Stdin
	cmd.Stdout = os.Stdout
	cmd.Stderr = os.Stderr

	// Inherit env + add OPENCODE_CONFIG_CONTENT if profile is set
	cmd.Env = os.Environ()
	if configContent != "" {
		cmd.Env = append(cmd.Env, "OPENCODE_CONFIG_CONTENT="+configContent)
	}

	return cmd.Run()
}
