package prompts

import (
	"fmt"
	"os"
	"sort"
	"strings"

	tea "github.com/charmbracelet/bubbletea"
	"github.com/charmbracelet/lipgloss"
	"github.com/joeldevz/skills/internal/models"
)

var (
	titleStyle    = lipgloss.NewStyle().Bold(true).Foreground(lipgloss.Color("39"))
	selectedStyle = lipgloss.NewStyle().Foreground(lipgloss.Color("42"))
	dimStyle      = lipgloss.NewStyle().Foreground(lipgloss.Color("240"))
)

// AdvisorModels is the curated list of models for the advisor picker.
var AdvisorModels = []models.AdvisorModel{
	{ID: "anthropic/claude-opus-4-6", DisplayName: "Claude Opus 4.6", Provider: "Anthropic", Description: "Most capable — best for complex strategic decisions"},
	{ID: "anthropic/claude-sonnet-4-6", DisplayName: "Claude Sonnet 4.6", Provider: "Anthropic", Description: "Good balance of capability and cost"},
	{ID: "openai/gpt-4o", DisplayName: "GPT-4o", Provider: "OpenAI", Description: "Strong reasoning, multi-modal"},
	{ID: "openai/o3", DisplayName: "o3", Provider: "OpenAI", Description: "Advanced reasoning model"},
	{ID: "google/gemini-2.5-pro", DisplayName: "Gemini 2.5 Pro", Provider: "Google", Description: "Strong reasoning, large context window"},
	{ID: "anthropic/claude-haiku-4-5", DisplayName: "Claude Haiku 4.5", Provider: "Anthropic", Description: "Fast and cheap — good for simple advice"},
}

// --- Multi-select model ---

type multiSelectModel struct {
	title    string
	options  []string
	cursor   int
	selected map[int]bool
	done     bool
}

func newMultiSelect(title string, options []string, defaults []int) multiSelectModel {
	sel := make(map[int]bool)
	for _, i := range defaults {
		sel[i] = true
	}
	return multiSelectModel{title: title, options: options, selected: sel}
}

func (m multiSelectModel) Init() tea.Cmd { return nil }

func (m multiSelectModel) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
	switch msg := msg.(type) {
	case tea.KeyMsg:
		switch msg.String() {
		case "up", "k":
			if m.cursor > 0 {
				m.cursor--
			}
		case "down", "j":
			if m.cursor < len(m.options)-1 {
				m.cursor++
			}
		case " ":
			m.selected[m.cursor] = !m.selected[m.cursor]
		case "enter":
			m.done = true
			return m, tea.Quit
		case "q", "ctrl+c":
			fmt.Println("Cancelled.")
			os.Exit(0)
		}
	}
	return m, nil
}

func (m multiSelectModel) View() string {
	s := titleStyle.Render(m.title) + "\n"
	s += dimStyle.Render("  (space to toggle, enter to confirm)") + "\n\n"
	for i, opt := range m.options {
		cursor := "  "
		if i == m.cursor {
			cursor = "> "
		}
		check := "[ ]"
		style := lipgloss.NewStyle()
		if m.selected[i] {
			check = "[x]"
			style = selectedStyle
		}
		s += style.Render(fmt.Sprintf("%s%s %s", cursor, check, opt)) + "\n"
	}
	return s
}

// --- Single-select model ---

type singleSelectModel struct {
	title   string
	options []string
	descs   []string
	cursor  int
	done    bool
}

func newSingleSelect(title string, options, descs []string, defaultIdx int) singleSelectModel {
	return singleSelectModel{title: title, options: options, descs: descs, cursor: defaultIdx}
}

func (m singleSelectModel) Init() tea.Cmd { return nil }

func (m singleSelectModel) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
	switch msg := msg.(type) {
	case tea.KeyMsg:
		switch msg.String() {
		case "up", "k":
			if m.cursor > 0 {
				m.cursor--
			}
		case "down", "j":
			if m.cursor < len(m.options)-1 {
				m.cursor++
			}
		case "enter":
			m.done = true
			return m, tea.Quit
		case "q", "ctrl+c":
			fmt.Println("Cancelled.")
			os.Exit(0)
		}
	}
	return m, nil
}

func (m singleSelectModel) View() string {
	s := titleStyle.Render(m.title) + "\n"
	s += dimStyle.Render("  (arrows to move, enter to select)") + "\n\n"
	for i, opt := range m.options {
		cursor := "  "
		if i == m.cursor {
			cursor = "> "
		}
		line := opt
		if i < len(m.descs) && m.descs[i] != "" {
			line += dimStyle.Render(" — " + m.descs[i])
		}
		style := lipgloss.NewStyle()
		if i == m.cursor {
			style = selectedStyle
		}
		s += style.Render(cursor+line) + "\n"
	}
	return s
}

// --- Yes/No model ---

type confirmModel struct {
	title string
	yes   bool
	done  bool
}

func (m confirmModel) Init() tea.Cmd { return nil }

func (m confirmModel) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
	switch msg := msg.(type) {
	case tea.KeyMsg:
		switch msg.String() {
		case "y", "Y":
			m.yes = true
			m.done = true
			return m, tea.Quit
		case "n", "N", "q", "ctrl+c":
			m.yes = false
			m.done = true
			return m, tea.Quit
		case "enter":
			m.yes = true
			m.done = true
			return m, tea.Quit
		}
	}
	return m, nil
}

