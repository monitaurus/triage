package cli

import (
	"encoding/json"
	"fmt"

	"github.com/monitaurus/triage/internal/fs"
	"github.com/monitaurus/triage/internal/naming"
	"github.com/spf13/cobra"
)

// renameCmd represents the rename command
var renameCmd = &cobra.Command{
	Use:   "rename [inbox_path] [old_filename] [title] [issuer] [recipient] [date]",
	Short: "Rename a file using the normalized Triage pattern",
	Args:  cobra.ExactArgs(6),
	RunE: func(cmd *cobra.Command, args []string) error {
		inboxPath := args[0]
		oldFilename := args[1]
		title := args[2]
		issuer := args[3]
		recipient := args[4]
		date := args[5]

		newFilename, err := naming.GenerateFilename(title, issuer, recipient, date, oldFilename)
		if err != nil {
			return fmt.Errorf("failed to generate valid filename: %w", err)
		}

		err = fs.RenameFile(inboxPath, oldFilename, newFilename)
		if err != nil {
			return fmt.Errorf("failed to rename file: %w", err)
		}

		if jsonOutput {
			result := map[string]string{
				"old_filename": oldFilename,
				"new_filename": newFilename,
				"status":       "success",
			}
			data, _ := json.Marshal(result)
			fmt.Println(string(data))
		} else {
			fmt.Printf("Successfully renamed '%s' to '%s'\n", oldFilename, newFilename)
		}

		return nil
	},
}

func init() {
	rootCmd.AddCommand(renameCmd)
}
