package main

import (
	"context"
	"fmt"
	"os"
	"os/signal"
	"strconv"
	"strings"
	"syscall"
	"time"

	"github.com/joeldevz/skynex/internal/eval/cases"
	"github.com/joeldevz/skynex/internal/eval/client"
	"github.com/joeldevz/skynex/internal/eval/lifecycle"
	"github.com/joeldevz/skynex/internal/eval/reporter"
	"github.com/joeldevz/skynex/internal/eval/runner"
)

const defaultPort = 4096

// SimpleJudge is a basic judge implementation
type SimpleJudge struct {
	name string
}

func (j *SimpleJudge) Name() string {
	return j.name
}

func (j *SimpleJudge) Evaluate(result map[string]interface{}, tc runner.EvalCase) ([]runner.CheckResult, float64, error) {
	// Simple pass/fail based on non-empty output
	text, ok := result["text"].(string)
	if !ok || text == "" {
		return []runner.CheckResult{
			{Name: "basic", Passed: false, Details: "no output"},
		}, 0.0, nil
	}
	return []runner.CheckResult{
		{Name: "basic", Passed: true, Details: "output present"},
	}, 1.0, nil
}

func main() {
	if len(os.Args) < 2 {
		printUsage()
		os.Exit(1)
	}

	command := os.Args[1]

	switch command {
	case "baseline":
		cmdBaseline(os.Args[2:])
	case "compare":
		cmdCompare(os.Args[2:])
	case "run":
		cmdRun(os.Args[2:])
	case "list":
		cmdList(os.Args[2:])
	case "help", "-h", "--help":
		printUsage()
		os.Exit(0)
	default:
		fmt.Fprintf(os.Stderr, "unknown command: %s\n", command)
		printUsage()
		os.Exit(1)
	}
}

func printUsage() {
	fmt.Fprintf(os.Stderr, `skynex-eval — evaluation framework

Usage:
  skynex-eval baseline --suite <name|all> [--no-llm-judge] [--cost-cap N] [--port N]
  skynex-eval compare --baseline <path> [--suite <name|all>] [--no-llm-judge] [--cost-cap N]
  skynex-eval run --case <case_id> [--no-llm-judge] [--n N]
  skynex-eval list [--suite <name>]
  skynex-eval help

Options:
  --suite <name|all>     Test suite name or 'all' (default: all)
  --no-llm-judge         Disable LLM judge
  --cost-cap N           Cost cap in dollars
  --port N               Server port (default: 4096)
  --baseline <path>      Baseline results JSON path
  --case <case_id>       Single case ID to run
  --n N                  Number of runs

`)
}

func parseFlags(args []string) map[string]string {
	flags := make(map[string]string)
	for i := 0; i < len(args); i++ {
		if strings.HasPrefix(args[i], "--") {
			key := strings.TrimPrefix(args[i], "--")
			if i+1 < len(args) && !strings.HasPrefix(args[i+1], "--") {
				flags[key] = args[i+1]
				i++
			} else {
				flags[key] = "true"
			}
		}
	}
	return flags
}

func cmdBaseline(args []string) {
	flags := parseFlags(args)

	suite, ok := flags["suite"]
	if !ok {
		suite = "all"
	}

	costCap := parseFloat(flags["cost-cap"], 0)
	port := parseInt(flags["port"], defaultPort)

	// Load cases
	allCases, err := cases.LoadAll("eval/cases")
	if err != nil {
		fmt.Fprintf(os.Stderr, "error loading cases: %v\n", err)
		os.Exit(1)
	}

	var suitesCases []cases.TestCase
	if suite == "all" {
		suitesCases = allCases
	} else {
		for _, c := range allCases {
			if c.Item == suite {
				suitesCases = append(suitesCases, c)
			}
		}
	}

	if len(suitesCases) == 0 {
		fmt.Fprintf(os.Stderr, "no cases found for suite: %s\n", suite)
		os.Exit(1)
	}

	// Start server
	cfg := lifecycle.Config{
		Port:    port,
		Timeout: 30 * time.Second,
		Binary:  "opencode",
	}
	srv := lifecycle.NewServerWithConfig(cfg)
	go func() {
		if err := srv.Start(context.Background()); err != nil {
			fmt.Fprintf(os.Stderr, "server error: %v\n", err)
		}
	}()

	// Setup graceful shutdown
	sigChan := make(chan os.Signal, 1)
	signal.Notify(sigChan, syscall.SIGINT, syscall.SIGTERM)
	defer signal.Stop(sigChan)

	go func() {
		<-sigChan
		fmt.Fprintf(os.Stderr, "\n\nshutting down...\n")
		srv.Stop()
		os.Exit(130)
	}()

	time.Sleep(500 * time.Millisecond) // Give server time to start

	// Create client
	c := client.NewClientWithBaseURL(fmt.Sprintf("http://localhost:%d", port))

	// Create judge
	judge := &SimpleJudge{name: "basic"}

	// Convert test cases to eval cases
	evalCases := convertTestCasesToEvalCases(suitesCases, suite)

	// Run suite
	fmt.Printf("Running baseline for suite: %s (%d cases)\n", suite, len(evalCases))

	result, err := runner.RunSuite(c, judge, evalCases, costCap)
	if err != nil {
		fmt.Fprintf(os.Stderr, "error running suite: %v\n", err)
		srv.Stop()
		os.Exit(1)
	}

	// Save results
	timestamp := time.Now().Format("20060102-150405")
	outputPath := fmt.Sprintf("eval/results/baseline-%s.json", timestamp)
	if err := reporter.SaveResult(result, outputPath); err != nil {
		fmt.Fprintf(os.Stderr, "error saving results: %v\n", err)
		srv.Stop()
		os.Exit(1)
	}

	fmt.Printf("\n✓ baseline saved to %s\n", outputPath)
	fmt.Printf("  Pass rate: %.1f%% (%d/%d)\n", result.PassRate*100, result.PassCount, result.TotalCases)
	fmt.Printf("  Total cost: $%.2f\n", result.TotalCost)

	// Shutdown server
	srv.Stop()
}

