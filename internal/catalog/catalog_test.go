package catalog_test

import (
	"testing"

	"github.com/joeldevz/skilar/internal/catalog"
)

func TestLoad_Succeeds(t *testing.T) {
	cat, err := catalog.Load()
	if err != nil {
		t.Fatalf("catalog.Load() failed: %v", err)
	}
	if cat == nil {
		t.Fatal("catalog.Load() returned nil catalog")
	}
}

func TestLoad_HasPackages(t *testing.T) {
	cat, _ := catalog.Load()
	if len(cat.Packages) == 0 {
		t.Error("catalog has no packages")
	}
}

func TestLoad_SkillsPackageExists(t *testing.T) {
	cat, _ := catalog.Load()
	pkg, ok := cat.Packages["skills"]
	if !ok {
		t.Fatal("'skills' package not found in catalog")
	}
	if pkg.ID != "skills" {
		t.Errorf("pkg.ID = %q, want 'skills'", pkg.ID)
	}
	if pkg.Adapter != "skills_repo" {
		t.Errorf("pkg.Adapter = %q, want 'skills_repo'", pkg.Adapter)
	}
	if len(pkg.SupportedTargets) == 0 {
		t.Error("skills package has no supported targets")
	}
}

func TestLoad_NeuroxPackageExists(t *testing.T) {
	cat, _ := catalog.Load()
	pkg, ok := cat.Packages["neurox"]
	if !ok {
		t.Fatal("'neurox' package not found in catalog")
	}
	if pkg.Adapter != "neurox_binary" {
		t.Errorf("pkg.Adapter = %q, want 'neurox_binary'", pkg.Adapter)
	}
	if pkg.RequiresNeurox {
		t.Error("neurox package should not require neurox (circular dependency)")
	}
}

func TestLoad_AllPackagesHaveRepoURL(t *testing.T) {
	cat, _ := catalog.Load()
	for id, pkg := range cat.Packages {
		if pkg.RepoURL == "" {
			t.Errorf("package %q has empty RepoURL", id)
		}
	}
}

func TestLoad_AllPackagesHaveDefaultVersion(t *testing.T) {
	cat, _ := catalog.Load()
	for id, pkg := range cat.Packages {
		if pkg.DefaultVersion == "" {
			t.Errorf("package %q has empty DefaultVersion", id)
		}
	}
}
