package textextract

import (
	"math"
	"sort"
	"strings"
	"unicode/utf8"

	"github.com/ledongthuc/pdf"
)

// The upstream Page.GetPlainText ignores TJ kerning offsets and Td/Tm moves, so
// words fuse together and lines vanish. pageText walks the content stream
// itself, tracking text positions, and rebuilds lines and spaces from geometry.

// tjSpaceThreshold is the TJ adjustment, in thousandths of an em, above which
// a gap is treated as a word space (kerning inside words is much smaller).
const tjSpaceThreshold = 180

// matrix is a PDF affine matrix [a b c d e f].
type matrix [6]float64

var identity = matrix{1, 0, 0, 1, 0, 0}

// mul returns m followed by n (the PDF "m × n" order).
func (m matrix) mul(n matrix) matrix {
	return matrix{
		m[0]*n[0] + m[1]*n[2], m[0]*n[1] + m[1]*n[3],
		m[2]*n[0] + m[3]*n[2], m[2]*n[1] + m[3]*n[3],
		m[4]*n[0] + m[5]*n[2] + n[4], m[4]*n[1] + m[5]*n[3] + n[5],
	}
}

// chunk is a piece of text shown at one position.
type chunk struct {
	x, y, size float64
	text       string
}

func pageText(p pdf.Page) string {
	if p.V.IsNull() || p.V.Key("Contents").Kind() == pdf.Null {
		return ""
	}

	fonts := map[string]*pdf.Font{}
	for _, name := range p.Fonts() {
		f := p.Font(name)
		fonts[name] = &f
	}

	var (
		chunks   []chunk
		enc      pdf.TextEncoding
		ctm      = identity
		ctmStack []matrix
		tm, tlm  = identity, identity
		leading  float64
		fontSize float64
	)

	moveLine := func(tx, ty float64) {
		tlm = matrix{1, 0, 0, 1, tx, ty}.mul(tlm)
		tm = tlm
	}
	decode := func(raw string) string {
		if enc == nil {
			return raw
		}
		return enc.Decode(raw)
	}
	emit := func(text string) {
		if text == "" {
			return
		}
		pos := tm.mul(ctm)
		size := fontSize * math.Hypot(pos[2], pos[3])
		if size <= 0 {
			size = 10
		}
		// Consecutive strings shown at the same spot belong to the same word run.
		if n := len(chunks); n > 0 && chunks[n-1].x == pos[4] && chunks[n-1].y == pos[5] {
			chunks[n-1].text += text
			return
		}
		chunks = append(chunks, chunk{x: pos[4], y: pos[5], size: size, text: text})
	}

	pdf.Interpret(p.V.Key("Contents"), func(stk *pdf.Stack, op string) {
		args := make([]pdf.Value, stk.Len())
		for i := len(args) - 1; i >= 0; i-- {
			args[i] = stk.Pop()
		}

		switch op {
		case "q":
			ctmStack = append(ctmStack, ctm)
		case "Q":
			if n := len(ctmStack); n > 0 {
				ctm, ctmStack = ctmStack[n-1], ctmStack[:n-1]
			}
		case "cm":
			if len(args) == 6 {
				ctm = matrix{
					args[0].Float64(), args[1].Float64(), args[2].Float64(),
					args[3].Float64(), args[4].Float64(), args[5].Float64(),
				}.mul(ctm)
			}
		case "BT":
			tm, tlm = identity, identity
		case "Tf":
			if len(args) == 2 {
				enc = nil
				if f, ok := fonts[args[0].Name()]; ok {
					enc = f.Encoder()
				}
				fontSize = args[1].Float64()
			}
		case "TL":
			if len(args) == 1 {
				leading = args[0].Float64()
			}
		case "Td":
			if len(args) == 2 {
				moveLine(args[0].Float64(), args[1].Float64())
			}
		case "TD":
			if len(args) == 2 {
				leading = -args[1].Float64()
				moveLine(args[0].Float64(), args[1].Float64())
			}
		case "Tm":
			if len(args) == 6 {
				tlm = matrix{
					args[0].Float64(), args[1].Float64(), args[2].Float64(),
					args[3].Float64(), args[4].Float64(), args[5].Float64(),
				}
				tm = tlm
			}
		case "T*":
			moveLine(0, -leading)
		case "Tj":
			if len(args) == 1 {
				emit(decode(args[0].RawString()))
			}
		case "'":
			if len(args) == 1 {
				moveLine(0, -leading)
				emit(decode(args[0].RawString()))
			}
		case "\"":
			if len(args) == 3 {
				moveLine(0, -leading)
				emit(decode(args[2].RawString()))
			}
		case "TJ":
			if len(args) != 1 {
				return
			}
			var b strings.Builder
			v := args[0]
			for i := 0; i < v.Len(); i++ {
				el := v.Index(i)
				switch el.Kind() {
				case pdf.String:
					b.WriteString(decode(el.RawString()))
				case pdf.Integer, pdf.Real:
					if -el.Float64() > tjSpaceThreshold {
						b.WriteString(" ")
					}
				}
			}
			emit(b.String())
		}
	})

	return layoutLines(chunks)
}

// layoutLines groups chunks into lines (top to bottom, left to right).
func layoutLines(chunks []chunk) string {
	if len(chunks) == 0 {
		return ""
	}
	sort.SliceStable(chunks, func(i, j int) bool { return chunks[i].y > chunks[j].y })

	var lines [][]chunk
	for _, c := range chunks {
		if n := len(lines); n > 0 {
			ref := lines[n-1][0]
			if math.Abs(ref.y-c.y) <= 0.4*math.Max(ref.size, c.size) {
				lines[n-1] = append(lines[n-1], c)
				continue
			}
		}
		lines = append(lines, []chunk{c})
	}

	var out strings.Builder
	for _, line := range lines {
		sort.SliceStable(line, func(i, j int) bool { return line[i].x < line[j].x })
		for i, c := range line {
			if i > 0 && needsSpace(line[i-1], c) {
				out.WriteString(" ")
			}
			out.WriteString(c.text)
		}
		out.WriteString("\n")
	}
	return out.String()
}

// needsSpace decides whether two neighbouring chunks on a line are separate
// words. Glyph widths are unknown, so runs are assumed to be words; the one
// exception is per-glyph placement (two single-character chunks close
// together), which is glued back into a word.
func needsSpace(prev, cur chunk) bool {
	if strings.HasSuffix(prev.text, " ") || strings.HasPrefix(cur.text, " ") {
		return false
	}
	if utf8.RuneCountInString(prev.text) == 1 && utf8.RuneCountInString(cur.text) == 1 {
		return cur.x-prev.x > 0.7*prev.size
	}
	return true
}
