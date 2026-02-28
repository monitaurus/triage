package cli

import (
	"github.com/spf13/cobra"
)

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
	return rootCmd.Execute()
}

func init() {
	// Global flag definition
	rootCmd.PersistentFlags().BoolVar(&jsonOutput, "json", false, "Output results in JSON format")
}
