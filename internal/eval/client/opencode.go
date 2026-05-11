package client

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"time"
)

// TokenInfo holds token usage information
type TokenInfo struct {
	Total      int `json:"total"`
	Input      int `json:"input"`
	Output     int `json:"output"`
	CacheRead  int `json:"cache_read"`
	CacheWrite int `json:"cache_write"`
}

// ResponseInfo holds metadata about a response
type ResponseInfo struct {
	Tokens     TokenInfo     `json:"tokens"`
	Cost       float64       `json:"cost"`
	Duration   time.Duration `json:"duration"`
	ModelID    string        `json:"model_id"`
	ProviderID string        `json:"provider_id"`
	Agent      string        `json:"agent"`
	Finish     string        `json:"finish"`
}

// Part represents a message part (text, tool, etc.)
type Part struct {
	Type      string          `json:"type"`
	Text      string          `json:"text,omitempty"`
	Tool      string          `json:"tool,omitempty"`
	ToolInput json.RawMessage `json:"tool_input,omitempty"`
}

// Session represents an opencode session
type Session struct {
	ID        string    `json:"id"`
	Title     string    `json:"title"`
	CreatedAt time.Time `json:"created_at"`
}

// Message represents a message in a session
type Message struct {
	Info  ResponseInfo `json:"info"`
	Parts []Part       `json:"parts"`
}

// Response represents a response from the server
type Response struct {
	Info  ResponseInfo `json:"info"`
	Parts []Part       `json:"parts"`
}

// Client wraps HTTP calls to opencode serve
type Client struct {
	baseURL    string
	httpClient *http.Client
}

// NewClient creates a new Client with default configuration
func NewClient() *Client {
	return NewClientWithBaseURL("http://127.0.0.1:4096")
}

// NewClientWithBaseURL creates a new Client with a custom base URL
func NewClientWithBaseURL(baseURL string) *Client {
	return &Client{
		baseURL: baseURL,
		httpClient: &http.Client{
			Timeout: 180 * time.Second,
		},
	}
}

// CreateSession creates a new session with the given title
func (c *Client) CreateSession(title string) (*Session, error) {
	ctx, cancel := context.WithTimeout(context.Background(), 180*time.Second)
	defer cancel()

	payload := map[string]string{"title": title}
	body, err := json.Marshal(payload)
	if err != nil {
		return nil, fmt.Errorf("failed to marshal request: %w", err)
	}

	req, err := http.NewRequestWithContext(ctx, http.MethodPost, c.baseURL+"/sessions", bytes.NewReader(body))
	if err != nil {
		return nil, fmt.Errorf("failed to create request: %w", err)
	}
	req.Header.Set("Content-Type", "application/json")

	resp, err := c.httpClient.Do(req)
	if err != nil {
		return nil, fmt.Errorf("failed to create session: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK && resp.StatusCode != http.StatusCreated {
		respBody, _ := io.ReadAll(resp.Body)
		return nil, fmt.Errorf("create session returned status %d: %s", resp.StatusCode, string(respBody))
	}

	var session Session
	if err := json.NewDecoder(resp.Body).Decode(&session); err != nil {
		return nil, fmt.Errorf("failed to unmarshal session: %w", err)
	}

	return &session, nil
}

// SendMessage sends a message to a session and receives a response
func (c *Client) SendMessage(sessionID, agent string, parts []Part) (*Response, error) {
	ctx, cancel := context.WithTimeout(context.Background(), 180*time.Second)
	defer cancel()

	payload := map[string]interface{}{
		"agent": agent,
		"parts": parts,
	}
	body, err := json.Marshal(payload)
	if err != nil {
		return nil, fmt.Errorf("failed to marshal request: %w", err)
	}

	url := fmt.Sprintf("%s/sessions/%s/messages", c.baseURL, sessionID)
	req, err := http.NewRequestWithContext(ctx, http.MethodPost, url, bytes.NewReader(body))
	if err != nil {
		return nil, fmt.Errorf("failed to create request: %w", err)
	}
	req.Header.Set("Content-Type", "application/json")

	resp, err := c.httpClient.Do(req)
	if err != nil {
		return nil, fmt.Errorf("failed to send message: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		respBody, _ := io.ReadAll(resp.Body)
		return nil, fmt.Errorf("send message returned status %d: %s", resp.StatusCode, string(respBody))
	}

	var response Response
	if err := json.NewDecoder(resp.Body).Decode(&response); err != nil {
		return nil, fmt.Errorf("failed to unmarshal response: %w", err)
	}

	return &response, nil
}

// GetMessages retrieves all messages for a session
func (c *Client) GetMessages(sessionID string) ([]Message, error) {
	ctx, cancel := context.WithTimeout(context.Background(), 180*time.Second)
	defer cancel()

	url := fmt.Sprintf("%s/sessions/%s/messages", c.baseURL, sessionID)
	req, err := http.NewRequestWithContext(ctx, http.MethodGet, url, nil)
	if err != nil {
		return nil, fmt.Errorf("failed to create request: %w", err)
	}

	resp, err := c.httpClient.Do(req)
	if err != nil {
		return nil, fmt.Errorf("failed to get messages: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		respBody, _ := io.ReadAll(resp.Body)
		return nil, fmt.Errorf("get messages returned status %d: %s", resp.StatusCode, string(respBody))
	}

	var messages []Message
	if err := json.NewDecoder(resp.Body).Decode(&messages); err != nil {
		return nil, fmt.Errorf("failed to unmarshal messages: %w", err)
	}

	return messages, nil
}

// Health checks if the server is healthy
func (c *Client) Health() (bool, error) {
	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()

	req, err := http.NewRequestWithContext(ctx, http.MethodGet, c.baseURL+"/global/health", nil)
	if err != nil {
		return false, fmt.Errorf("failed to create request: %w", err)
	}

	resp, err := c.httpClient.Do(req)
	if err != nil {
		return false, err
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return false, fmt.Errorf("health check returned status %d", resp.StatusCode)
	}

	var result map[string]bool
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return false, fmt.Errorf("failed to unmarshal health response: %w", err)
	}

	healthy, ok := result["healthy"]
	if !ok {
		return false, fmt.Errorf("health response missing 'healthy' field")
	}

	return healthy, nil
}

// ExtractText concatenates all text parts from a slice of parts
func ExtractText(parts []Part) string {
	var result string
	for _, part := range parts {
		if part.Type == "text" {
			result += part.Text
		}
	}
	return result
}
