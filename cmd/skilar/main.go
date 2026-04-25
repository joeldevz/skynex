package main

import (
	"fmt"
	"os"
	"strings"
	"time"

	"github.com/joeldevz/skilar/internal/adapters"
	"github.com/joeldevz/skilar/internal/catalog"
	"github.com/joeldevz/skilar/internal/config"
	"github.com/joeldevz/skilar/internal/doctor"
	"github.com/joeldevz/skilar/internal/models"
	"github.com/joeldevz/skilar/internal/paths"
	"github.com/joeldevz/skilar/internal/preflight"
	"github.com/joeldevz/skilar/internal/profiles"
	"github.com/joeldevz/skilar/internal/prompts"
	"github.com/joeldevz/skilar/internal/runner"
)

// version is set by goreleaser via -ldflags "-X main.version=..."
var (
	version = "dev"
	commit  = "none"
	date    = "unknown"
)

func main() {
	args := parseArgs()

	if args.ShowVersion {
		fmt.Printf("skilar %s (%s) built %s\n", version, commit, date)
		os.Exit(0)
	}

	if args.Doctor {
		report := doctor.Run()
		report.Print()
		if report.HasErrors() {
			os.Exit(1)
		}
		os.Exit(0)
	}

	if args.Help {
		printUsage()
		os.Exit(0)
	}

	// profiles — list
	if args.ProfileList {
		handleProfileList()
		os.Exit(0)
	}

	// profile create
	if args.ProfileCreate {
		handleProfileCreate("")
		os.Exit(0)
	}

	// profile edit
	if args.ProfileEdit != "" {
		handleProfileEdit(args.ProfileEdit)
		os.Exit(0)
	}

	// profile delete
	if args.ProfileDelete != "" {
		handleProfileDelete(args.ProfileDelete)
		os.Exit(0)
	}

	// up
	if args.RunUp {
		handleUp(args.UpProfile, args.UpWeb, args.UpPort)
		os.Exit(0)
	}

	if args.ListPackages {
		cat, err := catalog.Load()
		if err != nil {
			fmt.Fprintf(os.Stderr, "Error: %v\n", err)
			os.Exit(1)
		}
		catalog.Print(cat)
		os.Exit(0)
	}

	// Load catalog
	cat, err := catalog.Load()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error loading catalog: %v\n", err)
		os.Exit(1)
	}

	// Load existing config
	stateDir := args.StateDir
	if stateDir == "" {
		stateDir = paths.StateDir()
	}
	cfg := config.LoadOrDefault(stateDir + "/skills.config.json")

	// Resolve request
	var request *models.InstallRequest
	if args.NonInteractive {
		request, err = resolveNonInteractive(args, cat, cfg)
	} else {
		request, err = prompts.ResolveInteractive(cat, cfg, args)
	}
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error: %v\n", err)
		os.Exit(2)
	}
	request.StateDir = stateDir

	// Preflight
	issues := preflight.Run(request, cat)
	if preflight.HasErrors(issues) {
		preflight.PrintIssues(issues)
		fmt.Fprintln(os.Stderr, "\nInstallation aborted due to validation errors.")
		os.Exit(2)
	}

	// Confirm
	if !args.NonInteractive && !args.Yes {
		if !prompts.ConfirmPlan(request, cat) {
			fmt.Println("Installation cancelled.")
			os.Exit(0)
		}
	}

	// Install
	fmt.Println("\nInstalling packages...")
	results, err := adapters.InstallAll(request, cat)
	if err != nil {
		fmt.Fprintf(os.Stderr, "\nInstallation failed: %v\n", err)
		os.Exit(1)
	}

	// Save state
	config.SaveConfig(stateDir+"/skills.config.json", request, cfg)
	config.SaveLock(stateDir+"/skills.lock.json", results, request)

	// Print results
	fmt.Println("\nInstallation complete!")
	for _, r := range results {
		fmt.Printf("\n  %s @ %s (%s)\n", r.PackageID, r.ResolvedVersion, r.Commit[:8])
		for target, tr := range r.Targets {
			fmt.Printf("    [%s] %s: %s\n", target, tr.Status, joinStrings(tr.Artifacts))
		}
	}
	fmt.Printf("\nState files written to %s\n", stateDir)
}

type cliArgs struct {
	Packages       []string
	Targets        []string
	Versions       map[string]string
	NonInteractive bool
	Yes            bool
	TrustScripts   bool
	StateDir       string
	Help           bool
	ListPackages   bool
	ListVersions   string
	AdvisorModel   string
	ShowVersion    bool
	Doctor         bool
	ProfileList    bool
	ProfileCreate  bool
	ProfileEdit    string
	ProfileDelete  string
	UpProfile      string
	UpWeb          bool
	UpPort         int
	RunUp          bool
}