func cmdCompare(args []string) {
	flags := parseFlags(args)

	baseline, ok := flags["baseline"]
	if !ok {
		fmt.Fprintf(os.Stderr, "error: --baseline is required\n")
		os.Exit(1)
	}

	suite, ok := flags["suite"]
	if !ok {
		suite = "all"
	}

	costCap := parseFloat(flags["cost-cap"], 0)
	port := parseInt(flags["port"], defaultPort)

	// Load baseline
	baselineResult, err := reporter.LoadResult(baseline)
	if err != nil {
		fmt.Fprintf(os.Stderr, "error loading baseline: %v\n", err)
		os.Exit(1)
	}

	// Load cases
	allCases, err := cases.LoadAll("eval/cases")
	if err != nil {
		fmt.Fprintf(os.Stderr, "error loading cases: %v\n", err)
		os.Exit(1)
	}

	var suitesCases []cases.TestCase
	if suite == "all" {
		suitesCases = allCases
	} else {
		for _, c := range allCases {
			if c.Type == suite {
				suitesCases = append(suitesCases, c)
			}
		}
	}

	// Start server
	cfg := lifecycle.Config{
		Port:    port,
		Timeout: 30 * time.Second,
		Binary:  "opencode",
	}
	srv := lifecycle.NewServerWithConfig(cfg)
	go func() {
		if err := srv.Start(context.Background()); err != nil {
			fmt.Fprintf(os.Stderr, "server error: %v\n", err)
		}
	}()

	// Setup graceful shutdown
	sigChan := make(chan os.Signal, 1)
	signal.Notify(sigChan, syscall.SIGINT, syscall.SIGTERM)
	defer signal.Stop(sigChan)

	go func() {
		<-sigChan
		fmt.Fprintf(os.Stderr, "\n\nshutting down...\n")
		srv.Stop()
		os.Exit(130)
	}()

	time.Sleep(500 * time.Millisecond)

	// Create client
	c := client.NewClientWithBaseURL(fmt.Sprintf("http://localhost:%d", port))

	// Create judge
	judge := &SimpleJudge{name: "basic"}

	// Convert test cases to eval cases
	evalCases := convertTestCasesToEvalCases(suitesCases, suite)

	// Run suite
	fmt.Printf("Running comparison against baseline: %s\n", baseline)
	fmt.Printf("Suite: %s (%d cases)\n", suite, len(evalCases))

	currentResult, err := runner.RunSuite(c, judge, evalCases, costCap)
	if err != nil {
		fmt.Fprintf(os.Stderr, "error running suite: %v\n", err)
		srv.Stop()
		os.Exit(1)
	}

	// Compute diff
	diff := reporter.ComputeDiff(baselineResult, currentResult)

	// Print diff
	fmt.Println()
	reporter.PrintDiff(diff)

	// Shutdown server
	srv.Stop()
}

