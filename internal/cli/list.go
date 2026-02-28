package cli

import (
	"encoding/json"
	"fmt"

	"github.com/monitaurus/triage/internal/fs"
	"github.com/spf13/cobra"
)

// listCmd represents the list command
var listCmd = &cobra.Command{
	Use:   "list [inbox_path]",
	Short: "List files in the specified inbox folder",
	Args:  cobra.ExactArgs(1),
	RunE: func(cmd *cobra.Command, args []string) error {
		inboxPath := args[0]

		files, err := fs.ListInbox(inboxPath)
		if err != nil {
			return fmt.Errorf("failed to list inbox: %w", err)
		}

		if jsonOutput {
			data, err := json.MarshalIndent(files, "", "  ")
			if err != nil {
				return err
			}
			fmt.Println(string(data))
		} else {
			for _, file := range files {
				status := "❌"
				if file.IsValid {
					status = "✅"
				}
				fmt.Printf("%s %s (Size: %d bytes)\n", status, file.Name, file.Size)
			}
		}

		return nil
	},
}

func init() {
	rootCmd.AddCommand(listCmd)
}
