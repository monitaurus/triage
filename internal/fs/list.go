package fs

import (
	"os"
	"path/filepath"

	"github.com/monitaurus/triage/internal/naming"
)

// FileInfo holds metadata about a file in the inbox
type FileInfo struct {
	Name    string `json:"name"`
	Path    string `json:"path"`
	Size    int64  `json:"size"`
	IsValid bool   `json:"is_valid"`
}

// ListInbox scans the specified directory and returns basic info for all files.
// Ignores directories and the .triage-index.json file.
func ListInbox(dirPath string) ([]FileInfo, error) {
	var files []FileInfo

	entries, err := os.ReadDir(dirPath)
	if err != nil {
		return nil, err
	}

	for _, entry := range entries {
		if entry.IsDir() || entry.Name() == ".triage-index.json" {
			continue
		}

		info, err := entry.Info()
		if err != nil {
			continue // Skip files we can't read info for
		}

		fInfo := FileInfo{
			Name:    entry.Name(),
			Path:    filepath.Join(dirPath, entry.Name()),
			Size:    info.Size(),
			IsValid: naming.IsValidName(entry.Name()),
		}

		files = append(files, fInfo)
	}

	return files, nil
}
