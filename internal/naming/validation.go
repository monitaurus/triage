package naming

import (
	"regexp"
)

const (
	// FilePattern strictly enforces the <title>-<issuer>-<recipient>-<YYYY_MM_DD>.<ext> pattern
	FilePattern = `^([a-z0-9_]+)-([a-z0-9_]+)-([a-z0-9_]+)-(\d{4}_\d{2}_\d{2})(\.[a-zA-Z0-9]+)?$`
)

var (
	fileRegex = regexp.MustCompile(FilePattern)
)

// IsValidName checks if the filename conforms to the Triage pattern
func IsValidName(filename string) bool {
	return fileRegex.MatchString(filename)
}

// ParseFileName extracts the title, issuer, recipient, date, and extension from a valid filename.
// Returns empty strings if the name is invalid.
func ParseFileName(filename string) (title, issuer, recipient, date, ext string, valid bool) {
	matches := fileRegex.FindStringSubmatch(filename)
	if len(matches) != 6 {
		return "", "", "", "", "", false
	}
	return matches[1], matches[2], matches[3], matches[4], matches[5], true
}
