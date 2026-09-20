// Package textextract pulls the embedded text layer out of a document.
//
// It never performs OCR: when a document has no usable text layer, Extract
// returns an *Error whose Fallback tells the caller how to proceed (read the
// file visually).
package textextract

import (
	"fmt"
	"os"
	"path/filepath"
	"strings"
	"unicode"
	"unicode/utf8"

	"github.com/ledongthuc/pdf"
)

// Error codes returned in Error.Code.
const (
	CodeNotFound          = "not_found"
	CodeUnsupportedFormat = "unsupported_format"
	CodeNoText            = "no_text"
	CodeParseError        = "parse_error"
)

// FallbackVision signals that the caller should read the file visually.
const FallbackVision = "vision"

// minTextRatio is the minimum share of letters/digits among non-space runes
// for a text layer to be considered real text rather than encoding garbage.
const minTextRatio = 0.5

// Options tunes an extraction.
type Options struct {
	// MaxChars truncates the returned text (in runes). 0 means unlimited.
	MaxChars int
	// MinChars is the minimum number of non-space runes required for the
	// document to count as having text.
	MinChars int
	// Pages limits how many pages are read. 0 means all pages.
	Pages int
}

// Result is a successful extraction.
type Result struct {
	File      string `json:"file"`
	Pages     int    `json:"pages"`
	PagesRead int    `json:"pages_read"`
	Chars     int    `json:"chars"`
	Truncated bool   `json:"truncated"`
	Text      string `json:"text"`
}

// Error describes why text could not be extracted.
type Error struct {
	Code     string
	Message  string
	Fallback string
}

func (e *Error) Error() string { return e.Message }

var imageExts = map[string]bool{
	".png": true, ".jpg": true, ".jpeg": true, ".gif": true,
	".webp": true, ".bmp": true, ".tif": true, ".tiff": true, ".heic": true,
}

// Extract returns the text layer of the file at path.
func Extract(path string, opts Options) (*Result, error) {
	stat, err := os.Stat(path)
	if err != nil {
		return nil, &Error{Code: CodeNotFound, Message: fmt.Sprintf("file not found: %s", path)}
	}
	if stat.IsDir() {
		return nil, &Error{Code: CodeUnsupportedFormat, Message: fmt.Sprintf("is a directory, not a file: %s", path)}
	}

	ext := strings.ToLower(filepath.Ext(path))
	switch {
	case ext == ".pdf":
	case imageExts[ext]:
		return nil, &Error{
			Code:     CodeUnsupportedFormat,
			Message:  fmt.Sprintf("images have no text layer and OCR is not supported: %s", ext),
			Fallback: FallbackVision,
		}
	default:
		return nil, &Error{Code: CodeUnsupportedFormat, Message: fmt.Sprintf("unsupported format: %q", ext)}
	}

	return extractPDF(path, opts)
}

func extractPDF(path string, opts Options) (res *Result, err error) {
	// The PDF parser panics on some malformed inputs.
	defer func() {
		if r := recover(); r != nil {
			res, err = nil, &Error{Code: CodeParseError, Message: fmt.Sprintf("malformed PDF: %v", r)}
		}
	}()

	f, r, openErr := pdf.Open(path)
	if openErr != nil {
		return nil, &Error{Code: CodeParseError, Message: fmt.Sprintf("cannot open PDF: %v", openErr)}
	}
	defer f.Close()

	total := r.NumPage()
	limit := total
	if opts.Pages > 0 && opts.Pages < limit {
		limit = opts.Pages
	}

	var b strings.Builder
	read := 0
	for i := 1; i <= limit; i++ {
		read++
		b.WriteString(pageText(r.Page(i)))
		b.WriteString("\n")
		// Stop early once we have more than enough text.
		if opts.MaxChars > 0 && utf8.RuneCountInString(b.String()) > opts.MaxChars {
			break
		}
	}

	text := normalize(b.String())
	if err := checkUsable(text, opts.MinChars); err != nil {
		return nil, err
	}

	truncated := false
	if opts.MaxChars > 0 {
		if runes := []rune(text); len(runes) > opts.MaxChars {
			text = string(runes[:opts.MaxChars])
			truncated = true
		} else if read < total {
			truncated = true
		}
	} else if read < total {
		truncated = true
	}

	return &Result{
		File:      filepath.Base(path),
		Pages:     total,
		PagesRead: read,
		Chars:     utf8.RuneCountInString(text),
		Truncated: truncated,
		Text:      text,
	}, nil
}

// checkUsable rejects empty, too-short, or garbled text layers.
func checkUsable(text string, minChars int) error {
	var solid, meaningful int
	for _, r := range text {
		if unicode.IsSpace(r) {
			continue
		}
		solid++
		if unicode.IsLetter(r) || unicode.IsDigit(r) {
			meaningful++
		}
	}
	if solid == 0 || solid < minChars {
		return &Error{
			Code:     CodeNoText,
			Message:  fmt.Sprintf("no extractable text (%d non-space characters, need %d)", solid, minChars),
			Fallback: FallbackVision,
		}
	}
	if float64(meaningful)/float64(solid) < minTextRatio {
		return &Error{
			Code:     CodeNoText,
			Message:  "text layer looks garbled (too few letters or digits)",
			Fallback: FallbackVision,
		}
	}
	return nil
}

// normalize trims trailing spaces per line and collapses runs of blank lines.
func normalize(s string) string {
	lines := strings.Split(strings.ReplaceAll(s, "\r\n", "\n"), "\n")
	out := make([]string, 0, len(lines))
	blank := false
	for _, l := range lines {
		l = strings.TrimRightFunc(l, unicode.IsSpace)
		if l == "" {
			if blank {
				continue
			}
			blank = true
		} else {
			blank = false
		}
		out = append(out, l)
	}
	return strings.TrimSpace(strings.Join(out, "\n"))
}
