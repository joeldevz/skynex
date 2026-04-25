package prompts

import (
	"fmt"
	"os/exec"
	"regexp"
	"strings"

	"github.com/charmbracelet/bubbles/textinput"
	tea "github.com/charmbracelet/bubbletea"
	"github.com/charmbracelet/lipgloss"
)

var (
	errorStyle  = lipgloss.NewStyle().Foreground(lipgloss.Color("196"))
	subtleStyle = lipgloss.NewStyle().Foreground(lipgloss.Color("241"))
	activeStyle = lipgloss.NewStyle().Foreground(lipgloss.Color("212")).Bold(true)
	groupStyle  = lipgloss.NewStyle().Bold(true).Foreground(lipgloss.Color("39"))
)

// --- Profile Name Form ---

type profileNameForm struct {
	textInput textinput.Model
	err       string
}

func newProfileNameForm(initial string) profileNameForm {
	ti := textinput.New()
	ti.Placeholder = "backend"
	ti.SetValue(initial)
	ti.Focus()
	ti.CharLimit = 100
	return profileNameForm{textInput: ti}
}

func (m profileNameForm) Init() tea.Cmd {
	return textinput.Blink
}

func (m profileNameForm) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
	switch msg := msg.(type) {
	case tea.KeyMsg:
		switch msg.String() {
		case "enter":
			name := m.textInput.Value()
			if err := validateProfileName(name); err != nil {
				m.err = err.Error()
				return m, nil
			}
			return m, tea.Quit
		case "esc":
			return m, tea.Quit
		}
	}
	var cmd tea.Cmd
	m.textInput, cmd = m.textInput.Update(msg)
	m.err = ""
	if name := m.textInput.Value(); name != "" {
		if err := validateProfileName(name); err != nil {
			m.err = err.Error()
		}
	}
	return m, cmd
}

func (m profileNameForm) View() string {
	s := titleStyle.Render("Create Profile") + "\n"
	s += dimStyle.Render("──────────────────────────────") + "\n\n"
	s += fmt.Sprintf("Profile name: %s\n\n", m.textInput.View())
	if m.err != "" {
		s += errorStyle.Render("✗ "+m.err) + "\n\n"
	}
	s += dimStyle.Render("(enter to confirm, esc to cancel)") + "\n"
	s += dimStyle.Render("Hint: lowercase, hyphens ok (e.g. backend, front-v2)") + "\n"
	return s
}

func validateProfileName(name string) error {
	name = strings.TrimSpace(name)
	if name == "" {
		return fmt.Errorf("name cannot be empty")
	}
	if !regexp.MustCompile(`^[a-z0-9]([a-z0-9-]*[a-z0-9])?$`).MatchString(name) {
		return fmt.Errorf("lowercase, hyphens ok (e.g. backend, front-v2)")
	}
	return nil
}

// RunProfileNameForm displays the profile name form and returns the name or error on cancel.
func RunProfileNameForm(initial string) (string, error) {
	m := newProfileNameForm(initial)
	p := tea.NewProgram(m)
	finalModel, err := p.Run()
	if err != nil {
		return "", fmt.Errorf("profile form: %w", err)
	}
	result := finalModel.(profileNameForm)
	name := result.textInput.Value()
	if name == "" {
		return "", fmt.Errorf("cancelled")
	}
	return name, nil
}

// --- Mode Selector ---

type ConfigMode int

const (
	ModeSimple ConfigMode = iota
	ModeAdvanced
)

type modeSelector struct {
	cursor int
	modes  []string
	done   bool
}

func newModeSelector() modeSelector {
	return modeSelector{
		cursor: 0,
		modes:  []string{"Simple", "Advanced"},
	}
}

func (m modeSelector) Init() tea.Cmd { return nil }

func (m modeSelector) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
	switch msg := msg.(type) {
	case tea.KeyMsg:
		switch msg.String() {
		case "up", "k":
			if m.cursor > 0 {
				m.cursor--
			}
		case "down", "j":
			if m.cursor < len(m.modes)-1 {
				m.cursor++
			}
		case "enter":
			m.done = true
			return m, tea.Quit
		case "esc":
			return m, tea.Quit
		}
	}
	return m, nil
}

