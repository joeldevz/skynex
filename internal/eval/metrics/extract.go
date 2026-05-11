package metrics

import (
	"encoding/json"
	"strings"

	"github.com/joeldevz/skynex/internal/eval/client"
)

// MetricsData holds performance metrics from an execution
type MetricsData struct {
	TokensTotal   int
	TokensOutput  int
	TokensCached  int
	CostUSD       float64
	DurationMS    int64
	ToolCallCount int
	SubagentCalls []string
	FilesWritten  []string
}

// ExtractMetrics extracts and calculates metrics from responses
func ExtractMetrics(response *client.Response, messages []client.Message) *MetricsData {
	metricsData := &MetricsData{
		TokensTotal:   response.Info.Tokens.Total,
		TokensOutput:  response.Info.Tokens.Output,
		TokensCached:  response.Info.Tokens.CacheRead,
		CostUSD:       response.Info.Cost,
		DurationMS:    int64(response.Info.Duration.Milliseconds()),
		SubagentCalls: []string{},
		FilesWritten:  []string{},
	}

	// If cost is not provided, calculate from tokens
	if metricsData.CostUSD <= 0 {
		metricsData.CostUSD = CalculateCost(response.Info.Tokens, response.Info.ModelID)
	}

	// Count tool calls and extract subagent calls and files written
	for _, msg := range messages {
		for _, part := range msg.Parts {
			if part.Type == "tool" {
				metricsData.ToolCallCount++

				// Parse tool input to extract subagent calls and file writes
				var toolInput map[string]interface{}
				err := json.Unmarshal(part.ToolInput, &toolInput)
				if err != nil {
					continue
				}

				// Track subagent calls
				if part.Tool == "task" {
					if subtype, ok := toolInput["subagent_type"].(string); ok {
						metricsData.SubagentCalls = append(metricsData.SubagentCalls, subtype)
					}
				}

				// Track file writes
				if part.Tool == "write" || part.Tool == "edit" {
					if filePath, ok := toolInput["filePath"].(string); ok {
						metricsData.FilesWritten = append(metricsData.FilesWritten, filePath)
					}
				}
			}
		}
	}

	return metricsData
}

// CalculateCost calculates the cost based on token counts and model
func CalculateCost(tokens client.TokenInfo, model string) float64 {
	// Normalize model identifier
	model = strings.ToLower(model)

	// Determine pricing based on model
	var inputCost, outputCost, cacheReadCost float64

	// Check for Sonnet
	if strings.Contains(model, "sonnet") {
		// Sonnet: input=$3/MTok, output=$15/MTok, cache_read=$0.30/MTok
		inputCost = 3.0
		outputCost = 15.0
		cacheReadCost = 0.30
	} else if strings.Contains(model, "opus") {
		// Opus: input=$15/MTok, output=$75/MTok
		inputCost = 15.0
		outputCost = 75.0
		cacheReadCost = 1.5 // Assume 10% of input cost for cache read
	} else if strings.Contains(model, "haiku") {
		// Haiku: input=$0.25/MTok, output=$1.25/MTok
		inputCost = 0.25
		outputCost = 1.25
		cacheReadCost = 0.025 // Assume 10% of input cost for cache read
	} else {
		// Default to Haiku pricing for unknown models
		inputCost = 0.25
		outputCost = 1.25
		cacheReadCost = 0.025
	}

	// Calculate cost: per million tokens
	inputTokenCost := (float64(tokens.Input) / 1_000_000) * inputCost
	outputTokenCost := (float64(tokens.Output) / 1_000_000) * outputCost
	cacheReadTokenCost := (float64(tokens.CacheRead) / 1_000_000) * cacheReadCost

	return inputTokenCost + outputTokenCost + cacheReadTokenCost
}
