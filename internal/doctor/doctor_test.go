package doctor_test

import (
	"testing"

	"github.com/joeldevz/skilar/internal/doctor"
)

func TestRun_ReturnsReport(t *testing.T) {
	r := doctor.Run()
	if r == nil {
		t.Fatal("Run() returned nil")
	}
}

func TestRun_HasChecks(t *testing.T) {
	r := doctor.Run()
	if len(r.Checks) == 0 {
		t.Error("Run() returned report with no checks")
	}
}

func TestRun_HasCanInstall(t *testing.T) {
	r := doctor.Run()
	if len(r.CanInstall) == 0 {
		t.Error("Run() returned report with no CanInstall map")
	}
	// Both targets should be present
	if _, ok := r.CanInstall["claude"]; !ok {
		t.Error("CanInstall missing 'claude' target")
	}
	if _, ok := r.CanInstall["opencode"]; !ok {
		t.Error("CanInstall missing 'opencode' target")
	}
}

func TestRun_ChecksHaveNames(t *testing.T) {
	r := doctor.Run()
	for i, c := range r.Checks {
		if c.Name == "" {
			t.Errorf("check[%d] has empty Name", i)
		}
		if c.Status == "" {
			t.Errorf("check[%d] has empty Status", i)
		}
	}
}

func TestReport_Print_NoPanic(t *testing.T) {
	r := doctor.Run()
	// Should not panic even if stdout is not a terminal
	defer func() {
		if rec := recover(); rec != nil {
			t.Errorf("Print() panicked: %v", rec)
		}
	}()
	r.Print()
}
