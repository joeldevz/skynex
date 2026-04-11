package catalog

import (
	_ "embed"
	"encoding/json"
	"fmt"
	"sort"

	"github.com/joeldevz/skills/internal/models"
)

//go:embed catalog.json
var catalogJSON []byte

// Load parses the embedded catalog.
func Load() (*models.Catalog, error) {
	var cat models.Catalog
	if err := json.Unmarshal(catalogJSON, &cat); err != nil {
		return nil, fmt.Errorf("parse catalog: %w", err)
	}
	// Set ID field from map key
	for id, pkg := range cat.Packages {
		pkg.ID = id
	}
	return &cat, nil
}

// Print displays the catalog to stdout.
func Print(cat *models.Catalog) {
	fmt.Println("Supported packages:")
	ids := make([]string, 0, len(cat.Packages))
	for id := range cat.Packages {
		ids = append(ids, id)
	}
	sort.Strings(ids)
	for _, id := range ids {
		pkg := cat.Packages[id]
		fmt.Printf("  %s - %s\n", id, pkg.DisplayName)
		fmt.Printf("    Targets: %s\n", joinStrings(pkg.SupportedTargets))
		fmt.Printf("    Default version: %s\n", pkg.DefaultVersion)
	}
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
