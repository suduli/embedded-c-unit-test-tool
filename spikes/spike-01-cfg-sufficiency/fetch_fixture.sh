#!/usr/bin/env bash
# fetch_fixture.sh — pulls a real, >=20kLOC embedded C codebase with vendor
# headers (STM32F4 HAL driver + CMSIS) for the CFG-sufficiency spike.
# STMicroelectronics. Not vendored into this repo — fetched on demand into
# a gitignored directory.
#
# DEVIATION FROM THE ORIGINAL PLAN (documented in RESULTS.md): as of the
# date this spike ran, STM32CubeF4's superproject references
# Drivers/STM32F4xx_HAL_Driver and Drivers/CMSIS/Device/ST/STM32F4xx as git
# submodules (gitlinks, mode 160000), not plain committed directories, so
# the superproject's own sparse-checkout can no longer materialize their
# content (a plain `git sparse-checkout set` on those paths silently
# produces empty directories). We sparse-checkout the superproject only for
# the one path that IS still a plain directory (Drivers/CMSIS/Include) and
# clone the two former-submodule repos directly from their .gitmodules URLs.
# Both are still real, current STMicroelectronics vendor sources for the
# same STM32F4/Cortex-M4 target — same spirit as the original single-repo
# sparse-checkout, just split across the repos ST actually publishes today.
set -euo pipefail
cd "$(dirname "$0")"
rm -rf fixture

git clone --filter=blob:none --no-checkout --depth 1 \
  https://github.com/STMicroelectronics/STM32CubeF4.git fixture
(
  cd fixture
  git sparse-checkout init --cone
  git sparse-checkout set Drivers/CMSIS/Include
  git checkout
)

git clone --depth 1 --branch master \
  https://github.com/STMicroelectronics/stm32f4xx_hal_driver.git \
  fixture/Drivers/STM32F4xx_HAL_Driver
rm -rf fixture/Drivers/STM32F4xx_HAL_Driver/.git

git clone --depth 1 --branch master \
  https://github.com/STMicroelectronics/cmsis_device_f4.git \
  fixture/Drivers/CMSIS/Device/ST/STM32F4xx
rm -rf fixture/Drivers/CMSIS/Device/ST/STM32F4xx/.git

# stm32f4xx_hal_conf.h is a per-project config file that every HAL driver .c
# file #includes (via stm32f4xx_hal.h), but it is deliberately NOT shipped in
# the driver repo — only a template is, which every real STM32 project copies
# in and (optionally) edits during project setup. Without this step, ~80% of
# the HAL Src/*.c files fail to parse past their first #include with a fatal
# "file not found" error, which is a fixture-setup gap, not a libclang/CFG
# finding. This is the standard, ST-documented setup action, not a modification
# of vendor logic — the template enables every HAL module by default.
cp fixture/Drivers/STM32F4xx_HAL_Driver/Inc/stm32f4xx_hal_conf_template.h \
   fixture/Drivers/STM32F4xx_HAL_Driver/Inc/stm32f4xx_hal_conf.h

echo "Fixture ready. Line count:"
find fixture/Drivers \( -name '*.c' -o -name '*.h' \) | xargs wc -l | tail -1
