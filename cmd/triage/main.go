package main

import (
	"os"

	"github.com/monitaurus/triage/internal/cli"
)

func main() {
	if err := cli.Execute(); err != nil {
		os.Exit(1)
	}
}
