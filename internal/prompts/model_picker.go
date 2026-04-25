package prompts

import (
	"fmt"

	tea "github.com/charmbracelet/bubbletea"
)

// --- Provider Selector ---

type providerSelector struct {
	providers []string
	cursor    int
	allModels map[string][]string
	done      bool
}

func newProviderSelector(allModels map[string][]string) providerSelector {
	providers := make([]string, 0, len(allModels))
	for p := range allModels {
		providers = append(providers, p)
	}
	// Sort providers for deterministic order
	if len(providers) > 0 {
		for i := 0; i < len(providers)-1; i++ {
			for j := i + 1; j < len(providers); j++ {
				if providers[i] > providers[j] {
					providers[i], providers[j] = providers[j], providers[i]
				}
			}
		}
	}
	return providerSelector{
		providers: providers,
		cursor:    0,
		allModels: allModels,
	}
}

func (m providerSelector) Init() tea.Cmd { return nil }

func (m providerSelector) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
	switch msg := msg.(type) {
	case tea.KeyMsg:
		switch msg.String() {
		case "up", "k":
			if m.cursor > 0 {
				m.cursor--
			}
		case "down", "j":
			if m.cursor < len(m.providers)-1 {
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

func (m providerSelector) View() string {
	s := titleStyle.Render("Pick model for: (provider)") + "\n"
	s += dimStyle.Render("──────────────────────────────") + "\n\n"
	s += dimStyle.Render("Provider:") + "\n"

	for i, provider := range m.providers {
		cursor := "  "
		if i == m.cursor {
			cursor = "> "
		}
		count := len(m.allModels[provider])
		line := fmt.Sprintf("%s%s (%d model%s)", cursor, provider, count, map[bool]string{true: "s", false: ""}[count != 1])
		style := dimStyle
		if i == m.cursor {
			style = selectedStyle
		}
		s += style.Render(line) + "\n"
	}
	s += "\n" + dimStyle.Render("[enter] Select provider   [esc] Back") + "\n"
	return s
}

// --- Model Selector (per provider) ---

type modelSelector struct {
	provider string
	models   []string
	cursor   int
	done     bool
}

func newModelSelector(provider string, models []string) modelSelector {
	return modelSelector{
		provider: provider,
		models:   models,
		cursor:   0,
	}
}

func (m modelSelector) Init() tea.Cmd { return nil }

func (m modelSelector) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
	switch msg := msg.(type) {
	case tea.KeyMsg:
		switch msg.String() {
		case "up", "k":
			if m.cursor > 0 {
				m.cursor--
			}
		case "down", "j":
			if m.cursor < len(m.models)-1 {
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

func (m modelSelector) View() string {
	s := titleStyle.Render(fmt.Sprintf("Pick model for: %s / %s", "(agent)", m.provider)) + "\n"
	s += dimStyle.Render("──────────────────────────────") + "\n\n"

	for i, model := range m.models {
		cursor := "  "
		if i == m.cursor {
			cursor = "> "
		}
		style := dimStyle
		if i == m.cursor {
			style = selectedStyle
		}
		s += style.Render(fmt.Sprintf("%s%s\n", cursor, model))
	}

	s += "\n" + dimStyle.Render("[enter] Select   [esc] Back to providers") + "\n"
	return s
}

// RunModelPicker displays the hierarchical model picker: providers → models.
// Takes the context string (agent or group name) and all available models.
// Returns the full model ID (provider/model) or empty string if cancelled.
func RunModelPicker(context string, allModels map[string][]string) (string, error) {
	if len(allModels) == 0 {
		return "", fmt.Errorf("no models available")
	}

	// 1. Provider selection
	providerModel := newProviderSelector(allModels)
	p := tea.NewProgram(providerModel)
	finalModel, err := p.Run()
	if err != nil {
		return "", fmt.Errorf("provider selection: %w", err)
	}
	providerResult := finalModel.(providerSelector)
	if !providerResult.done || providerResult.cursor >= len(providerResult.providers) {
		return "", nil // Cancelled
	}
	selectedProvider := providerResult.providers[providerResult.cursor]

	// 2. Model selection
	models := allModels[selectedProvider]
	modelModel := newModelSelector(selectedProvider, models)
	p = tea.NewProgram(modelModel)
	finalModel, err = p.Run()
	if err != nil {
		return "", fmt.Errorf("model selection: %w", err)
	}
	modelResult := finalModel.(modelSelector)
	if !modelResult.done || modelResult.cursor >= len(modelResult.models) {
		return "", nil // Cancelled
	}
	return modelResult.models[modelResult.cursor], nil
}
