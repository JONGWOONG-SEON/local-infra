package installer

import (
	"bytes"
	"fmt"
	"os"
	"os/exec"
)

func (i *BrewInstaller) InstallBrewPackage(pkg string) error {
	if _, err := exec.LookPath("brew"); err != nil {
		fmt.Fprintln(os.Stderr, "Homebrew(brew)가 시스템에 설치되어 있지 않거나 PATH에 없습니다.")
		os.Exit(1)
	}

	cmd := exec.Command("brew", "install", pkg)

	var outBuf, errBuf bytes.Buffer
	cmd.Stdout = os.Stdout
	cmd.Stderr = os.Stderr

	// 실제 명령 실행
	if err := cmd.Run(); err != nil {
		fmt.Fprintf(os.Stderr, "설치 중 오류 발생: %v\n", err)
		fmt.Fprintf(os.Stderr, "stderr: %s\n", errBuf.String())
		os.Exit(1)
	}

	// 성공 시 출력
	fmt.Println("=== 설치 성공 ===")
	fmt.Println(outBuf.String())

	return nil
}

func (i *BrewInstaller) CatchBrewInstallList(pkgs []string) error {
	for _, pkg := range pkgs {
		if err := i.InstallBrewPackage(pkg); err != nil {
			return err
		}
	}
	return nil
}
