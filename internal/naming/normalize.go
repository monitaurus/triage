package naming

import (
	"fmt"
	"path/filepath"
	"regexp"
	"strings"
)

var (
	// invalidCharsRegex matches anything that IS NOT a lowercase letter, number, or underscore.
	invalidCharsRegex = regexp.MustCompile(`[^a-z0-9_]+`)
)

// Normalize cleans up a metadata string (title, issuer, recipient).
// It converts to lowercase, replaces spaces/dashes with underscores, and strips invalid chars.
func Normalize(input string) string {
	s := strings.ToLower(strings.TrimSpace(input))
	// Replace spaces and dashes with underscores
	s = strings.ReplaceAll(s, " ", "_")
	s = strings.ReplaceAll(s, "-", "_")
	// Strip out any non-alphanumeric/underscore characters
	s = invalidCharsRegex.ReplaceAllString(s, "")
	return s
}

// NormalizeDate ensures the date is in YYYY_MM_DD format. It replaces '-' and '/' with '_'.
func NormalizeDate(input string) string {
	s := strings.TrimSpace(input)
	s = strings.ReplaceAll(s, "-", "_")
	s = strings.ReplaceAll(s, "/", "_")
	return s
}

// GenerateFilename normalizes the inputs and returns a valid formatted string.
// Returns an error if the date format is completely wrong or fields end up empty.
func GenerateFilename(title, issuer, recipient, date, originalFilename string) (string, error) {
	t := Normalize(title)
	i := Normalize(issuer)
	r := Normalize(recipient)
	d := NormalizeDate(date)

	if t == "" || i == "" || r == "" {
		return "", fmt.Errorf("one or more fields normalized to an empty string")
	}

	ext := strings.ToLower(filepath.Ext(originalFilename))

	newName := fmt.Sprintf("%s-%s-%s-%s%s", t, i, r, d, ext)
	if !IsValidName(newName) {
		return "", fmt.Errorf("generated name '%s' is not valid according to the pattern", newName)
	}

	return newName, nil
}
