package cli

import (
	"encoding/json"
	"fmt"
	"path/filepath"

	"github.com/monitaurus/triage/internal/indexer"
	"github.com/spf13/cobra"
)

// indexCmd represents the index command
var indexCmd = &cobra.Command{
	Use:   "index [archive_path]",
	Short: "Build an index of issuers and recipients from the archive",
	Args:  cobra.ExactArgs(1),
	RunE: func(cmd *cobra.Command, args []string) error {
		archivePath := args[0]

		absArchive, err := filepath.Abs(archivePath)
		if err != nil {
			return err
		}

		indexData, err := indexer.BuildIndex(absArchive)
		if err != nil {
			return fmt.Errorf("failed to build index: %w", err)
		}

		if jsonOutput {
			data, err := json.MarshalIndent(indexData, "", "  ")
			if err != nil {
				return err
			}
			fmt.Println(string(data))
		} else {
			fmt.Printf("Found %d unique issuers.\n", len(indexData.Issuers))
			for _, i := range indexData.Issuers {
				fmt.Printf(" - %s\n", i)
			}
			fmt.Println()
			fmt.Printf("Found %d unique recipients.\n", len(indexData.Recipients))
			for _, r := range indexData.Recipients {
				fmt.Printf(" - %s\n", r)
			}
		}

		return nil
	},
}

func init() {
	rootCmd.AddCommand(indexCmd)
}
