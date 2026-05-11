package runner

import (
	"encoding/json"
	"fmt"
	"sort"
	"strings"
	"time"

	"github.com/joeldevz/skynex/internal/eval/client"
	"github.com/joeldevz/skynex/internal/eval/metrics"
)

// EvalCase represents a single evaluation test case
type EvalCase struct {
	ID            string                 // unique case identifier
	Suite         string                 // suite name
	Item          string                 // item being tested
	Type          string                 // test type
	Agent         string                 // agent type to test
	Input         string                 // initial input message
	Turns         []Turn                 // multi-turn responses (optional)
	MaxTurns      int                    // max turns (default 10)
	NRuns         int                    // number of runs for aggregation
	AggMethod     string                 // aggregation method: min, median, mean
	Judges        []string               // judge names to apply
	ExpectedFiles []string               // expected output files
	Checks        map[string]interface{} // custom check configurations
}

// Turn represents a multi-turn response
type Turn struct {
	Role    string // "user" or "assistant"
	Content string // message content
}

// CaseResult holds the result of a single test case execution
type CaseResult struct {
	ID                 string
	Item               string
	Status             string  // "pass" or "fail"
	DeterministicScore float64 // 0.0 - 1.0
	LLMScore           float64 // 0.0 - 10.0
	Score              float64
	PassCount          int
	Checks             []CheckResult
	Metrics            metrics.MetricsData
	RawResponse        json.RawMessage
	Error              string
	Cost               float64
}

// MetricsData holds performance metrics from an execution
type MetricsData = metrics.MetricsData

// CheckResult represents the result of a single judge check
type CheckResult struct {
	Name    string
	Passed  bool
	Details string
}

// SuiteResult holds the result of running an entire test suite
type SuiteResult struct {
	Timestamp  time.Time
	SuiteName  string
	TotalCases int
	PassCount  int
	PassRate   float64
	TotalCost  float64
	Items      []CaseResult
}

// Judge interface for test evaluation
type Judge interface {
	Evaluate(result map[string]interface{}, tc EvalCase) ([]CheckResult, float64, error)
	Name() string
}

// RunCase executes a single test case
func RunCase(c *client.Client, judge Judge, tc EvalCase, costCap float64) (*CaseResult, error) {
	if costCap > 0 {
		// Check accumulated cost (would need global tracking in production)
		// For now, just track per-case cost
	}

	result := &CaseResult{
		ID:      tc.ID,
		Item:    tc.Item,
		Checks:  []CheckResult{},
		Metrics: metrics.MetricsData{},
	}

	// Create session
	session, err := c.CreateSession(tc.Agent)
	if err != nil {
		result.Error = fmt.Sprintf("failed to create session: %v", err)
		result.Status = "fail"
		return result, err
	}

	// Send initial message as a single text part
	parts := []client.Part{
		{
			Type: "text",
			Text: tc.Input,
		},
	}
	response, err := c.SendMessage(session.ID, tc.Agent, parts)
	if err != nil {
		result.Error = fmt.Sprintf("failed to send initial message: %v", err)
		result.Status = "fail"
		return result, err
	}

	// Store raw response for debugging
	rawBytes, _ := json.Marshal(response)
	result.RawResponse = rawBytes

	// Handle multi-turn conversation if needed
	if len(tc.Turns) > 0 {
		turnCount := 0
		maxTurns := tc.MaxTurns
		if maxTurns == 0 {
			maxTurns = 10
		}

		for turnCount < maxTurns && !isTestDone(response) {
			var nextContent string
			if turnCount < len(tc.Turns) {
				nextContent = tc.Turns[turnCount].Content
			} else {
				nextContent = "use recommended"
			}

			turnCount++

			// Send next turn
			turnParts := []client.Part{
				{
					Type: "text",
					Text: nextContent,
				},
			}
			response, err = c.SendMessage(session.ID, tc.Agent, turnParts)
			if err != nil {
				result.Error = fmt.Sprintf("failed to send turn %d: %v", turnCount, err)
				result.Status = "fail"
				return result, err
			}

			rawBytes, _ = json.Marshal(response)
			result.RawResponse = rawBytes
		}
	}

	// Collect all messages
	messages, err := c.GetMessages(session.ID)
	if err != nil {
		result.Error = fmt.Sprintf("failed to get messages: %v", err)
		result.Status = "fail"
		return result, err
	}

	// Build run result from messages
	runResult := buildRunResult(messages)

	// Extract metrics
	metricsData := metrics.ExtractMetrics(response, messages)
	result.Metrics = *metricsData
	result.Cost = metricsData.CostUSD

	// Run judge
	checks, score, err := judge.Evaluate(runResult, tc)
	if err != nil {
		result.Error = fmt.Sprintf("judge error: %v", err)
	}
	result.Checks = checks

	// Calculate deterministic score from checks
	if len(checks) > 0 {
		passed := 0
		for _, check := range checks {
			if check.Passed {
				passed++
			}
		}
		result.DeterministicScore = float64(passed) / float64(len(checks))
		result.PassCount = passed
	}

	// Use judge score if available
	result.LLMScore = score
	result.Score = score
	if result.Score < 0.7 {
		result.Score = result.DeterministicScore
	}

	// Set status based on threshold
	if result.Score >= 0.7 {
		result.Status = "pass"
	} else {
		result.Status = "fail"
	}

	return result, nil
}

