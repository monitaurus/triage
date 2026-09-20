package cli

import (
	"encoding/json"
	"errors"
	"fmt"
	"os"

	"github.com/spf13/cobra"
)

// ExitFallback is the exit code meaning "nothing usable here, the caller should
// fall back to another method" (e.g. read the file visually).
const ExitFallback = 2

// ExitError is an error carrying a stable machine-readable code and process exit code.
type ExitError struct {
	ExitCode int
	Code     string
	Message  string
	Fallback string
}

func (e *ExitError) Error() string { return e.Message }

// ExitCodeOf returns the process exit code for an error returned by Execute.
func ExitCodeOf(err error) int {
	var ee *ExitError
	if errors.As(err, &ee) && ee.ExitCode != 0 {
		return ee.ExitCode
	}
	return 1
}

var (
	// Root flag for JSON output
	jsonOutput bool
)

// rootCmd represents the base command when called without any subcommands
var rootCmd = &cobra.Command{
	Use:   "triage",
	Short: "Triage is an agentic CLI for managing an inbox of documents",
	Long: `Triage is a CLI tool designed to be used by AI agents to manage, rename, and archive
documents within an inbox directory in a structured and deterministic way.`,
}

// Execute adds all child commands to the root command and sets flags appropriately.
// This is called by main.main(). It only needs to happen once to the rootCmd.
func Execute() error {
	rootCmd.SilenceErrors = true
	rootCmd.SilenceUsage = true

	err := rootCmd.Execute()
	if err != nil {
		if jsonOutput {
			// Print error as JSON
			result := map[string]string{
				"status": "failed",
				"error":  err.Error(),
			}
			var ee *ExitError
			if errors.As(err, &ee) {
				result["code"] = ee.Code
				if ee.Fallback != "" {
					result["fallback"] = ee.Fallback
				}
			}
			data, _ := json.MarshalIndent(result, "", "  ")
			fmt.Println(string(data))
		} else {
			fmt.Fprintln(os.Stderr, "error:", err)
		}
		return err
	}
	return nil
}

func init() {
	// Global flag definition
	rootCmd.PersistentFlags().BoolVar(&jsonOutput, "json", false, "Output results in JSON format")
}
