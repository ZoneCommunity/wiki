---
title: ZoneOS
core: ZoneCore
initial_development: March 2022
status: In development
developer: ZoneCommunity
latest_build: R2 B34 (261117)
current_branch: Mesolite
current_core: ZoneCore
source_model: Open source
license: 3-Clause BSD License
official_website: zonecommunity.net
image: /assets/ZoneOS/MesolitePromo.png
description: ZoneOS is a series of PPTOSes developed by ZoneCommunity.
---

# ZoneOS

**ZoneOS** is a series of PPTOSes developed by ZoneCommunity.

## Overview

ZoneOS is a long-running project with many versions. The version
order is Culebra, Malachite, Tanzanite, Plexorite, Levynite,
ZoneOS+, and Mesolite.

The current version is [Mesolite](/ZoneOS/Mesolite/), which also has
the most features. Mesolite is the most advanced version of ZoneOS
to date, utilizing various different techniques to provide the
most realistic PPTOS experience possible.

## History

ZoneOS started with many early experiments such as: Culebra, a PPTOS
that created windows in pure VBA; Malachite, which extended the usage
of VBA for applications; and Tanzanite, which was originally the longest
lasting branch of ZoneOS up until Mesolite.

In late 2025, ZoneCore ran in both Mesolite and Levynite. Levynite
branched off Mesolite as a simplified release version, but it
gained complex experimental features and got buggy, while Mesolite
lagged in features. So they merged into ZoneOS+, then stripped some
Levynite UI and became Mesolite again.

During the merger, it was being considered to scrap ZoneOS+ and
ZoneCore entirely, instead developing two ZoneOSes at the same
time: ZoneOS S, with SCore, simpler and to release first, and
ZoneOS X, with XCore, the full, most advanced one. However, only
a singular XCore build exists.

## Architecture

ZoneOS runs inside a PowerPoint slideshow. Windows are shapes in a
cSurface and cElement tree, managed by the surface. Input comes
in through Win32 mouse and keyboard hooks. A system timer
ticks to handle various system services.

Mesolite adds real apps, a shape-based virtual filesystem, a custom
input system, a hover system, a textbox system, a theme system, and
multi-language support. It also has work-in-progress HiDPI and aspect
ratio support.

## Versions

| Version | Core | Status |
| --- | --- | --- |
| Culebra | - | Unknown |
| Malachite | - | Early experiment |
| Malachite | Zore | Canceled |
| Tanzanite | ZMC | Scrapped |
| Tanzanite | Zore | Early experiment |
| Plexorite | - | Various experiments |
| [Mesolite](/ZoneOS/Mesolite/) | ZoneCore | In development |
| [Levynite](/ZoneOS/Levynite/) | ZoneCore | Merged into ZoneOS+ |
| [ZoneOS+](/ZoneOS/ZoneOS-Plus/) | ZoneCore | Became Mesolite again |

See [All versions](/ZoneOS/Versions/) for the full list, with
each version's subpages.

## See also

- [All versions](/ZoneOS/Versions/)
- [Mesolite](/ZoneOS/Mesolite/)
