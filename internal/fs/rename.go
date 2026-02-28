package fs

import (
	"fmt"
	"os"
	"path/filepath"
)

// RenameFile atomically renames a file within the same directory.
func RenameFile(dirPath, oldFilename, newFilename string) error {
	oldPath := filepath.Join(dirPath, oldFilename)
	newPath := filepath.Join(dirPath, newFilename)

	if _, err := os.Stat(oldPath); os.IsNotExist(err) {
		return fmt.Errorf("source file does not exist: %s", oldPath)
	}

	if _, err := os.Stat(newPath); err == nil {
		return fmt.Errorf("destination file already exists: %s", newPath)
	}

	return os.Rename(oldPath, newPath)
}