func parseArgs() *cliArgs {
	args := &cliArgs{Versions: make(map[string]string)}
	osArgs := os.Args[1:]

	for i := 0; i < len(osArgs); i++ {
		switch osArgs[i] {
		case "--help", "-h":
			args.Help = true
		case "version":
			args.ShowVersion = true
		case "doctor":
			args.Doctor = true
		case "profiles":
			args.ProfileList = true
		case "profile":
			// skilar profile create [name]
			// skilar profile edit <name>
			// skilar profile delete <name>
			if i+1 < len(osArgs) {
				sub := osArgs[i+1]
				i++
				switch sub {
				case "create":
					args.ProfileCreate = true
				case "edit":
					if i+1 < len(osArgs) {
						args.ProfileEdit = osArgs[i+1]
						i++
					}
				case "delete":
					if i+1 < len(osArgs) {
						args.ProfileDelete = osArgs[i+1]
						i++
					}
				}
			}
		case "up":
			// skilar up [profile] [--web] [--port N]
			for i+1 < len(osArgs) {
				next := osArgs[i+1]
				if next == "--web" {
					args.UpWeb = true
					i++
				} else if next == "--port" && i+2 < len(osArgs) {
					fmt.Sscanf(osArgs[i+2], "%d", &args.UpPort)
					i += 2
				} else if !strings.HasPrefix(next, "-") && args.UpProfile == "" {
					args.UpProfile = next
					i++
				} else {
					break
				}
			}
			args.RunUp = true
		case "--list-packages":
			args.ListPackages = true
		case "--list-versions":
			if i+1 < len(osArgs) {
				i++
				args.ListVersions = osArgs[i]
			}
		case "--package":
			if i+1 < len(osArgs) {
				i++
				args.Packages = append(args.Packages, osArgs[i])
			}
		case "--target":
			if i+1 < len(osArgs) {
				i++
				if osArgs[i] == "both" {
					args.Targets = append(args.Targets, "claude", "opencode")
				} else {
					args.Targets = append(args.Targets, osArgs[i])
				}
			}
		case "--version":
			// Check if this is the info flag or package version flag
			if i+1 < len(osArgs) && !isFlag(osArgs[i+1]) {
				i++
				parts := splitOnce(osArgs[i], "=")
				if len(parts) == 2 {
					args.Versions[parts[0]] = parts[1]
				}
			} else {
				// --version with no arg or followed by flag = show version
				args.ShowVersion = true
			}
		case "--non-interactive":
			args.NonInteractive = true
		case "--yes", "-y":
			args.Yes = true
		case "--trust-setup-scripts":
			args.TrustScripts = true
		case "--state-dir":
			if i+1 < len(osArgs) {
				i++
				args.StateDir = osArgs[i]
			}
		case "--advisor-model":
			if i+1 < len(osArgs) {
				i++
				args.AdvisorModel = osArgs[i]
			}
		}
	}
	return args
}

func isFlag(s string) bool {
	return len(s) > 0 && s[0] == '-'
}

func splitOnce(s, sep string) []string {
	for i := 0; i < len(s); i++ {
		if s[i:i+len(sep)] == sep {
			return []string{s[:i], s[i+len(sep):]}
		}
	}
	return []string{s}
}

func joinStrings(ss []string) string {
	result := ""
	for i, s := range ss {
		if i > 0 {
			result += ", "
		}
		result += s
	}
	return result
}

func resolveNonInteractive(args *cliArgs, cat *models.Catalog, cfg map[string]interface{}) (*models.InstallRequest, error) {
	if len(args.Packages) == 0 {
		return nil, fmt.Errorf("--package is required in non-interactive mode")
	}
	if len(args.Targets) == 0 {
		return nil, fmt.Errorf("--target is required in non-interactive mode")
	}

	// Validate packages exist in catalog
	for _, pkg := range args.Packages {
		if _, ok := cat.Packages[pkg]; !ok {
			return nil, fmt.Errorf("unknown package: %s", pkg)
		}
	}

	// Resolve versions
	versions := make(map[string]string)
	for _, pkg := range args.Packages {
		if v, ok := args.Versions[pkg]; ok {
			versions[pkg] = v
		} else {
			versions[pkg] = cat.Packages[pkg].DefaultVersion
		}
	}

	req := &models.InstallRequest{
		Packages:    args.Packages,
		Targets:     args.Targets,
		Versions:    versions,
		Interactive: false,
	}

	// Advisor config from flag
	if args.AdvisorModel != "" {
		req.Advisor = &models.AdvisorConfig{
			Enabled: true,
			Model:   args.AdvisorModel,
			MaxUses: 3,
		}
	}

	return req, nil
}

