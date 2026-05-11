package lifecycle

import (
	"context"
	"fmt"
	"net/http"
	"os"
	"os/exec"
	"sync"
	"syscall"
	"time"
)

// Config holds server configuration
type Config struct {
	Port    int
	Timeout time.Duration
	Binary  string
}

// Server manages the opencode serve process
type Server struct {
	cfg      Config
	cmd      *exec.Cmd
	logFile  *os.File
	mu       sync.RWMutex
	running  bool
	baseURL  string
	stopOnce sync.Once
}

// NewServer creates a new Server with default config
func NewServer() *Server {
	return NewServerWithConfig(Config{
		Port:    4096,
		Timeout: 30 * time.Second,
		Binary:  "opencode",
	})
}

// NewServerWithConfig creates a new Server with provided config
func NewServerWithConfig(cfg Config) *Server {
	if cfg.Port == 0 {
		cfg.Port = 4096
	}
	if cfg.Timeout == 0 {
		cfg.Timeout = 30 * time.Second
	}
	if cfg.Binary == "" {
		cfg.Binary = "opencode"
	}

	return &Server{
		cfg:     cfg,
		baseURL: fmt.Sprintf("http://127.0.0.1:%d", cfg.Port),
	}
}

// Start launches the opencode serve process and waits for healthcheck
func (s *Server) Start(ctx context.Context) error {
	s.mu.Lock()
	defer s.mu.Unlock()

	if s.running {
		return fmt.Errorf("server is already running")
	}

	// Open log file
	logFile, err := os.OpenFile("/tmp/skynex-eval-server.log", os.O_CREATE|os.O_WRONLY|os.O_TRUNC, 0644)
	if err != nil {
		return fmt.Errorf("failed to open log file: %w", err)
	}
	s.logFile = logFile

	// Create command
	s.cmd = exec.CommandContext(
		ctx,
		s.cfg.Binary,
		"serve",
		"--port", fmt.Sprintf("%d", s.cfg.Port),
		"--hostname", "127.0.0.1",
	)

	// Redirect stdout/stderr to log file
	s.cmd.Stdout = logFile
	s.cmd.Stderr = logFile

	// Start the process
	if err := s.cmd.Start(); err != nil {
		logFile.Close()
		return fmt.Errorf("failed to start opencode serve: %w", err)
	}

	s.running = true

	// Poll healthcheck until healthy or timeout
	deadline := time.Now().Add(s.cfg.Timeout)
	ticker := time.NewTicker(500 * time.Millisecond)
	defer ticker.Stop()

	for {
		select {
		case <-ctx.Done():
			s.running = false
			_ = s.cmd.Process.Kill()
			logFile.Close()
			return ctx.Err()
		case <-ticker.C:
			healthy, err := s.IsHealthy()
			if err == nil && healthy {
				return nil
			}
			if time.Now().After(deadline) {
				s.running = false
				_ = s.cmd.Process.Kill()
				logFile.Close()
				return fmt.Errorf("healthcheck timeout after %v", s.cfg.Timeout)
			}
		}
	}
}

// Stop sends SIGTERM to the process, waits 5s, then SIGKILL if still alive
func (s *Server) Stop() error {
	s.mu.Lock()
	defer s.mu.Unlock()

	s.stopOnce.Do(func() {
		if !s.running || s.cmd == nil || s.cmd.Process == nil {
			return
		}

		// Send SIGTERM
		_ = s.cmd.Process.Signal(syscall.SIGTERM)

		// Wait up to 5 seconds for graceful shutdown
		done := make(chan error, 1)
		go func() {
			done <- s.cmd.Wait()
		}()

		select {
		case <-done:
			// Process exited gracefully
		case <-time.After(5 * time.Second):
			// Force kill
			_ = s.cmd.Process.Kill()
			_ = s.cmd.Wait()
		}

		s.running = false
		if s.logFile != nil {
			s.logFile.Close()
		}
	})

	return nil
}

// IsHealthy checks if the server is healthy via GET /global/health
func (s *Server) IsHealthy() (bool, error) {
	s.mu.RLock()
	defer s.mu.RUnlock()

	if !s.running {
		return false, fmt.Errorf("server is not running")
	}

	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()

	req, err := http.NewRequestWithContext(ctx, http.MethodGet, s.baseURL+"/global/health", nil)
	if err != nil {
		return false, err
	}

	client := &http.Client{Timeout: 5 * time.Second}
	resp, err := client.Do(req)
	if err != nil {
		return false, err
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return false, fmt.Errorf("health check returned status %d", resp.StatusCode)
	}

	return true, nil
}

// Port returns the configured port
func (s *Server) Port() int {
	return s.cfg.Port
}

// BaseURL returns the base URL of the server
func (s *Server) BaseURL() string {
	return s.baseURL
}

// IsRunning returns whether the server is currently running
func (s *Server) IsRunning() bool {
	s.mu.RLock()
	defer s.mu.RUnlock()
	return s.running
}
