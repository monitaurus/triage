package indexer

import (
	"os"
	"path/filepath"

	"github.com/monitaurus/triage/internal/naming"
)

// IndexData holds the distinct lists of issuers and recipients.
type IndexData struct {
	Issuers    []string `json:"issuers"`
	Recipients []string `json:"recipients"`
}

// BuildIndex scans the given directory recursively for files that match the Triage naming pattern.
// It extracts and deduplicates all 'issuers' and 'recipients' found.
func BuildIndex(dirPath string) (IndexData, error) {
	issuersMap := make(map[string]bool)
	recipientsMap := make(map[string]bool)

	err := filepath.WalkDir(dirPath, func(path string, d os.DirEntry, err error) error {
		if err != nil {
			return err
		}
		if !d.IsDir() {
			_, issuer, recipient, _, _, valid := naming.ParseFileName(d.Name())
			if valid {
				issuersMap[issuer] = true
				recipientsMap[recipient] = true
			}
		}
		return nil
	})

	if err != nil {
		return IndexData{}, err
	}

	var issuers []string
	for i := range issuersMap {
		issuers = append(issuers, i)
	}

	var recipients []string
	for r := range recipientsMap {
		recipients = append(recipients, r)
	}

	return IndexData{
		Issuers:    issuers,
		Recipients: recipients,
	}, nil
}
