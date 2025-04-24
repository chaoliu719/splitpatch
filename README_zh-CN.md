# splitpatch

[![PyPI version](https://img.shields.io/pypi/v/splitpatch.svg)](https://pypi.org/project/splitpatch/)
[![Python Versions](https://img.shields.io/pypi/pyversions/splitpatch.svg)](https://pypi.org/project/splitpatch/)
[![License](https://img.shields.io/github/license/chaoliu719/splitpatch.svg)](LICENSE)
[![Tests](https://github.com/chaoliu719/splitpatch/actions/workflows/tests.yml/badge.svg)](https://github.com/chaoliu719/splitpatch/actions/workflows/tests.yml)
[![codecov](https://codecov.io/gh/chaoliu719/splitpatch/branch/main/graph/badge.svg)](https://codecov.io/gh/chaoliu719/splitpatch)

[English](https://github.com/chaoliu719/splitpatch?tab=readme-ov-file#splitpatch) | [简体中文](https://github.com/chaoliu719/splitpatch/blob/main/README_zh-CN.md)

## 为什么需要 Splitpatch？

在日常开发中，我们经常会遇到这些困扰：

- 📦 收到一个包含几十个甚至上百个文件改动的大型补丁
- 🔍 需要分批次审查大量代码改动
- 🔀 补丁中可能存在问题，需要选择性地应用部分改动
- 📋 想要按照功能模块逐步应用补丁

Splitpatch 就是为解决这些问题而生的，它可以将超大补丁文件（patch）智能地分割成多个基于模块和文件的小补丁，让补丁管理和代码审查变得更加简单、高效。

### 与类似工具的区别

Splitpatch 与传统的补丁分割工具（如 [splitpatch](https://manpages.ubuntu.com/manpages/jammy/man1/splitpatch.1.html) 或 [split-patch](https://github.com/aleclearmind/split-patch)）有本质区别：

- **按目录分割，而非按文件或代码块(hunk)分割**：传统工具通常按单个文件或代码块来分割补丁，而 Splitpatch 以目录结构为基础，保持了逻辑模块的完整性。
- **智能合并和路径优化**：Splitpatch 会分析目录结构和文件数量，优化路径并合并小改动，生成更有逻辑意义的补丁分组。
- **保持文件完整性**：即使一个文件有多个修改块(hunk)，Splitpatch 也会将其保留在同一个补丁中，确保文件级别的上下文完整性。

这种设计使 Splitpatch 特别适合处理大型项目中的复杂补丁，产出更符合人类直觉和项目结构的补丁分组。

## 安装与使用

```bash
# 使用 pip 安装（无第三方依赖，也可以直接克隆代码仓库使用）
pip install splitpatch

# 基本用法
splitpatch patch.diff --outdir patches

# 设置目录级别和文件数量阈值
splitpatch patch.diff --outdir patches --level 2 --threshold 5
```

### 参数使用指南

Splitpatch 的核心是智能地理解补丁中的目录结构和修改分布。`--level` 和 `--threshold` 这两个参数让你可以精细地调整这种理解和分割方式：

- `--level` (默认值: 1): **定义模块识别和保护的层级深度**。
  - 它设定了一个“基准”深度。目录层级**等于或浅于** `level` 的路径被视为重要的顶层模块边界，**不会**被合并到它们的父目录中，也不会进行路径优化。这有助于保留项目的主要结构（例如，`bsp/`, `vendor/` 在 `level=1` 时是受保护的；`bsp/bootloader/`, `vendor/modules/` 在 `level=2` 时也是受保护的）。
  - **选择建议：**
    -    如果你想按项目**最顶层**的几个大模块（如 `bsp`, `vendor`, `frameworks`）来划分补丁，使用 `--level 1`。
    -    如果你需要更细致地深入到**次级模块**（如 `bsp/kernel`, `vendor/camera`），则使用 `--level 2` 或更高。
- `--threshold` (默认值: 10): **定义多小的改动规模算是“零碎改动”**。
  - 它是一个**文件数量阈值**。当一个目录（及其所有子目录）的总文件修改数**少于**这个阈值，**并且**该目录的深度**大于** `--level` 所定义的保护深度时，这个目录下的所有修改就会被“上提”合并到其父目录对应的补丁中。
  - **作用：** 防止为只有一两个文件修改的小目录生成独立的补丁文件，将这些零散的改动聚合到更上一层的逻辑单元中，使得补丁列表更简洁、更聚焦于主要改动。
  - **选择建议：**
    -    设置**较大**的 `threshold` (如 20, 30)：会合并更多的小目录，生成**数量更少、更综合**的补丁，适合快速概览主要改动。
    -    设置**较小**的 `threshold` (如 5, 10)：会保留更多独立的小目录结构，成**数量更多、更聚焦**的补丁，适合需要细致审查每个小功能块的场景。

总之，`--level` 负责保留你认为重要的顶层/次层模块结构，而 `--threshold` 负责清理这些结构之下过于零散的改动，让输出更聚焦。

## 理解工具原理：Splitpatch 如何智能分割

Splitpatch 的核心优势在于它**并非**简单地按文件或代码块 (hunk) 分割，而是尝试理解补丁内容与项目**目录结构、模块化**的关系，从而进行**逻辑上**的分割。这使得生成的补丁块更符合开发者的认知和审查习惯。其处理逻辑主要包含以下几个关键阶段：

### 与众不同之处：基于目录结构的智能分割

在深入了解原理之前，请注意 Splitpatch 与其他工具 (例如 `git diff -- '*.c'` 或某些按 hunk 分割的工具) 的关键区别：Splitpatch **着眼于目录**。即使一个文件内有多个 hunk 修改，它也始终属于该文件所在的目录逻辑块。Splitpatch 的目标是根据文件**所在的目录**及其在项目中的**层级关系**，将相关的改动聚合在一起。

### 第一阶段：识别潜在的模块边界

Splitpatch 首先会分析补丁涉及的所有文件路径，构建一个文件修改的目录树结构。然后，它会根据以下启发式规则识别哪些目录可能代表着一个独立的逻辑模块：

1.  **深度优先：** 目录的深度是重要的考量因素，`--level` 参数在这里设定了初始的识别基准。
2.  **寻找模块“根”标志：** Splitpatch 会关注那些**自身包含文件修改** (例如，直接修改了 `bsp/bootloader/Makefile`) 或者**其直接子目录包含大量修改**的目录。特别是，如果一个目录直接包含像 `Makefile`, `build.gn`, `CMakeLists.txt` 这样的编译/构建相关文件修改，它就很有可能是一个模块的根目录。
3.  **独立性判断：** 如果一个目录的父目录**没有**直接的文件修改，这通常也暗示着该目录是一个相对独立的逻辑单元。

### 第二阶段：路径优化 (缩短深层路径)

大型项目中，代码路径可能非常深。路径优化阶段旨在简化这些路径，使得生成的补丁文件名和补丁内部的文件路径更简洁易懂。

1.  **优化对象：** 只考虑处理深度**大于** `--level` 的目录路径。`--level` 及更浅的路径被认为是重要的、受保护的结构，不进行优化。
2.  **压缩规则：** 如果一个目录仅仅作为“通道”（自身无文件修改，且只有一个子目录包含修改），它可能在最终路径中被“压缩”掉。

### 第三阶段：智能合并零散改动

经过前两步，我们有了一个结构更清晰、路径更合理的目录树。最后一步是处理那些改动很少的“零散”目录，将它们合并到父级中，避免生成过多细碎的补丁。

1.  **合并检查：** 从较深的目录开始，向上检查每个目录（及其子目录）的总文件修改数。
2.  **`--threshold` 决策：** 如果一个目录的总文件修改数**小于** `--threshold`，并且该目录的深度**大于** `--level` (意味着它不是受保护的顶层模块)，则这个目录下的所有修改将被合并到其父目录的处理单元中。
3.  **`--level` 保护：** `--level` 参数在此阶段的作用是**防止过度合并**。它确保了达到 `level` 深度的目录（以及更浅的目录）不会因为文件数量少而被合并到其父目录中，保留了用户指定的重要模块划分。
4.  **递归合并：** 这个过程会递归进行，直到所有符合条件的零散目录都被合并。

通过这三个阶段的处理，Splitpatch 旨在将一个可能包含数百个文件、横跨数十个目录的大补丁，智能地拆分成一系列**逻辑内聚、大小适中**的小补丁，极大地提升了代码审查和补丁应用管理的效率和体验。

## 一个实际的例子：化繁为简

想象一下，您收到了一个庞大的补丁文件 `real-project.diff`，其中包含了跨越项目多个模块、深层嵌套目录的几百个文件改动。直接审查或应用这样的补丁无疑是一项艰巨的任务。

现在，让我们看看 Splitpatch 如何解决这个问题。我们运行以下命令：

```bash
splitpatch real-project.diff --outdir split-patches --level 1 --threshold 10
```

执行完毕后，原本杂乱无章的大补丁被 **智能地分割** 成了 `split-patches/` 目录下 **逻辑清晰、结构分明** 的多个小补丁：

```
split-patches/
├── 001_bsp.patch                 # 包含 bsp/ 下除 bootloader/ 外的所有修改 (7 files)
├── 002_bsp_bootloader.patch      # 专门包含 bsp/bootloader/ 的修改 (11 files)
├── 003_build.patch               # build/ 目录下的所有修改 (5 files)
├── 004_device.patch              # device/ 目录下的所有修改 (5 files)
├── 005_external.patch            # external/ 目录下的所有修改 (1 file)
├── 006_frameworks.patch          # frameworks/ 目录下的所有修改 (4 files)
├── 007_packages.patch            # packages/ 目录下的所有修改 (3 files)
├── 008_system.patch              # system/ 目录下的所有修改 (9 files)
├── 009_vendor.patch              # vendor/ 下除 modules/ 外的所有修改 (1 file)
└── 010_vendor_modules.patch      # 专门包含 vendor/modules/ 的大量修改 (320 files)
```

正如您所见，Splitpatch 将一个复杂的大补丁转换成了一系列按模块组织的、更易于管理的小补丁。这使得分批审查、按功能应用或定位特定改动变得异常简单。

那么，Splitpatch 是如何实现这种 **智能分割** 的呢？让我们以上述命令 (`level=1`, `threshold=10`) 为例，一步步拆解它的工作流程：


### 原始补丁文件结构

这个补丁包含了分布在复杂目录结构中的多个文件修改。初始状态下，文件树如下所示（简化展示，仅显示部分结构）：

```
/
└── bsp
│   └── bootloader
│   │   └── lk
│   │       └── app
│   │       │   └── sprdboot (1 files)
│   │       └── platform
│   │       │   └── common (1 files)
│   │       │   │   └── include (1 files)
│   │       │   └── sprd_shared
│   │       │       └── driver
│   │       │           └── video
│   │       │               └── sprd (1 files)
│   │       │                   └── lcd (1 files)
│   │       └── project (1 files)
│   │       └── target
│   │           └── uis7885_2h10 (5 files)
│   └── kernel5.4
│       └── kernel5.4
│           └── arch
│           │   └── arm64
│           │       └── boot
│           │       │   └── dts
│           │       │       └── sprd (3 files)
│           │       └── configs (1 files)
│           └── drivers
│               └── input
│                   └── touchscreen (2 files)
│                       └── focaltech_touch (1 files)
└── build
    └── make
        └── core (1 files)
        └── target
        │   └── product (2 files)
        └── tools (2 files)
# ... 更多目录结构省略
└── vendor
    └── sprd
        └── modules
        │   └── libcamera (1 files)
        │       └── sensor
        │           └── af_drv (1 files)
        │           │   └── dw9714 (3 files)
        │           │   └── dw9800 (3 files)
        │           └── its_param
        │               └── qogirn6pro
        │                   └── Samsung
        │                   │   └── s5k3p9sx04 (1 files)
        │                   │   │   └── cap0 (11 files)
        │                   │   │   └── cap0_hdr (1 files)
        │                   │   │   └── cap0_zoom (4 files)
        │                   │   │   └── com (58 files)
        │                   │   │   └── other (5 files)
        │                   │   │   └── prv0 (6 files)
        │                   │   │   └── video0 (15 files)
        │                   │   └── s5k3p9sx04_main2 (1 files)
        │                   │   │   └── ... 类似结构，多个子目录
        │                   │   └── s5k4h7_front_main (1 files)
        │                   │       └── ... 类似结构
        └── release
            └── bmp
                └── unisoc_bmp (1 files)
```

这个结构展示了一个典型的复杂项目，改动分散且路径深。直接处理会非常困难。

### 第一阶段：识别模块与路径扁平化

Splitpatch 首先分析所有修改的文件路径，并基于目录结构初步识别逻辑单元。同时，它会进行路径扁平化，将一些在逻辑上属于同一子模块深层目录中的文件“上提”到更合理的层级。

在这个例子中，我们设置了 `level=1`，意味着所有第一级目录（如 `bsp/`, `build/`, `vendor/` 等）被视为重要的模块边界，不会合并到更高层次。

平展化处理后，文件树变为：

```
/
└── bsp
│   └── bootloader
│   │   └── lk
│   │       └── app
│   │       │   └── sprdboot (1 files)
│   │       └── platform
│   │       │   └── common (2 files)  # 合并了 include 下的文件
│   │       │   └── sprd_shared
│   │       │       └── driver
│   │       │           └── video
│   │       │               └── sprd (2 files) # 合并了 lcd 下的文件
# ... (省略) ...
│   └── kernel5.4
│       └── kernel5.4 # 注意这里仍有冗余层级
# ... (省略) ...
│                   └── touchscreen (3 files) # 合并了 focaltech_touch 下的文件
# ... (省略) ...
└── vendor
    └── sprd
        └── modules
        │   └── libcamera (320 files)  # 大量深层文件被合并到 libcamera 单元
        └── release
            └── bmp
                └── unisoc_bmp (1 files)
```

在此阶段，Splitpatch 已经开始合并一些文件，例如 `vendor/sprd/modules/libcamera` 下的 320 个文件被归到了相同的逻辑单元中。

### 第二阶段：路径优化

接下来，Splitpatch 进一步处理目录结构，**缩短**那些过深的、或者仅作为“通道”的路径层级。关键在于，它会 **尊重 `--level` 参数**。因为我们设置了 `level=1`，所以深度为 1 的目录（如 `bsp/`, `build/`, `vendor/`）及其直接路径不会被优化掉，保证了顶层模块结构的完整性。优化主要作用于更深的层级。

路径优化后，内部的文件树（逻辑表示）变得更加简洁：

```
/
└── bsp
│   └── bootloader
│   │   └── app (1 files) # lk/app/sprdboot 简化
│   │   └── platform
│   │   │   └── common (2 files)
│   │   │   └── sprd_shared (2 files) # driver/video/sprd 简化
│   │   └── project (1 files)
│   │   └── target (5 files) # uis7885_2h10 简化
│   └── kernel5.4 # kernel5.4/kernel5.4 简化为一层
│       └── arch
│       │   └── boot (3 files) # arm64/boot/dts/sprd 简化
│       │   └── configs (1 files)
│       └── drivers (3 files) # input/touchscreen 简化
└── build
│   └── make # 保持 make 层级
│       └── core (1 files)
│       └── target (2 files) # product 简化
│       └── tools (2 files)
# ... (省略) ...
└── vendor
    └── sprd # sprd 层级通常会保留
        └── modules (320 files) # libcamera 下的复杂结构大幅简化到 modules
        └── release (1 files) # bmp/unisoc_bmp 简化
```

通过路径优化，深层嵌套的改动被映射到了更易于理解和管理的目录层级上。

### 第三阶段：智能文件合并

最后一步是合并那些“零散”的改动。Splitpatch 会从最深的优化后路径开始，向上检查每个目录（及其子目录）包含的总文件修改数。

1.  **检查阈值 (`--threshold 10`)**：如果一个目录的总文件修改数 **小于 10**...
2.  **检查保护级别 (`--level 1`)**：**并且** 这个目录的深度 **大于 1** (即它不是 `bsp/`, `build/`, `vendor/` 这样的顶层目录)...
3.  **执行合并**：那么这个目录下的所有文件修改，就会被合并到其 **父目录** 的计数中，并且在最终生成补丁时归入父目录对应的 `.patch` 文件。

这个过程是递归的。例如，`vendor/sprd/release` 只有一个文件，小于 10，且深度大于 1，所以它会被合并到 `vendor/sprd`。但 `vendor/sprd` 连同 `modules`（320个文件）总数远超 10，所以 `vendor/sprd` 自身不会再向上合并。但是，由于 `vendor/sprd/modules` 包含 320 个文件，远超阈值 10，它会 **保持独立**，形成自己的 `vendor_modules.patch`。

最终，基于 `--level 1` 和 `--threshold 10` 的合并逻辑，形成了我们开头看到的那个文件计数和分组结果：

```
/
└── bsp (7 files)  # 合并了 kernel5.4 下的零散改动，但 bootloader 独立
│   └── bootloader (11 files) # 文件数 > 10，保持独立
└── build (5 files)
└── device (5 files)
└── external (1 files)
└── frameworks (4 files)
└── packages (3 files)
└── system (9 files)
└── vendor (1 files) # 合并了 release 的 1 个文件
    └── modules (320 files) # 文件数 > 10，保持独立
```

### 总结分析

通过这个实例，我们可以清晰地看到 Splitpatch 如何根据参数 `level=1` 和 `threshold=10` 工作：

1.  **尊重顶层结构 (`level=1`)**：`bsp/`, `build/`, `vendor/` 等一级目录始终被视为独立的分割单元，不会被合并。
2.  **保留重要子模块 (`threshold=10`)**：文件数量超过 10 的子目录（如 `bsp/bootloader` 和 `vendor/modules`）也被识别为重要的逻辑单元，单独生成补丁。
3.  **聚合零散改动**：文件数量少于 10 且深度大于 1 的目录下的改动，被智能地归并到其父级模块中，避免了过多琐碎的补丁文件。

这样，一个原本可能包含数百个文件、横跨数十个目录的庞大补丁，就被 Splitpatch 有条不紊地整理成了 10 个逻辑内聚、大小适中的补丁文件。这极大地简化了代码审查和补丁管理流程，让开发者可以更高效地处理复杂的代码变更。

## 贡献指南 (Contributing)

非常欢迎并感谢您对 `splitpatch` 的贡献！我们鼓励各种形式的参与，包括但不限于：

*   报告 Bug 或问题
*   提出功能建议或改进想法
*   提交代码修复或新功能实现
*   改进文档

如果您想要贡献，请遵循以下基本流程：

1.  **报告问题或建议功能**：
    *   请通过项目的 [GitHub Issues](https://github.com/chaoliu719/splitpatch/issues) 页面提交。
    *   对于 Bug 报告，请尽可能提供详细的复现步骤、环境信息以及您观察到的行为。
    *   对于功能建议，请清晰地描述您希望实现的功能及其使用场景。

2.  **提交代码或文档改进 (Pull Requests)**：
    *   如果您希望直接修复问题或实现新功能，我们非常欢迎 Pull Request。
    *   请先 Fork 本仓库到您的账户下，在完成修改并提交后，向本仓库的 `main` 提起 Pull Request，并在描述中清晰说明您所做的更改及其原因。

我们期待您的参与，共同让 `splitpatch` 变得更好！

## 许可证

本项目采用 MIT 许可证。详见 [LICENSE](LICENSE) 文件。
