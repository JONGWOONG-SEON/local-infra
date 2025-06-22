package main

import (
	"fmt"
	"os"

	"install/installer"
	"install/pkglist"
)

func main() {
	inst := installer.BrewInstaller{}
	dinst := installer.DockerInstaller{}

	if err := inst.CatchBrewInstallList(pkglist.BrewPackges); err != nil {
		fmt.Fprintln(os.Stderr, "Brew 설치 오류", err)
		os.Exit(1)
	}

	if err := dinst.CatchDockerInstallList(pkglist.DockerImages); err != nil {
		fmt.Fprintln(os.Stderr, "Docker Images Pull 오류", err)
		os.Exit(1)
	}
}
