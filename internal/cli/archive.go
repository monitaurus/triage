package cli

import (
	"encoding/json"
	"fmt"
	"path/filepath"

	"github.com/monitaurus/triage/internal/fs"
	"github.com/spf13/cobra"
)

var (
	targetFile string
)

// archiveCmd represents the archive command
var archiveCmd = &cobra.Command{
	Use:   "archive [inbox_path] [archive_path]",
	Short: "Archive properly named files from the inbox to the archive",
	Args:  cobra.ExactArgs(2),
	RunE: func(cmd *cobra.Command, args []string) error {
		inboxPath := args[0]
		archivePath := args[1]

		// create absolute paths to avoid weird relativism issues
		absInbox, err := filepath.Abs(inboxPath)
		if err != nil {
			return err
		}
		absArchive, err := filepath.Abs(archivePath)
		if err != nil {
			return err
		}

		var results []fs.ArchiveResult

		if targetFile != "" {
			res := fs.ArchiveFile(absInbox, absArchive, targetFile)
			results = append(results, res)
		} else {
			results = fs.ArchiveInbox(absInbox, absArchive)
		}

		if jsonOutput {
			data, err := json.MarshalIndent(results, "", "  ")
			if err != nil {
				return err
			}
			fmt.Println(string(data))
		} else {
			for _, res := range results {
				if res.Status == "success" {
					fmt.Printf("✅ Archived: %s -> %s\n", res.Filename, res.To)
				} else {
					fmt.Printf("❌ Failed: %s (%s)\n", res.Filename, res.Error)
				}
			}
		}

		return nil
	},
}

func init() {
	archiveCmd.Flags().StringVar(&targetFile, "file", "", "Target a specific file to archive")
	rootCmd.AddCommand(archiveCmd)
}