func (m confirmModel) View() string {
	return titleStyle.Render(m.title) + " [Y/n] "
}

// --- Public API ---

// ResolveInteractive guides the user through package/target/version/advisor selection.
func ResolveInteractive(cat *models.Catalog, cfg map[string]interface{}, args interface{}) (*models.InstallRequest, error) {
	// 1. Package selection — sort IDs for deterministic order
	pkgIDs := make([]string, 0, len(cat.Packages))
	for id := range cat.Packages {
		pkgIDs = append(pkgIDs, id)
	}
	sort.Strings(pkgIDs)

	pkgNames := make([]string, len(pkgIDs))
	for i, id := range pkgIDs {
		pkgNames[i] = fmt.Sprintf("%s (%s)", cat.Packages[id].DisplayName, id)
	}
	defaults := make([]int, len(pkgIDs))
	for i := range defaults {
		defaults[i] = i
	}

	pkgModel := newMultiSelect("Select packages to install:", pkgNames, defaults)
	p := tea.NewProgram(pkgModel)
	finalModel, err := p.Run()
	if err != nil {
		return nil, fmt.Errorf("package selection: %w", err)
	}
	pkgResult := finalModel.(multiSelectModel)
	selectedPkgs := []string{}
	for i, id := range pkgIDs {
		if pkgResult.selected[i] {
			selectedPkgs = append(selectedPkgs, id)
		}
	}
	if len(selectedPkgs) == 0 {
		return nil, fmt.Errorf("no packages selected")
	}

	// 2. Target selection
	targetOptions := []string{"claude", "opencode"}
	targetModel := newMultiSelect("Select targets:", targetOptions, []int{0, 1})
	p = tea.NewProgram(targetModel)
	finalModel, err = p.Run()
	if err != nil {
		return nil, fmt.Errorf("target selection: %w", err)
	}
	targetResult := finalModel.(multiSelectModel)
	selectedTargets := []string{}
	for i, t := range targetOptions {
		if targetResult.selected[i] {
			selectedTargets = append(selectedTargets, t)
		}
	}
	if len(selectedTargets) == 0 {
		return nil, fmt.Errorf("no targets selected")
	}

	// 3. Version selection per package
	versions := make(map[string]string)
	for _, pkgID := range selectedPkgs {
		versionOptions := []string{"latest", "workspace"}
		versionDescs := []string{"Latest tagged release", "Current local checkout"}
		vModel := newSingleSelect(
			fmt.Sprintf("Select version for %s:", pkgID),
			versionOptions, versionDescs, 0,
		)
		p = tea.NewProgram(vModel)
		finalModel, err = p.Run()
		if err != nil {
			return nil, fmt.Errorf("version selection for %s: %w", pkgID, err)
		}
		vResult := finalModel.(singleSelectModel)
		versions[pkgID] = versionOptions[vResult.cursor]
	}

	// 4. Advisor configuration
	var advisorCfg *models.AdvisorConfig
	advisorConfirm := confirmModel{title: "Enable Advisor Strategy? (larger model for strategic guidance)"}
	p = tea.NewProgram(advisorConfirm)
	finalModel, err = p.Run()
	if err != nil {
		return nil, fmt.Errorf("advisor confirmation: %w", err)
	}
	if finalModel.(confirmModel).yes {
		// Model picker
		modelNames := make([]string, len(AdvisorModels))
		modelDescs := make([]string, len(AdvisorModels))
		for i, m := range AdvisorModels {
			modelNames[i] = fmt.Sprintf("%s (%s)", m.DisplayName, m.Provider)
			modelDescs[i] = m.Description
		}
		modelSelect := newSingleSelect("Select advisor model:", modelNames, modelDescs, 0)
		p = tea.NewProgram(modelSelect)
		finalModel, err = p.Run()
		if err != nil {
			return nil, fmt.Errorf("advisor model selection: %w", err)
		}
		selected := finalModel.(singleSelectModel)
		advisorCfg = &models.AdvisorConfig{
			Enabled: true,
			Model:   AdvisorModels[selected.cursor].ID,
			MaxUses: 3,
		}

		fmt.Printf("\n%s Advisor enabled: %s\n\n",
			selectedStyle.Render("✓"),
			selectedStyle.Render(AdvisorModels[selected.cursor].DisplayName))
	}

	return &models.InstallRequest{
		Packages:    selectedPkgs,
		Targets:     selectedTargets,
		Versions:    versions,
		Interactive: true,
		Advisor:     advisorCfg,
	}, nil
}

// ConfirmPlan shows the install plan and asks for confirmation.
func ConfirmPlan(req *models.InstallRequest, cat *models.Catalog) bool {
	fmt.Println(titleStyle.Render("\nInstall plan:"))
	targets := strings.Join(req.Targets, ", ")
	for _, pkgID := range req.Packages {
		version := req.Versions[pkgID]
		fmt.Printf("  %s -> %s -> %s\n", pkgID, version, targets)
	}
	if req.Advisor != nil && req.Advisor.Enabled {
		fmt.Printf("  advisor -> %s (max %d calls/session)\n", req.Advisor.Model, req.Advisor.MaxUses)
	}
	fmt.Println()

	confirm := confirmModel{title: "Proceed with installation?"}
	p := tea.NewProgram(confirm)
	finalModel, err := p.Run()
	if err != nil {
		return false
	}
	return finalModel.(confirmModel).yes
}
