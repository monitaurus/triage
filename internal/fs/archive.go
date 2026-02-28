package fs

import (
	"fmt"
	"os"
	"path/filepath"
	"strconv"
	"strings"

	"github.com/monitaurus/triage/internal/naming"
)

// ArchiveResult holds the status of a single archiving operation
type ArchiveResult struct {
	Filename string `json:"filename"`
	From     string `json:"from"`
	To       string `json:"to"`
	Status   string `json:"status"`
	Error    string `json:"error,omitempty"`
}

// ArchiveFile moves a file from inbox to the archive_path/<YYYY>/ directory.
func ArchiveFile(inboxPath, archivePath, filename string) ArchiveResult {
	res := ArchiveResult{
		Filename: filename,
		From:     filepath.Join(inboxPath, filename),
		Status:   "failed",
	}

	_, _, _, date, _, valid := naming.ParseFileName(filename)
	if !valid {
		res.Error = "invalid file name pattern"
		return res
	}

	// Extract Year from YYYY_MM_DD
	parts := strings.Split(date, "_")
	if len(parts) != 3 {
		res.Error = "invalid date format"
		return res
	}

	yearStr := parts[0]
	if _, err := strconv.Atoi(yearStr); err != nil {
		res.Error = "year is not a valid number"
		return res
	}

	yearDir := filepath.Join(archivePath, yearStr)
	if err := os.MkdirAll(yearDir, os.ModePerm); err != nil {
		res.Error = fmt.Sprintf("failed to create year directory: %s", err.Error())
		return res
	}

	toPath := filepath.Join(yearDir, filename)
	res.To = toPath

	if _, err := os.Stat(toPath); err == nil {
		res.Error = "file already exists in archive"
		return res
	}

	if err := os.Rename(res.From, toPath); err != nil {
		res.Error = fmt.Sprintf("failed to move file: %s", err.Error())
		return res
	}

	res.Status = "success"
	return res
}

// ArchiveInbox archives all valid files in the inbox.
func ArchiveInbox(inboxPath, archivePath string) []ArchiveResult {
	var results []ArchiveResult

	files, err := ListInbox(inboxPath)
	if err != nil {
		// return a single error result instead of failing silently or crashing
		return []ArchiveResult{{Status: "failed", Error: fmt.Sprintf("failed to list inbox: %s", err.Error())}}
	}

	for _, f := range files {
		if f.IsValid {
			res := ArchiveFile(inboxPath, archivePath, f.Name)
			results = append(results, res)
		}
	}

	return results
}
