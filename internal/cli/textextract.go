package cli

import (
	"encoding/json"
	"errors"
	"fmt"

	"github.com/monitaurus/triage/internal/textextract"
	"github.com/spf13/cobra"
)

var (
	textExtractMaxChars int
	textExtractMinChars int
	textExtractPages    int
)

// textExtractCmd represents the text-extract command
var textExtractCmd = &cobra.Command{
	Use:   "text-extract [file_path]",
	Short: "Extract the text layer of a document, or fail so the caller can read it visually",
	Long: `Extract the embedded text of a PDF. No OCR and no LLM is involved.

On success the text is printed (or a JSON object with --json) and the exit code is 0.

If the document has no usable text (scanned PDF, image, garbled text layer) the command
fails with exit code 2 and, with --json, {"code": "...", "fallback": "vision"}: the caller
should then read the file visually itself. Any other failure exits with code 1.`,
	Args: cobra.ExactArgs(1),
	RunE: func(cmd *cobra.Command, args []string) error {
		res, err := textextract.Extract(args[0], textextract.Options{
			MaxChars: textExtractMaxChars,
			MinChars: textExtractMinChars,
			Pages:    textExtractPages,
		})
		if err != nil {
			var te *textextract.Error
			if errors.As(err, &te) {
				exit := 1
				if te.Fallback != "" {
					exit = ExitFallback
				}
				return &ExitError{ExitCode: exit, Code: te.Code, Message: te.Message, Fallback: te.Fallback}
			}
			return err
		}

		if jsonOutput {
			out := struct {
				Status string `json:"status"`
				*textextract.Result
			}{"success", res}
			data, err := json.MarshalIndent(out, "", "  ")
			if err != nil {
				return err
			}
			fmt.Println(string(data))
		} else {
			fmt.Println(res.Text)
		}
		return nil
	},
}

func init() {
	textExtractCmd.Flags().IntVar(&textExtractMaxChars, "max-chars", 3000, "Truncate the text to this many characters (0 = unlimited)")
	textExtractCmd.Flags().IntVar(&textExtractMinChars, "min-chars", 50, "Minimum non-space characters required to count as text")
	textExtractCmd.Flags().IntVar(&textExtractPages, "pages", 0, "Only read the first N pages (0 = all)")
	rootCmd.AddCommand(textExtractCmd)
}