// RunCaseNTimes runs a case N times and aggregates results
func RunCaseNTimes(c *client.Client, judge Judge, tc EvalCase, n int, costCap float64) (*CaseResult, error) {
	var scores []float64
	var lastResult *CaseResult

	for i := 0; i < n; i++ {
		result, err := RunCase(c, judge, tc, costCap)
		if err != nil {
			return nil, fmt.Errorf("run %d failed: %w", i+1, err)
		}
		scores = append(scores, result.Score)
		lastResult = result
	}

	// Aggregate scores
	var aggregatedScore float64
	method := strings.ToLower(tc.AggMethod)
	if method == "" {
		method = "mean"
	}

	switch method {
	case "min":
		aggregatedScore = scores[0]
		for _, s := range scores[1:] {
			if s < aggregatedScore {
				aggregatedScore = s
			}
		}
	case "median":
		sortedScores := make([]float64, len(scores))
		copy(sortedScores, scores)
		sort.Float64s(sortedScores)
		if len(sortedScores)%2 == 1 {
			aggregatedScore = sortedScores[len(sortedScores)/2]
		} else {
			aggregatedScore = (sortedScores[len(sortedScores)/2-1] + sortedScores[len(sortedScores)/2]) / 2.0
		}
	case "mean", "avg":
		sum := 0.0
		for _, s := range scores {
			sum += s
		}
		aggregatedScore = sum / float64(len(scores))
	default:
		aggregatedScore = lastResult.Score
	}

	// Update the result with aggregated score
	if lastResult != nil {
		lastResult.Score = aggregatedScore
		if aggregatedScore >= 0.7 {
			lastResult.Status = "pass"
		} else {
			lastResult.Status = "fail"
		}
	}

	return lastResult, nil
}

// RunSuite runs all test cases in a suite
func RunSuite(c *client.Client, judge Judge, testCases []EvalCase, costCap float64) (*SuiteResult, error) {
	startTime := time.Now()
	result := &SuiteResult{
		Timestamp:  startTime,
		TotalCases: len(testCases),
		Items:      []CaseResult{},
	}

	accumulatedCost := 0.0

	for _, tc := range testCases {
		if costCap > 0 && accumulatedCost >= costCap {
			break
		}

		nRuns := tc.NRuns
		if nRuns == 0 {
			nRuns = 1
		}

		var caseResult *CaseResult
		var err error

		if nRuns > 1 {
			caseResult, err = RunCaseNTimes(c, judge, tc, nRuns, costCap)
		} else {
			caseResult, err = RunCase(c, judge, tc, costCap)
		}

		if err != nil && caseResult == nil {
			return nil, err
		}

		if caseResult != nil {
			result.Items = append(result.Items, *caseResult)
			if caseResult.Status == "pass" {
				result.PassCount++
			}
			accumulatedCost += caseResult.Cost
		}
	}

	result.TotalCost = accumulatedCost
	if result.TotalCases > 0 {
		result.PassRate = float64(result.PassCount) / float64(result.TotalCases)
	}

	return result, nil
}

// Helper functions

// isTestDone checks if the test execution is complete
func isTestDone(response *client.Response) bool {
	// Check if response indicates completion
	if response == nil {
		return false
	}
	// TODO: implement artifact detection or max turns check
	return false
}

// buildRunResult constructs a run result map from messages
func buildRunResult(messages []client.Message) map[string]interface{} {
	result := make(map[string]interface{})

	var text strings.Builder
	toolCalls := []interface{}{}
	filesWritten := []string{}
	subagentCalls := []string{}

	for _, msg := range messages {
		for _, part := range msg.Parts {
			switch part.Type {
			case "text":
				text.WriteString(part.Text)
				text.WriteString("\n")
			case "tool":
				toolCalls = append(toolCalls, map[string]interface{}{
					"name": part.Tool,
					"args": part.ToolInput,
				})
				// Track file writes
				if part.Tool == "write" || part.Tool == "edit" {
					var toolInput map[string]interface{}
					err := json.Unmarshal(part.ToolInput, &toolInput)
					if err == nil {
						if path, ok := toolInput["filePath"].(string); ok {
							filesWritten = append(filesWritten, path)
						}
					}
				}
				// Track subagent calls
				if part.Tool == "task" {
					var toolInput map[string]interface{}
					err := json.Unmarshal(part.ToolInput, &toolInput)
					if err == nil {
						if subtype, ok := toolInput["subagent_type"].(string); ok {
							subagentCalls = append(subagentCalls, subtype)
						}
					}
				}
			}
		}
	}

	result["text"] = text.String()
	result["toolCalls"] = toolCalls
	result["filesWritten"] = filesWritten
	result["subagentCalls"] = subagentCalls

	return result
}
