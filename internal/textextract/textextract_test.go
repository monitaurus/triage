package textextract

import (
	"bytes"
	"errors"
	"fmt"
	"os"
	"path/filepath"
	"strings"
	"testing"
)

// buildPDF assembles a minimal single-page-per-content PDF using Helvetica.
func buildPDF(contents ...string) []byte {
	var buf bytes.Buffer
	offsets := []int{}
	obj := func(body string) {
		offsets = append(offsets, buf.Len())
		fmt.Fprintf(&buf, "%d 0 obj\n%s\nendobj\n", len(offsets), body)
	}

	buf.WriteString("%PDF-1.4\n")
	n := len(contents)
	kids := make([]string, n)
	for i := range contents {
		kids[i] = fmt.Sprintf("%d 0 R", 4+2*i)
	}
	obj("<< /Type /Catalog /Pages 2 0 R >>")
	obj(fmt.Sprintf("<< /Type /Pages /Kids [%s] /Count %d >>", strings.Join(kids, " "), n))
	obj("<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")
	for i, c := range contents {
		obj(fmt.Sprintf("<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents %d 0 R /Resources << /Font << /F1 3 0 R >> >> >>", 5+2*i))
		obj(fmt.Sprintf("<< /Length %d >>\nstream\n%s\nendstream", len(c), c))
	}

	xref := buf.Len()
	fmt.Fprintf(&buf, "xref\n0 %d\n0000000000 65535 f \n", len(offsets)+1)
	for _, o := range offsets {
		fmt.Fprintf(&buf, "%010d 00000 n \n", o)
	}
	fmt.Fprintf(&buf, "trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF\n", len(offsets)+1, xref)
	return buf.Bytes()
}

func textPage(lines ...string) string {
	var b strings.Builder
	b.WriteString("BT /F1 12 Tf 14 TL 50 700 Td\n")
	for _, l := range lines {
		fmt.Fprintf(&b, "(%s) Tj T*\n", l)
	}
	b.WriteString("ET")
	return b.String()
}

func writeTemp(t *testing.T, name string, data []byte) string {
	t.Helper()
	p := filepath.Join(t.TempDir(), name)
	if err := os.WriteFile(p, data, 0o644); err != nil {
		t.Fatal(err)
	}
	return p
}

func wantCode(t *testing.T, err error, code, fallback string) {
	t.Helper()
	var ee *Error
	if !errors.As(err, &ee) {
		t.Fatalf("want *Error, got %v", err)
	}
	if ee.Code != code || ee.Fallback != fallback {
		t.Fatalf("got code=%q fallback=%q, want code=%q fallback=%q (%s)", ee.Code, ee.Fallback, code, fallback, ee.Message)
	}
}

func TestExtractText(t *testing.T) {
	p := writeTemp(t, "facture.pdf", buildPDF(textPage("Facture veterinaire", "Cabinet des Canuts", "Date 2026-08-17")))
	res, err := Extract(p, Options{MinChars: 20})
	if err != nil {
		t.Fatal(err)
	}
	if res.Pages != 1 || res.PagesRead != 1 || res.Truncated {
		t.Fatalf("unexpected result: %+v", res)
	}
	for _, want := range []string{"Facture veterinaire", "Cabinet des Canuts", "2026-08-17"} {
		if !strings.Contains(res.Text, want) {
			t.Errorf("text %q missing %q", res.Text, want)
		}
	}
}

func TestExtractTruncatesAndLimitsPages(t *testing.T) {
	p := writeTemp(t, "multi.pdf", buildPDF(
		textPage("Page one has some real words in it"),
		textPage("Page two has other words in it too"),
	))

	res, err := Extract(p, Options{MaxChars: 10})
	if err != nil {
		t.Fatal(err)
	}
	if !res.Truncated || res.Chars != 10 {
		t.Fatalf("want truncated to 10 chars, got %+v", res)
	}

	res, err = Extract(p, Options{Pages: 1})
	if err != nil {
		t.Fatal(err)
	}
	if res.PagesRead != 1 || res.Pages != 2 || !res.Truncated || strings.Contains(res.Text, "Page two") {
		t.Fatalf("unexpected page limiting: %+v", res)
	}
}

func TestScannedPDFHasNoText(t *testing.T) {
	// A page that only draws a rectangle: what an image-only scan looks like to a text parser.
	p := writeTemp(t, "scan.pdf", buildPDF("0 0 200 200 re f"))
	_, err := Extract(p, Options{MinChars: 50})
	wantCode(t, err, CodeNoText, FallbackVision)
}

func TestShortTextBelowMinimum(t *testing.T) {
	p := writeTemp(t, "short.pdf", buildPDF(textPage("Hi")))
	_, err := Extract(p, Options{MinChars: 50})
	wantCode(t, err, CodeNoText, FallbackVision)
}

func TestGarbledText(t *testing.T) {
	p := writeTemp(t, "garbled.pdf", buildPDF(textPage("#$%&*+=<>~^|#$%&*+=<>~^|#$%&*+=<>~^|#$%&*+=<>~^|")))
	_, err := Extract(p, Options{MinChars: 10})
	wantCode(t, err, CodeNoText, FallbackVision)
}

func TestImagesFallBackToVision(t *testing.T) {
	p := writeTemp(t, "scan.PNG", []byte("not really a png"))
	_, err := Extract(p, Options{})
	wantCode(t, err, CodeUnsupportedFormat, FallbackVision)
}

func TestUnsupportedFormat(t *testing.T) {
	p := writeTemp(t, "doc.docx", []byte("x"))
	_, err := Extract(p, Options{})
	wantCode(t, err, CodeUnsupportedFormat, "")
}

func TestNotFound(t *testing.T) {
	_, err := Extract(filepath.Join(t.TempDir(), "missing.pdf"), Options{})
	wantCode(t, err, CodeNotFound, "")
}

func TestCorruptPDF(t *testing.T) {
	p := writeTemp(t, "bad.pdf", []byte("%PDF-1.4 this is not a pdf"))
	_, err := Extract(p, Options{})
	wantCode(t, err, CodeParseError, "")
}

func TestSpacingAndLinesFromGeometry(t *testing.T) {
	content := "BT /F1 12 Tf 50 700 Td\n" +
		"[(Hello) -300 (World)] TJ\n" + // big TJ gap = word space
		"[(W) 80 (orld)] TJ\n" + // small kerning = no space (same spot, joins previous run)
		"0 -20 Td (Second) Tj\n" + // new line
		"60 0 Td (line) Tj\n" + // same line, moved right = new word
		"ET"
	p := writeTemp(t, "layout.pdf", buildPDF(content))
	res, err := Extract(p, Options{MinChars: 5})
	if err != nil {
		t.Fatal(err)
	}
	want := "Hello WorldWorld\nSecond line"
	if res.Text != want {
		t.Fatalf("got %q, want %q", res.Text, want)
	}
}

func TestReadingOrderIsTopToBottom(t *testing.T) {
	// Text drawn bottom-first in the stream must still come out top-first.
	content := "BT /F1 12 Tf 50 100 Td (bottom line here) Tj ET\n" +
		"BT /F1 12 Tf 50 700 Td (top line here) Tj ET"
	p := writeTemp(t, "order.pdf", buildPDF(content))
	res, err := Extract(p, Options{MinChars: 5})
	if err != nil {
		t.Fatal(err)
	}
	if want := "top line here\nbottom line here"; res.Text != want {
		t.Fatalf("got %q, want %q", res.Text, want)
	}
}