func (m modeSelector) View() string {
	s := titleStyle.Render("Configure Models") + "\n"
	s += dimStyle.Render("──────────────────────────────") + "\n\n"

	descs := []string{
		"Set model by role (orchestrator, workers, advisor)",
		"Set model per agent individually",
	}

	for i, mode := range m.modes {
		cursor := "  "
		if i == m.cursor {
			cursor = "> "
		}
		indicator := "○"
		style := dimStyle
		if i == m.cursor {
			indicator = "●"
			style = selectedStyle
		}
		line := fmt.Sprintf("%s%s %-10s", cursor, indicator, mode)
		if i < len(descs) {
			line += dimStyle.Render(" — " + descs[i])
		}
		s += style.Render(line) + "\n"
	}
	s += "\n" + dimStyle.Render("(↑↓ to move, enter to select, esc to go back)") + "\n"
	return s
}

// RunModeSelector displays the mode selector and returns the selected mode.
func RunModeSelector() (ConfigMode, error) {
	m := newModeSelector()
	p := tea.NewProgram(m)
	finalModel, err := p.Run()
	if err != nil {
		return ModeSimple, fmt.Errorf("mode selector: %w", err)
	}
	result := finalModel.(modeSelector)
	if result.cursor == 1 {
		return ModeAdvanced, nil
	}
	return ModeSimple, nil
}

// --- Simple Model Picker ---

type simpleModelPicker struct {
	groups    []string          // ["Orchestrator & Manager", "Workers", "Advisor"]
	models    map[string]string // group -> full model ID
	cursor    int
	allModels map[string][]string // provider -> []modelID from opencode models
	done      bool
}

func newSimpleModelPicker(initial map[string]string) simpleModelPicker {
	allModels, _ := LoadOpencodeModels()
	return simpleModelPicker{
		groups: []string{
			"Orchestrator & Manager",
			"Workers (planners, coder, verifier...)",
			"Advisor",
		},
		models:    initial,
		cursor:    0,
		allModels: allModels,
	}
}

func (m simpleModelPicker) Init() tea.Cmd { return nil }

func (m simpleModelPicker) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
	switch msg := msg.(type) {
	case tea.KeyMsg:
		switch msg.String() {
		case "up", "k":
			if m.cursor > 0 {
				m.cursor--
			}
		case "down", "j":
			if m.cursor < len(m.groups)-1 {
				m.cursor++
			}
		case "enter":
			// Open model picker for this group
			groupIdx := m.cursor
			modelID, err := RunModelPicker(m.groups[groupIdx], m.allModels)
			if err != nil {
				return m, nil
			}
			if modelID != "" {
				m.models[m.groups[groupIdx]] = modelID
			}
			return m, nil
		case "s":
			// Set all to same model
			modelID, err := RunModelPicker("All Groups", m.allModels)
			if err != nil {
				return m, nil
			}
			if modelID != "" {
				for _, group := range m.groups {
					m.models[group] = modelID
				}
			}
			return m, nil
		case "esc":
			return m, tea.Quit
		}
	}
	return m, nil
}

func (m simpleModelPicker) View() string {
	s := titleStyle.Render("Simple Model Setup") + "\n"
	s += dimStyle.Render("──────────────────────────────") + "\n\n"

	for i, group := range m.groups {
		cursor := "  "
		if i == m.cursor {
			cursor = "> "
		}
		modelID := m.models[group]
		if modelID == "" {
			modelID = "(not set)"
		}
		style := dimStyle
		if i == m.cursor {
			style = selectedStyle
		}
		s += style.Render(fmt.Sprintf("%s%s\n", cursor, group)) + "\n"
		s += dimStyle.Render(fmt.Sprintf("  %s", modelID)) + "\n\n"
	}

	s += "\n" + dimStyle.Render("[s] Set all to same model   [enter] Confirm   [esc] Back") + "\n"
	return s
}

// --- Advanced Model Picker ---

type agentConfig struct {
	name  string
	model string
}

type advancedModelPicker struct {
	agents    []agentConfig
	cursor    int
	allModels map[string][]string
	done      bool
}

var agentList = []string{
	"orchestrator",
	"tech-planner",
	"product-planner",
	"coder",
	"manager",
	"verifier",
	"test-reviewer",
	"security",
	"skill-validator",
	"advisor",
}

func newAdvancedModelPicker(initial map[string]string) advancedModelPicker {
	allModels, _ := LoadOpencodeModels()
	agents := make([]agentConfig, len(agentList))
	for i, name := range agentList {
		model := initial[name]
		if model == "" {
			model = "(not set)"
		}
		agents[i] = agentConfig{name: name, model: model}
	}
	return advancedModelPicker{
		agents:    agents,
		cursor:    0,
		allModels: allModels,
	}
}

func (m advancedModelPicker) Init() tea.Cmd { return nil }

