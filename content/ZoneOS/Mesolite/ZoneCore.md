---
title: ZoneCore
description: The core used within ZoneOS Mesolite.
developer: ZoneCommunity
status: Current
latest_build: R2 B34 (261117)
---

# ZoneCore

**ZoneCore** is the core used within ZoneOS Mesolite. It is the
current core of ZoneOS, powering the current branch,
[Mesolite](/ZoneOS/Mesolite/).

## Overview

ZoneCore is the foundation Mesolite runs on. It provides the window
manager, the UI toolkit, input handling, and the filesystem, all
inside a PowerPoint slideshow. Mesolite is the longest developed
ZoneOS version, with the most features, and it runs on ZoneCore.

## What it does

- Window manager: windows are shapes in a cSurface and cElement
  tree, managed by the surface.
- Surface System: ZoneOS's class-based VBA UI toolkit for creating
  ZoneOS applications.
- Input: Win32 mouse and keyboard hooks bring mouse and keyboard
  input into the slideshow.
- System services: a system timer ticks to handle various system
  services.
- Filesystem: ZoneFS, a shape-based virtual filesystem.
- Interface systems: a hover system, a textbox system, and a theme
  system.
- Languages: multi-language support.

## History

In late 2025, ZoneCore ran in both Mesolite and
[Levynite](/ZoneOS/Levynite/). Levynite branched off Mesolite as
a simplified release version, but it gained complex experimental
features and got buggy, while Mesolite lagged in features. So they
merged into [ZoneOS+](/ZoneOS/ZoneOS-Plus/), then some Levynite UI
was stripped and it became Mesolite again, in November 2025.

Mesolite originally began development in August 2024 as an
experimental PPTOS. In November 2026, Mesolite's development was
picked back up after months of inactivity, entering the "R2"
phase of development. The latest build is R2 B34 (261117).

## Versions that use it

- [Mesolite](/ZoneOS/Mesolite/) - the current branch, running
  ZoneCore.
- [Levynite](/ZoneOS/Levynite/) - ran ZoneCore in late 2025,
  before merging into ZoneOS+.
- [ZoneOS+](/ZoneOS/ZoneOS-Plus/) - the merger of Mesolite and
  Levynite, running ZoneCore, which became Mesolite again.

## See also

- [Mesolite](/ZoneOS/Mesolite/)
- [Levynite](/ZoneOS/Levynite/)
- [ZoneOS+](/ZoneOS/ZoneOS-Plus/)
- [ZoneOS](/ZoneOS/)
- [All versions](/ZoneOS/Versions/)