func handleProfileList() {
	// Show builtin tiers first, then saved profiles
	fmt.Println("\n  Built-in tiers:")
	fmt.Printf("  %-16s %s\n", "cheap", "Haiku everywhere — fast & cheap")
	fmt.Printf("  %-16s %s\n", "balanced", "Sonnet for planning, Haiku for execution (default)")
	fmt.Printf("  %-16s %s\n", "premium", "Opus for planning, Sonnet for execution")
	fmt.Println()

	saved, err := profiles.List()
	if err != nil || len(saved) == 0 {
		fmt.Println("  No custom profiles saved.")
		fmt.Println("  Create one: skilar profile create")
		return
	}

	fmt.Println("  Custom profiles:")
	for _, p := range saved {
		fmt.Printf("  %-16s %d agents configured\n", p.Name, len(p.Models))
	}
	fmt.Println()
	fmt.Println("  Usage: skilar up <profile>")
}

func handleProfileCreate(initialName string) {
	// Call the TUI flow
	result, err := prompts.RunProfileCreationFlow(nil)
	if err != nil {
		fmt.Fprintf(os.Stderr, "Cancelled.\n")
		return
	}

	p := &profiles.Profile{
		Name:      result.Name,
		Models:    result.Models,
		CreatedAt: time.Now(),
		UpdatedAt: time.Now(),
	}

	if err := profiles.Save(p); err != nil {
		fmt.Fprintf(os.Stderr, "Error saving profile: %v\n", err)
		os.Exit(1)
	}

	fmt.Printf("\n  ✓ Profile %q saved.\n", p.Name)
	fmt.Printf("  Usage: skilar up %s\n\n", p.Name)
}

func handleProfileEdit(name string) {
	p, err := profiles.Load(name)
	if err != nil {
		fmt.Fprintf(os.Stderr, "Profile %q not found.\n", name)
		os.Exit(1)
	}

	result, err := prompts.RunProfileCreationFlow(p.Models)
	if err != nil {
		fmt.Fprintf(os.Stderr, "Cancelled.\n")
		return
	}

	p.Models = result.Models
	p.UpdatedAt = time.Now()

	if err := profiles.Save(p); err != nil {
		fmt.Fprintf(os.Stderr, "Error saving: %v\n", err)
		os.Exit(1)
	}
	fmt.Printf("\n  ✓ Profile %q updated.\n\n", p.Name)
}

func handleProfileDelete(name string) {
	if err := profiles.Delete(name); err != nil {
		fmt.Fprintf(os.Stderr, "Error: %v\n", err)
		os.Exit(1)
	}
	fmt.Printf("  ✓ Profile %q deleted.\n", name)
}

func handleUp(profileName string, web bool, port int) {
	if profileName == "" {
		profileName = "balanced" // default tier
	}

	fmt.Printf("\n  Launching OpenCode")
	if profileName != "" {
		fmt.Printf(" with profile: %s", profileName)
	}
	if web {
		fmt.Printf(" (web UI)")
	}
	if port > 0 {
		fmt.Printf(" on port %d", port)
	}
	fmt.Println()

	if err := runner.Run(runner.Options{
		Profile: profileName,
		Web:     web,
		Port:    port,
	}); err != nil {
		// If the process terminated normally (exit 0 or ctrl+c), don't treat as error
		fmt.Fprintf(os.Stderr, "opencode exited: %v\n", err)
	}
}

func printUsage() {
	fmt.Println(`Usage: skilar [command] [options]

Commands:
  install                 Interactive installer (TUI)
  doctor                  Check environment and dependencies
  version                 Show version
  profiles                List all profiles (builtin + custom)
  profile create [name]   Create a new profile (TUI)
  profile edit <name>     Edit an existing profile
  profile delete <name>   Delete a custom profile
  up [profile]            Launch OpenCode with a profile
                          Builtin: cheap, balanced, premium
                          Custom: any profile you created
  up [profile] --web      Launch web UI instead of TUI
  up [profile] --port N   Use specific port (with --web)

Examples:
  skilar up                        Launch with balanced profile
  skilar up cheap                  Haiku everywhere
  skilar up frontend               Your custom frontend profile
  skilar up frontend --web --port 3001
  skilar profile create backend
  skilar profiles

Options:
  --package PACKAGE       Package to install (skills, neurox). Repeatable.
  --target TARGET         Target: claude, opencode, or both. Repeatable.
  --version PKG=VER       Version for a package (e.g., skills=latest). Repeatable.
  --advisor-model MODEL   Advisor model (e.g., anthropic/claude-opus-4-6).
  --non-interactive       Skip prompts, require all inputs via flags.
  --yes, -y               Skip confirmation prompt.
  --trust-setup-scripts   Trust external setup scripts.
  --state-dir DIR         State directory (default: ~/.config/skilar).
  --list-packages         List available packages.
  --list-versions PKG     List versions for a package.
  --version               Show version and exit.
  -h, --help              Show this help.`)
}
