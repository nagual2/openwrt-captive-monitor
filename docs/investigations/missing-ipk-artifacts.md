# Investigation: missing `.ipk` artifacts

## Summary

The CI run referenced in PR #47 only executed the **BusyBox lint and test** workflow. That job exercises the ash test
harness but does not build or publish the OpenWrt package. The workflow that actually creates and uploads the `.ipk`
artefact is **Build OpenWrt packages**, and in the inspected run it was never triggered, so no package or feed files
could appear in the runs artefact list, releases, or repository tree.

Locally and in any CI run that executes `openwrt-build.yml`, `scripts/build_ipk.sh` produces a valid `.ipk` together
with `Packages` and `Packages.gz`. The upload step in the workflow depends on those files and will fail the job if
they are missing, which confirms that the artefact absence stems from the workflow not running rather than the build
helper malfunctioning.

## Findings

1. **Workflow coverage**
* `.github/workflows/openwrt-build.yml` contains the `Build .ipk package`, `Verify build outputs`, and `Upload build
artifacts` steps. When executed, it wipes `dist/opkg`, runs `./scripts/build_ipk.sh`, checks for the expected files,
and uploads them with the artefact name `${pkg_name}_${pkg_version}-${pkg_release}_${pkg_arch}`.
* The CI run linked from PR #47 lists only the **BusyBox lint and test** workflow. There is no corresponding **Build
OpenWrt packages** run, which is why no artefact is attached.

2. **`scripts/build_ipk.sh` behaviour**
* The helper script validates prerequisites (`ar`, `tar`, `gzip`, `md5sum`, `sha256sum`, `stat`), stages payload and
control files, assembles the package (`ar r dist/opkg/<arch>/<pkg>_<ver>-<rel>_<arch>.ipk`), and regenerates
`Packages` / `Packages.gz`.
   * Run locally from the repository root:

     ```bash
     $ bash scripts/build_ipk.sh
     Created package: /home/engine/project/dist/opkg/all/openwrt-captive-monitor_0.1.3-1_all.ipk (13260 bytes)
     Updated feed index under: /home/engine/project/dist/opkg/all (entries: 1)
     Feed artifacts:
       - dist/opkg/all/openwrt-captive-monitor_0.1.3-1_all.ipk (13260 bytes)
       - dist/opkg/all/Packages (704 bytes)
       - dist/opkg/all/Packages.gz (475 bytes)
     ```

     The same steps run inside the `Build .ipk package` job, so the helper is not the source of the missing artefact.

3. **Upload guarantees**
* `openwrt-build.yml` marks `if-no-files-found: error` on the upload step and performs explicit `test -f`/`test -s`
checks. A successful job therefore implies the files exist and were uploaded; an absent artefact means the job never
ran.

## Root cause

The packaging workflow did not execute for the analysed run (only the lint/test workflow ran). Because the `.ipk` is
produced and uploaded exclusively by `.github/workflows/openwrt-build.yml`, skipping that workflow leaves no artefact
in Actions, Releases, or the repository tree.

Typical reasons for the packaging workflow not running include:

* The workflow was never triggered (e.g. only the lint workflow ran, or the branch push was outside the trigger
filters).
* The run required manual approval (e.g. PRs from forks) and was not started.

## Recommended actions

1. **Re-run `Build OpenWrt packages` for the branch/PR.** Use the _Actions_ tab to manually dispatch the workflow or
approve its execution for forked pull requests. Once the job finishes, an artefact named
`openwrt-captive-monitor_<version>-<release>_<arch>` will appear with the `.ipk`, `Packages`, and `Packages.gz` files.
2. **Automatic branch coverage is now enabled.** The workflow triggers on `main` as well as `feature/**`, `feature-*`,
`fix/**`, `fix-*`, `chore/**`, `chore-*`, `docs/**`, `docs-*`, `hotfix/**`, and `hotfix-*` pushes, so new topic
branches immediately build and upload `.ipk` artefacts without manual intervention.
3. **Manual fallback**: run `scripts/build_ipk.sh` locally and upload the contents of `dist/opkg/<arch>/` to the
release if a run still needs to be backfilled.

Following these steps ensures `.ipk` artefacts are created whenever a branch or PR needs validation, eliminating the
gap observed in PR #47.