func (m advancedModelPicker) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
	switch msg := msg.(type) {
	case tea.KeyMsg:
		switch msg.String() {
		case "up", "k":
			if m.cursor > 0 {
				m.cursor--
			}
		case "down", "j":
			if m.cursor < len(m.agents)-1 {
				m.cursor++
			}
		case "enter":
			agentName := m.agents[m.cursor].name
			modelID, err := RunModelPicker(agentName, m.allModels)
			if err != nil {
				return m, nil
			}
			if modelID != "" {
				m.agents[m.cursor].model = modelID
			}
			return m, nil
		case "s":
			modelID, err := RunModelPicker("All Agents", m.allModels)
			if err != nil {
				return m, nil
			}
			if modelID != "" {
				for i := range m.agents {
					m.agents[i].model = modelID
				}
			}
			return m, nil
		case "esc":
			return m, tea.Quit
		}
	}
	return m, nil
}

func (m advancedModelPicker) View() string {
	s := titleStyle.Render("Advanced Model Setup") + "\n"
	s += dimStyle.Render("──────────────────────────────") + "\n\n"

	for i, ac := range m.agents {
		cursor := "  "
		if i == m.cursor {
			cursor = "> "
		}
		style := dimStyle
		if i == m.cursor {
			style = selectedStyle
		}
		s += style.Render(fmt.Sprintf("%s%-20s %s\n", cursor, ac.name, ac.model))
	}

	s += "\n" + dimStyle.Render("[enter] Pick model   [s] Set all   [esc] Back") + "\n"
	return s
}

// RunSimpleModelPicker runs the simple mode picker.
func RunSimpleModelPicker(initial map[string]string) (map[string]string, error) {
	m := newSimpleModelPicker(initial)
	p := tea.NewProgram(m)
	finalModel, err := p.Run()
	if err != nil {
		return nil, fmt.Errorf("simple model picker: %w", err)
	}
	result := finalModel.(simpleModelPicker)
	return result.models, nil
}

// RunAdvancedModelPicker runs the advanced mode picker.
func RunAdvancedModelPicker(initial map[string]string) (map[string]string, error) {
	m := newAdvancedModelPicker(initial)
	p := tea.NewProgram(m)
	finalModel, err := p.Run()
	if err != nil {
		return nil, fmt.Errorf("advanced model picker: %w", err)
	}
	result := finalModel.(advancedModelPicker)
	models := make(map[string]string)
	for _, ac := range result.agents {
		if ac.model != "(not set)" {
			models[ac.name] = ac.model
		}
	}
	return models, nil
}

// --- Main Flow ---

type ProfileResult struct {
	Name   string
	Models map[string]string // agentName -> modelID
}

// RunProfileCreationFlow runs the complete flow: name → mode → models.
func RunProfileCreationFlow(initialModels map[string]string) (*ProfileResult, error) {
	// 1. Profile name
	name, err := RunProfileNameForm("")
	if err != nil {
		return nil, err
	}

	// 2. Mode selector
	mode, err := RunModeSelector()
	if err != nil {
		return nil, err
	}

	// 3. Model picker based on mode
	var models map[string]string
	if mode == ModeSimple {
		models, err = RunSimpleModelPicker(initialModels)
	} else {
		models, err = RunAdvancedModelPicker(initialModels)
	}
	if err != nil {
		return nil, err
	}

	return &ProfileResult{
		Name:   name,
		Models: models,
	}, nil
}

// LoadOpencodeModels executes "opencode models" and parses the output.
// Returns map[provider][]modelID.
func LoadOpencodeModels() (map[string][]string, error) {
	out, err := exec.Command("opencode", "models").Output()
	if err != nil {
		// If opencode is not available, return a sensible default set
		return defaultModels(), nil
	}
	result := make(map[string][]string)
	for _, line := range strings.Split(string(out), "\n") {
		line = strings.TrimSpace(line)
		if line == "" {
			continue
		}
		parts := strings.SplitN(line, "/", 2)
		if len(parts) == 2 {
			provider := parts[0]
			result[provider] = append(result[provider], line) // full ID
		}
	}
	if len(result) == 0 {
		return defaultModels(), nil
	}
	return result, nil
}

// defaultModels returns a fallback set of models if opencode is unavailable.
func defaultModels() map[string][]string {
	return map[string][]string{
		"anthropic": {
			"anthropic/claude-opus-4-6",
			"anthropic/claude-sonnet-4-6",
			"anthropic/claude-haiku-4-5",
		},
		"openai": {
			"openai/gpt-4o",
			"openai/o1",
		},
		"google": {
			"google/gemini-2-pro",
		},
	}
}
