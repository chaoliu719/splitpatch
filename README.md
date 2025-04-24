# splitpatch

[![PyPI version](https://img.shields.io/pypi/v/splitpatch.svg)](https://pypi.org/project/splitpatch/)
[![Python Versions](https://img.shields.io/pypi/pyversions/splitpatch.svg)](https://pypi.org/project/splitpatch/)
[![License](https://img.shields.io/github/license/chaoliu719/splitpatch.svg)](LICENSE)
[![Tests](https://github.com/chaoliu719/splitpatch/actions/workflows/tests.yml/badge.svg)](https://github.com/chaoliu719/splitpatch/actions/workflows/tests.yml)

[English](https://github.com/chaoliu719/splitpatch?tab=readme-ov-file#splitpatch) | [简体中文](https://github.com/chaoliu719/splitpatch/blob/main/README_zh-CN.md)

## Why Splitpatch?

In daily development, we often encounter these challenges:

-   📦 Receiving a massive patch with changes to dozens or even hundreds of files.
-   🔍 Needing to review large code changes in batches.
-   🔀 The patch might contain issues, requiring selective application of changes.
-   📋 Wanting to apply the patch progressively based on functional modules.

Splitpatch is designed to address these issues. It intelligently splits oversized patch files into multiple smaller patches based on modules and files, making patch management and code review simpler and more efficient.

### Differences from Similar Tools

Splitpatch differs fundamentally from traditional patch splitting tools (like [splitpatch](https://manpages.ubuntu.com/manpages/jammy/man1/splitpatch.1.html) or [split-patch](https://github.com/aleclearmind/split-patch)):

-   **Splits by Directory, Not File or Hunk**: Traditional tools usually split patches by individual files or hunks. Splitpatch uses the directory structure as a basis, preserving the integrity of logical modules.
-   **Intelligent Merging and Path Optimization**: Splitpatch analyzes the directory structure and file counts, optimizes paths, and merges small changes to generate more logically meaningful patch groups.
-   **Preserves File Integrity**: Even if a file has multiple modification hunks, Splitpatch keeps them within the same patch, ensuring file-level context integrity.

This design makes Splitpatch particularly suitable for handling complex patches in large projects, producing patch groupings that align better with human intuition and project structure.

## Installation and Usage

```bash
# Install using pip (no third-party dependencies, can also be used by cloning the repo)
pip install splitpatch

# Basic usage
splitpatch patch.diff --outdir patches

# Set directory level and file count threshold
splitpatch patch.diff --outdir patches --level 2 --threshold 5
```

### Parameter Usage Guide

The core of Splitpatch lies in its intelligent understanding of the directory structure and modification distribution within a patch. The `--level` and `--threshold` parameters allow you to fine-tune this understanding and splitting behavior:

-   `--level` (default: 1): **Defines the depth for module identification and protection.**
    -   It sets a "baseline" depth. Directory paths **at or shallower than** `level` are considered important top-level module boundaries and will **not** be merged into their parent directories or undergo path optimization. This helps preserve the main structure of the project (e.g., `bsp/`, `vendor/` are protected at `level=1`; `bsp/bootloader/`, `vendor/modules/` are also protected at `level=2`).
    -   **Selection Advice:**
        -   Use `--level 1` if you want to divide the patch according to the project's **top-level** major modules (like `bsp`, `vendor`, `frameworks`).
        -   Use `--level 2` or higher if you need finer granularity down to **sub-modules** (like `bsp/kernel`, `vendor/camera`).
-   `--threshold` (default: 10): **Defines how small a change scope qualifies as a "fragmented change".**
    -   It is a **file count threshold**. When the total number of modified files in a directory (including all its subdirectories) is **less than** this threshold, **and** the directory's depth is **greater than** the protection depth defined by `--level`, all modifications within this directory will be "promoted" and merged into the patch corresponding to its parent directory.
    -   **Purpose:** Prevents generating separate patch files for small directories with only one or two file modifications. It aggregates these scattered changes into a higher-level logical unit, making the patch list cleaner and more focused on major changes.
    -   **Selection Advice:**
        -   Set a **larger** `threshold` (e.g., 20, 30): This will merge more small directories, resulting in **fewer, more comprehensive** patches, suitable for quickly overviewing major changes.
        -   Set a **smaller** `threshold` (e.g., 5, 10): This will preserve more independent small directory structures, resulting in **more numerous, more focused** patches, suitable for scenarios requiring detailed review of each small functional block.

In summary, `--level` preserves the module structure you deem important (top-level/sub-level), while `--threshold` cleans up the overly fragmented changes beneath that structure, making the output more focused.

## Understanding the Tool's Logic: How Splitpatch Intelligently Splits

Splitpatch's core advantage is that it does **not** simply split by file or hunk. Instead, it attempts to understand the relationship between the patch content and the project's **directory structure and modularity**, performing a **logical** split. This results in patch chunks that better align with developer cognition and review habits. Its processing logic involves several key stages:

### The Key Difference: Directory Structure-Based Splitting

Before diving into the details, note the key distinction between Splitpatch and other tools (e.g., `git diff -- '*.c'` or some hunk-splitting tools): Splitpatch **focuses on directories**. Even if a file has multiple hunks, it always belongs to the logical block of the directory containing it. Splitpatch aims to group related changes based on the **directory** a file resides in and its **hierarchical relationship** within the project.

### Phase 1: Identifying Potential Module Boundaries

Splitpatch first analyzes all file paths involved in the patch to build a directory tree structure of modifications. It then identifies directories likely representing independent logical modules based on the following heuristics:

1.  **Depth Matters:** Directory depth is a significant factor, with `--level` setting the initial identification baseline.
2.  **Finding Module "Root" Indicators:** Splitpatch looks for directories that **contain file modifications themselves** (e.g., direct modification to `bsp/bootloader/Makefile`) or whose **direct subdirectories contain numerous modifications**. Particularly, if a directory directly contains modified build-related files like `Makefile`, `build.gn`, or `CMakeLists.txt`, it's highly likely to be the root of a module.
3.  **Independence Judgment:** If a directory's parent directory has **no** direct file modifications, this often suggests the directory is a relatively independent logical unit.

### Phase 2: Path Optimization (Shortening Deep Paths)

In large projects, code paths can be very deep. This phase aims to simplify these paths, making the generated patch filenames and the file paths within the patches more concise and understandable.

1.  **Optimization Target:** Only directory paths **deeper than** `--level` are considered for processing. Paths at `level` and shallower are considered important, protected structures and are not optimized.
2.  **Compression Rule:** If a directory merely acts as a "pass-through" (no file modifications itself, and only one subdirectory contains modifications), it might be "compressed" out of the final path representation.

### Phase 3: Intelligent Merging of Fragmented Changes

After the first two phases, we have a directory tree with a clearer structure and more reasonable paths. The final step is to handle "fragmented" directories with few changes, merging them into their parent level to avoid generating too many small, granular patches.

1.  **Merge Check:** Starting from the deeper directories, it checks the total file modification count for each directory (including its subdirectories) upwards.
2.  **`--threshold` Decision:** If a directory's total file modification count is **less than** `--threshold`, **and** its depth is **greater than** `--level` (meaning it's not a protected top-level module), then all modifications under this directory are merged into the processing unit of its parent directory.
3.  **`--level` Protection:** The `--level` parameter acts here to **prevent over-merging**. It ensures that directories reaching the `level` depth (and shallower ones) are not merged into their parents due to low file counts, preserving the user-specified important module divisions.
4.  **Recursive Merging:** This process occurs recursively until all eligible fragmented directories are merged.

Through these three stages, Splitpatch aims to intelligently transform a large patch—potentially containing hundreds of files across dozens of directories—into a series of **logically cohesive, appropriately sized** smaller patches, significantly enhancing the efficiency and experience of code review and patch application management.

## A Practical Example: Simplifying Complexity

Imagine receiving a massive patch file, `real-project.diff`, containing hundreds of file changes spanning multiple project modules and deeply nested directories. Directly reviewing or applying such a patch is undoubtedly a daunting task.

Now, let's see how Splitpatch tackles this. We run the following command:

```bash
splitpatch real-project.diff --outdir split-patches --level 1 --threshold 10
```

After execution, the originally chaotic large patch is **intelligently split** into multiple **logically clear and structurally organized** small patches within the `split-patches/` directory:

```
split-patches/
├── 001_bsp.patch                 # Contains all changes under bsp/ except bootloader/ (7 files)
├── 002_bsp_bootloader.patch      # Specifically contains changes in bsp/bootloader/ (11 files)
├── 003_build.patch               # All changes under the build/ directory (5 files)
├── 004_device.patch              # All changes under the device/ directory (5 files)
├── 005_external.patch            # All changes under the external/ directory (1 file)
├── 006_frameworks.patch          # All changes under the frameworks/ directory (4 files)
├── 007_packages.patch            # All changes under the packages/ directory (3 files)
├── 008_system.patch              # All changes under the system/ directory (9 files)
├── 009_vendor.patch              # Contains changes under vendor/ except modules/ (1 file)
└── 010_vendor_modules.patch      # Specifically contains the numerous changes in vendor/modules/ (320 files)
```

As you can see, Splitpatch transformed a complex large patch into a series of module-organized, easier-to-manage small patches. This makes batch reviewing, applying by functionality, or locating specific changes exceptionally simple.

So, how does Splitpatch achieve this **intelligent splitting**? Let's break down its workflow step-by-step using the command above (`level=1`, `threshold=10`) as an example:

### Original Patch File Structure

This patch contains modifications scattered across a complex directory structure. Initially, the file tree looks like this (simplified, showing only part of the structure):

```
/
└── bsp
│   └── bootloader
│   │   └── lk
│   │       └── app
│   │       │   └── sprdboot (1 file)
│   │       └── platform
│   │       │   └── common (1 file)
│   │       │   │   └── include (1 file)
│   │       │   └── sprd_shared
│   │       │       └── driver
│   │       │           └── video
│   │       │               └── sprd (1 file)
│   │       │                   └── lcd (1 file)
│   │       └── project (1 file)
│   │       └── target
│   │           └── uis7885_2h10 (5 files)
│   └── kernel5.4
│       └── kernel5.4
│           └── arch
│           │   └── arm64
│           │       └── boot
│           │       │   └── dts
│           │       │       └── sprd (3 files)
│           │       └── configs (1 file)
│           └── drivers
│               └── input
│                   └── touchscreen (2 files)
│                       └── focaltech_touch (1 file)
└── build
    └── make
        └── core (1 file)
        └── target
        │   └── product (2 files)
        └── tools (2 files)
# ... more directory structure omitted
└── vendor
    └── sprd
        └── modules
        │   └── libcamera (1 file)
        │       └── sensor
        │           └── af_drv (1 file)
        │           │   └── dw9714 (3 files)
        │           │   └── dw9800 (3 files)
        │           └── its_param
        │               └── qogirn6pro
        │                   └── Samsung
        │                   │   └── s5k3p9sx04 (1 file)
        │                   │   │   └── cap0 (11 files)
        │                   │   │   └── cap0_hdr (1 file)
        │                   │   │   └── cap0_zoom (4 files)
        │                   │   │   └── com (58 files)
        │                   │   │   └── other (5 files)
        │                   │   │   └── prv0 (6 files)
        │                   │   │   └── video0 (15 files)
        │                   │   └── s5k3p9sx04_main2 (1 file)
        │                   │   │   └── ... similar structure, multiple subdirs
        │                   │   └── s5k4h7_front_main (1 file)
        │                   │       └── ... similar structure
        └── release
            └── bmp
                └── unisoc_bmp (1 file)
```

This structure shows a typical complex project with scattered changes and deep paths. Handling it directly would be very difficult.

### Phase 1: Module Identification and Path Flattening

Splitpatch first analyzes all modified file paths and initially identifies logical units based on the directory structure. Simultaneously, it performs path flattening, "promoting" files from deep directories that logically belong to the same submodule to a more reasonable level.

In this example, we set `level=1`, meaning all first-level directories (like `bsp/`, `build/`, `vendor/`) are treated as important module boundaries and won't be merged to higher levels.

After flattening, the file tree becomes:

```
/
└── bsp
│   └── bootloader
│   │   └── lk
│   │       └── app
│   │       │   └── sprdboot (1 file)
│   │       └── platform
│   │       │   └── common (2 files)  # Merged files from include
│   │       │   └── sprd_shared
│   │       │       └── driver
│   │       │           └── video
│   │       │               └── sprd (2 files) # Merged file from lcd
# ... (omitted) ...
│   └── kernel5.4
│       └── kernel5.4 # Note the redundant level still exists here
# ... (omitted) ...
│                   └── touchscreen (3 files) # Merged file from focaltech_touch
# ... (omitted) ...
└── vendor
    └── sprd
        └── modules
        │   └── libcamera (320 files)  # Numerous deep files merged into the libcamera unit
        └── release
            └── bmp
                └── unisoc_bmp (1 file)
```
At this stage, Splitpatch has already started consolidating some files, like the 320 files under `vendor/sprd/modules/libcamera` being grouped into the same logical unit.

### Phase 2: Path Optimization

Next, Splitpatch further processes the directory structure, **shortening** path levels that are excessively deep or serve only as "pass-throughs". Crucially, it **respects the `--level` parameter**. Since we set `level=1`, depth-1 directories (like `bsp/`, `build/`, `vendor/`) and their direct paths are not optimized away, ensuring the integrity of the top-level module structure. Optimization primarily affects deeper levels.

After path optimization, the internal file tree (logical representation) becomes much cleaner:

```
/
└── bsp
│   └── bootloader
│   │   └── app (1 file) # lk/app/sprdboot simplified
│   │   └── platform
│   │   │   └── common (2 files)
│   │   │   └── sprd_shared (2 files) # driver/video/sprd simplified
│   │   └── project (1 file)
│   │   └── target (5 files) # uis7885_2h10 simplified
│   └── kernel5.4 # kernel5.4/kernel5.4 simplified to one level
│       └── arch
│       │   └── boot (3 files) # arm64/boot/dts/sprd simplified
│       │   └── configs (1 file)
│       └── drivers (3 files) # input/touchscreen simplified
└── build
│   └── make # make level preserved
│       └── core (1 file)
│       └── target (2 files) # product simplified
│       └── tools (2 files)
# ... (omitted) ...
└── vendor
    └── sprd # sprd level usually preserved
        └── modules (320 files) # Complex structure under libcamera simplified significantly to modules
        └── release (1 file) # bmp/unisoc_bmp simplified
```
Through path optimization, changes in deeply nested structures are mapped to more manageable and understandable directory levels.

### Phase 3: Intelligent File Merging

The final step is merging the "fragmented" changes. Splitpatch starts from the deepest optimized paths and works upwards, checking the total number of modified files within each directory (including subdirectories).

1.  **Check Threshold (`--threshold 10`)**: If a directory's total file count is **less than 10**...
2.  **Check Protection Level (`--level 1`)**: **AND** the directory's depth is **greater than 1** (i.e., it's not a top-level directory like `bsp/`, `build/`, `vendor/`)...
3.  **Perform Merge**: Then all file modifications under this directory are merged into its **parent directory's** count and will be included in the parent's corresponding `.patch` file during generation.

This process is recursive. For example, `vendor/sprd/release` has only 1 file (< 10) and is deeper than level 1, so it gets merged into `vendor/sprd`. However, `vendor/sprd` itself, when considering `modules` (320 files), has a total count far exceeding 10, so `vendor/sprd` won't be merged further up. But, since `vendor/sprd/modules` contains 320 files (>> 10), it **remains independent**, forming its own `vendor_modules.patch`.

Ultimately, based on the merging logic with `--level 1` and `--threshold 10`, the file counts and groupings we saw at the beginning are formed:

```
/
└── bsp (7 files)  # Merged fragmented changes from kernel5.4, but bootloader is separate
│   └── bootloader (11 files) # File count > 10, remains independent
└── build (5 files)
└── device (5 files)
└── external (1 file)
└── frameworks (4 files)
└── packages (3 files)
└── system (9 files)
└── vendor (1 file) # Merged the 1 file from release
    └── modules (320 files) # File count > 10, remains independent
```

### Summary Analysis

This example clearly demonstrates how Splitpatch works according to the parameters `level=1` and `threshold=10`:

1.  **Respects Top-Level Structure (`level=1`)**: First-level directories like `bsp/`, `build/`, `vendor/` are always treated as separate splitting units and are not merged.
2.  **Preserves Important Submodules (`threshold=10`)**: Subdirectories with file counts exceeding 10 (like `bsp/bootloader` and `vendor/modules`) are also recognized as significant logical units and get their own patches.
3.  **Aggregates Fragmented Changes**: Modifications in directories with fewer than 10 files and deeper than level 1 are intelligently merged into their parent module, avoiding excessive trivial patch files.

Thus, a massive patch, potentially spanning hundreds of files and dozens of directories, is systematically organized by Splitpatch into 10 logically cohesive and manageably sized patch files. This significantly simplifies the code review and patch management process, enabling developers to handle complex code changes more efficiently.

## Contributing

We warmly welcome and appreciate contributions to `splitpatch`! We encourage participation in various forms, including but not limited to:

*   Reporting bugs or issues
*   Suggesting features or improvement ideas
*   Submitting code fixes or implementing new features
*   Improving documentation

If you wish to contribute, please follow these basic steps:

1.  **Report Issues or Suggest Features**:
    *   Please submit them via the project's [GitHub Issues](https://github.com/chaoliu719/splitpatch/issues) page.
    *   For bug reports, provide detailed steps to reproduce, environment information, and the observed behavior.
    *   For feature suggestions, clearly describe the desired functionality and its use case.

2.  **Submit Code or Documentation Improvements (Pull Requests)**:
    *   We highly welcome Pull Requests if you want to fix issues or implement features directly.
    *   Please fork the repository to your account first. After making your changes and committing them, create a Pull Request targeting the `main` branch of this repository. Clearly describe the changes you made and the reasoning behind them in the PR description.

We look forward to your participation in making `splitpatch` even better!

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.