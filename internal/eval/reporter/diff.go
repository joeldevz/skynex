package reporter

import (
	"fmt"

	"github.com/joeldevz/skynex/internal/eval/runner"
)

// DiffReport compares baseline vs current SuiteResult
type DiffReport struct {
	Items   []ItemDiff
	Summary DiffSummary
}

// ItemDiff represents the difference for a single test case
type ItemDiff struct {
	CaseID     string
	Item       string
	BaseScore  float64
	CurrScore  float64
	Delta      float64
	BaseStatus string
	CurrStatus string
	Regressed  bool
	Improved   bool
	PassCount  int
}

// DiffSummary contains aggregated diff statistics
type DiffSummary struct {
	TotalCases    int
	Improved      int
	Regressed     int
	Unchanged     int
	BasePassRate  float64
	CurrPassRate  float64
	DeltaPassRate float64
	BaseCost      float64
	CurrCost      float64
}

// ComputeDiff compares baseline vs current SuiteResult
func ComputeDiff(baseline, current *runner.SuiteResult) *DiffReport {
	if baseline == nil || current == nil {
		return &DiffReport{
			Items:   []ItemDiff{},
			Summary: DiffSummary{},
		}
	}

	report := &DiffReport{
		Items: []ItemDiff{},
	}

	// Build map of baseline cases for quick lookup
	baselineMap := make(map[string]runner.CaseResult)
	for _, c := range baseline.Items {
		baselineMap[c.ID] = c
	}

	// Compare each current case against baseline
	for _, currCase := range current.Items {
		baseCase, exists := baselineMap[currCase.ID]

		baseScore := 0.0
		baseStatus := "missing"
		if exists {
			baseScore = baseCase.Score
			baseStatus = baseCase.Status
		}

		delta := currCase.Score - baseScore
		improved := delta > 0.01 && exists // small epsilon for floating point
		regressed := delta < -0.01 && exists

		report.Items = append(report.Items, ItemDiff{
			CaseID:     currCase.ID,
			Item:       currCase.Item,
			BaseScore:  baseScore,
			CurrScore:  currCase.Score,
			Delta:      delta,
			BaseStatus: baseStatus,
			CurrStatus: currCase.Status,
			Regressed:  regressed,
			Improved:   improved,
			PassCount:  currCase.PassCount,
		})

		if improved {
			report.Summary.Improved++
		} else if regressed {
			report.Summary.Regressed++
		} else {
			report.Summary.Unchanged++
		}
	}

	report.Summary.TotalCases = len(current.Items)
	report.Summary.BasePassRate = baseline.PassRate
	report.Summary.CurrPassRate = current.PassRate
	report.Summary.DeltaPassRate = current.PassRate - baseline.PassRate
	report.Summary.BaseCost = baseline.TotalCost
	report.Summary.CurrCost = current.TotalCost

	return report
}

// PrintDiff prints a formatted diff report to stdout
func PrintDiff(report *DiffReport) {
	if report == nil {
		fmt.Println("No diff report available")
		return
	}

	const (
		ansiGreen = "\033[32m"
		ansiRed   = "\033[31m"
		ansiReset = "\033[0m"
		ansiBlod  = "\033[1m"
	)

	// Print header
	fmt.Println("╔══════════════════════════════════════════════════╗")
	fmt.Println("║              EVALUATION DIFF REPORT              ║")
	fmt.Println("╠══════════════════════════════════════════════════╣")

	// Print metrics
	passRateDelta := report.Summary.DeltaPassRate * 100
	costDelta := report.Summary.CurrCost - report.Summary.BaseCost
	costDeltaPercent := 0.0
	if report.Summary.BaseCost > 0 {
		costDeltaPercent = (costDelta / report.Summary.BaseCost) * 100
	}

	passRateIcon := ""
	if passRateDelta > 0 {
		passRateIcon = ansiGreen + "✅" + ansiReset
	} else if passRateDelta < 0 {
		passRateIcon = ansiRed + "❌" + ansiReset
	}

	costIcon := ""
	if costDelta < 0 {
		costIcon = ansiGreen + "✅" + ansiReset
	} else if costDelta > 0 {
		costIcon = ansiRed + "⚠️ " + ansiReset
	}

	fmt.Printf("║  Metric           Baseline   Current    Δ       ║\n")
	fmt.Printf("║  Pass rate        %.0f%%        %.0f%%        %+.0f%% %s ║\n",
		report.Summary.BasePassRate*100,
		report.Summary.CurrPassRate*100,
		passRateDelta,
		passRateIcon)
	fmt.Printf("║  Cost             $%.2f      $%.2f      %+.1f%% %s ║\n",
		report.Summary.BaseCost,
		report.Summary.CurrCost,
		costDeltaPercent,
		costIcon)

	fmt.Println("╠══════════════════════════════════════════════════╣")

	// Print summary counts
	fmt.Printf("║  Cases improved:  %d                             ║\n", report.Summary.Improved)
	if report.Summary.Regressed > 0 {
		fmt.Printf("║  Cases regressed: %d  ← ", report.Summary.Regressed)
		// Print first regressed case
		for _, item := range report.Items {
			if item.Regressed {
				fmt.Printf("%s", item.CaseID)
				break
			}
		}
		fmt.Println()
		fmt.Printf("║%-50s║\n", "")
	} else {
		fmt.Printf("║  Cases regressed: 0                              ║\n")
	}
	fmt.Printf("║  Cases unchanged: %d                            ║\n", report.Summary.Unchanged)

	fmt.Println("╚══════════════════════════════════════════════════╝")
}