func cmdRun(args []string) {
	flags := parseFlags(args)

	caseID, ok := flags["case"]
	if !ok {
		fmt.Fprintf(os.Stderr, "error: --case is required\n")
		os.Exit(1)
	}

	nRuns := parseInt(flags["n"], 1)
	port := parseInt(flags["port"], defaultPort)

	// Load cases
	allCases, err := cases.LoadAll("eval/cases")
	if err != nil {
		fmt.Fprintf(os.Stderr, "error loading cases: %v\n", err)
		os.Exit(1)
	}

	var targetCase cases.TestCase
	found := false
	for _, c := range allCases {
		if c.ID == caseID {
			targetCase = c
			found = true
			break
		}
	}

	if !found {
		fmt.Fprintf(os.Stderr, "case not found: %s\n", caseID)
		os.Exit(1)
	}

	// Start server
	cfg := lifecycle.Config{
		Port:    port,
		Timeout: 30 * time.Second,
		Binary:  "opencode",
	}
	srv := lifecycle.NewServerWithConfig(cfg)
	go func() {
		if err := srv.Start(context.Background()); err != nil {
			fmt.Fprintf(os.Stderr, "server error: %v\n", err)
		}
	}()

	// Setup graceful shutdown
	sigChan := make(chan os.Signal, 1)
	signal.Notify(sigChan, syscall.SIGINT, syscall.SIGTERM)
	defer signal.Stop(sigChan)

	go func() {
		<-sigChan
		fmt.Fprintf(os.Stderr, "\n\nshutting down...\n")
		srv.Stop()
		os.Exit(130)
	}()

	time.Sleep(500 * time.Millisecond)

	// Create client
	c := client.NewClientWithBaseURL(fmt.Sprintf("http://localhost:%d", port))

	// Create judge
	judge := &SimpleJudge{name: "basic"}

	// Convert test case to eval case
	evalCase := convertTestCaseToEvalCase(targetCase, "")

	// Run case
	fmt.Printf("Running case: %s (n=%d)\n", caseID, nRuns)

	for i := 1; i <= nRuns; i++ {
		fmt.Printf("[%d/%d] executing...\n", i, nRuns)

		res, err := runner.RunCase(c, judge, evalCase, 0)
		if err != nil {
			fmt.Fprintf(os.Stderr, "error running case: %v\n", err)
			srv.Stop()
			os.Exit(1)
		}

		fmt.Printf("  Status: %s\n", res.Status)
		fmt.Printf("  Score: %.4f\n", res.Score)
		fmt.Printf("  Pass count: %d\n", res.PassCount)
		fmt.Println()
	}

	// Shutdown server
	srv.Stop()
}

func cmdList(args []string) {
	flags := parseFlags(args)

	suite, ok := flags["suite"]
	if !ok {
		suite = "all"
	}

	// Load cases
	allCases, err := cases.LoadAll("eval/cases")
	if err != nil {
		fmt.Fprintf(os.Stderr, "error loading cases: %v\n", err)
		os.Exit(1)
	}

	var suitesCases []cases.TestCase
	if suite == "all" {
		suitesCases = allCases
	} else {
		for _, c := range allCases {
			if c.Item == suite {
				suitesCases = append(suitesCases, c)
			}
		}
	}

	if len(suitesCases) == 0 {
		fmt.Fprintf(os.Stderr, "no cases found for suite: %s\n", suite)
		os.Exit(1)
	}

	// Print table
	fmt.Printf("Cases in suite: %s (%d)\n\n", suite, len(suitesCases))
	fmt.Printf("%-40s | %-20s | %-15s | %-5s\n", "ID", "Item", "Type", "Runs")
	fmt.Println(strings.Repeat("-", 85))

	for _, c := range suitesCases {
		nRuns := c.NRuns
		if nRuns == 0 {
			nRuns = 1
		}
		fmt.Printf("%-40s | %-20s | %-15s | %-5d\n", c.ID, c.Item, c.Type, nRuns)
	}

	fmt.Println()
}

func convertTestCasesToEvalCases(testCases []cases.TestCase, suite string) []runner.EvalCase {
	var evalCases []runner.EvalCase
	for _, tc := range testCases {
		evalCases = append(evalCases, convertTestCaseToEvalCase(tc, suite))
	}
	return evalCases
}

func convertTestCaseToEvalCase(tc cases.TestCase, suite string) runner.EvalCase {
	var turns []runner.Turn
	for _, t := range tc.Turns {
		turns = append(turns, runner.Turn{
			Role:    "user",
			Content: t.Answer,
		})
	}

	if suite == "" {
		suite = tc.Type
	}

	return runner.EvalCase{
		ID:       tc.ID,
		Suite:    suite,
		Item:     tc.Item,
		Type:     tc.Type,
		Agent:    tc.Agent,
		Input:    tc.Input,
		Turns:    turns,
		MaxTurns: tc.MaxTurns,
		NRuns:    tc.NRuns,
	}
}

func parseInt(s string, defaultVal int) int {
	if s == "" {
		return defaultVal
	}
	val, err := strconv.Atoi(s)
	if err != nil {
		return defaultVal
	}
	return val
}

func parseFloat(s string, defaultVal float64) float64 {
	if s == "" {
		return defaultVal
	}
	val, err := strconv.ParseFloat(s, 64)
	if err != nil {
		return defaultVal
	}
	return val
}
