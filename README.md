# ocap

[![ocap](https://img.shields.io/pypi/v/ocap?label=ocap)](https://pypi.org/project/ocap/) [![gstreamer-bundle](https://img.shields.io/conda/vn/open-world-agents/gstreamer-bundle?label=gstreamer-bundle)](https://anaconda.org/open-world-agents/gstreamer-bundle)

High-performance desktop recorder for Windows. Captures screen, audio, keyboard, mouse, and window events.

https://github.com/user-attachments/assets/4e94782c-02ae-4f64-bb52-b08be69d33da

## What is ocap?

**ocap** (Omnimodal CAPture) captures all essential desktop signals in synchronized format. Records screen video, audio, keyboard/mouse input, and window events. Built for the _open-world-agents_ project but works for any desktop recording needs.

> **TL;DR**: Complete, high-performance desktop recording tool for Windows. Captures everything in one command.

📊 **Working with recorded data?** See the [Data Guide](https://open-world-agents.github.io/open-world-agents/data/) for analysis, processing, and ML integration.

## Key Features

- **Complete desktop recording**: Video, audio, keyboard/mouse events, window events
- **High performance**: Hardware-accelerated with Windows APIs and [GStreamer](https://gstreamer.freedesktop.org/)
- **Efficient encoding**: [H265/HEVC](https://en.wikipedia.org/wiki/High_Efficiency_Video_Coding) for high quality and small file size
- **Simple operation**: `ocap FILE_LOCATION` (stop with Ctrl+C)
- **Clean architecture**: Core logic in a single 400-line [recorder.py](https://github.com/open-world-agents/ocap/blob/main/owa/ocap/recorder.py)
- **Modern formats**: MKV with embedded timestamps, [**OWAMcap format**](https://open-world-agents.github.io/open-world-agents/data/) for events (built on [MCAP](https://mcap.dev/))

## System Requirements

Based on OBS Studio recommended specs + NVIDIA GPU requirements:

| Component | Specification |
|-----------|---------------|
| **OS** | Windows 11 (64-bit) |
| **Processor** | Intel i7 8700K / AMD Ryzen 1600X |
| **Memory** | 8 GB RAM |
| **Graphics** | **NVIDIA GeForce 10 Series or newer** ⚠️ |
| **DirectX** | Version 11 |
| **Storage** | 600 MB + ~100MB per minute recording |

> ⚠️ **NVIDIA GPU Required**: Currently only supports NVIDIA GPUs for hardware acceleration. AMD/Intel GPU support possible through GStreamer framework - **contributions welcome**!

> 🖥️ **OS Support**: Currently only supports Windows. However, support for other operating systems (Linux, macOS) can be relatively easily extended due to the presence of GStreamer. Simply using different GStreamer pipelines can enable capture on other platforms - **contributions welcome**!

## Installation & Usage

### Option 1: Download Release
1. Download `ocap.zip` from [releases](https://github.com/open-world-agents/ocap/releases)
2. Unzip and run:
    - Double-click `run.bat` (opens terminal with virtual environment)
    - Or in CLI: `run.bat --help`

### Option 2: Package Install

All OWA packages are available on PyPI:

```sh
# Install GStreamer dependencies first (for video recording)
$ conda install open-world-agents::gstreamer-bundle

# Install ocap
$ pip install ocap
```

### Basic Usage

```sh
# Start recording (stop with Ctrl+C)
$ ocap my-recording

# Show all options
$ ocap --help

# Advanced options
$ ocap FILENAME --window-name "App"   # Record specific window
$ ocap FILENAME --monitor-idx 1       # Record specific monitor
$ ocap FILENAME --fps 60              # Set framerate
$ ocap FILENAME --no-record-audio     # Disable audio
```

### Output Files
- `.mcap` — Event log (keyboard, mouse, windows) in [**OWAMcap format**](https://open-world-agents.github.io/open-world-agents/data/)
- `.mkv`  — Video/audio with embedded timestamps

Your recording files will be ready immediately!

## Feature Comparison

| **Feature**                              | **ocap**                 | [OBS](https://obsproject.com/) | [wcap](https://github.com/mmozeiko/wcap) | [pillow](https://github.com/python-pillow/Pillow)/[mss](https://github.com/BoboTiG/python-mss) |
|------------------------------------------|--------------------------|--------------------------------|------------------------------------------|----------------------------------|
| Advanced data formats ([OWAMcap](https://open-world-agents.github.io/open-world-agents/data/)/MKV) | ✅ Yes                   | ❌ No                          | ❌ No                                    | ❌ No                            |
| Timestamp aligned logging                | ✅ Yes                   | ❌ No                          | ❌ No                                    | ❌ No                            |
| Customizable event definition & Listener | ✅ Yes                   | ❌ No                          | ❌ No                                    | ❌ No                            |
| Single python file                       | ✅ Yes                   | ❌ No                          | ❌ No                                    | ❌ No                            |
| Audio + Window + Keyboard + Mouse        | ✅ Yes                   | ⚠️ Partial                    | ❌ No                                    | ❌ No                            |
| Hardware-accelerated encoder             | ✅ Yes                   | ✅ Yes                         | ✅ Yes                                   | ❌ No                            |
| Supports latest Windows APIs             | ✅ Yes                   | ✅ Yes                         | ✅ Yes                                   | ❌ No (legacy APIs only)         |
| Optional mouse cursor capture            | ✅ Yes                   | ✅ Yes                         | ✅ Yes                                   | ❌ No                            |

## Technical Architecture

Built on GStreamer with clean, maintainable design:

```mermaid
flowchart TD
    %% Input Sources
    A[owa.env.desktop] --> B[Keyboard Events]
    A --> C[Mouse Events] 
    A --> D[Window Events]
    E[owa.env.gst] --> F[Screen Capture]
    E --> G[Audio Capture]
    
    %% Core Processing
    B --> H[Event Queue]
    C --> H
    D --> H
    F --> H
    F --> I[Video/Audio Pipeline]
    G --> I
    
    %% Outputs
    H --> J[MCAP Writer]
    I --> K[MKV Pipeline]
    
    %% Files
    J --> L[📄 events.mcap]
    K --> M[🎥 video.mkv]
    
    style A fill:#e1f5fe
    style E fill:#e1f5fe
    style H fill:#fff3e0
    style L fill:#e8f5e8
    style M fill:#e8f5e8
```

- **Easy to verify**: Extensive [OWA's Env](../env/index.md) design enables customizable [`recorder.py`](https://github.com/open-world-agents/ocap/blob/main/owa/ocap/recorder.py)
- **Native performance**: Direct Windows API integration ([DXGI](https://learn.microsoft.com/en-us/windows/win32/direct3ddxgi/d3d10-graphics-programming-guide-dxgi)/[WGC](https://learn.microsoft.com/en-us/uwp/api/windows.graphics.capture?view=winrt-26100), [WASAPI](https://learn.microsoft.com/en-us/windows/win32/coreaudio/wasapi))

## Troubleshooting

- **Record terminates right after start?** Re-run the same command a few times. This is due to an intermittent GStreamer crash with an unknown cause.
- **GStreamer error message box appears on first run?** This is a known issue where GStreamer may show error dialogs the first time you run `ocap`. These messages do not affect recording—simply close the dialogs and continue. `ocap` will function normally.
- **Audio not recording?** By default, only audio from the target process is recorded. To change this, manually edit the [GStreamer pipeline](https://github.com/open-world-agents/open-world-agents/blob/main/projects/owa-env-gst/owa/env/gst/pipeline_builder/factory.py#L80).
- **Large file sizes?** Reduce file size by adjusting the [`gop-size`](https://gstreamer.freedesktop.org/documentation/nvcodec/nvd3d11h265enc.html?gi-language=c#nvd3d11h265enc:gop-size) parameter in the `nvd3d11h265enc` element. See [pipeline.py](https://github.com/open-world-agents/open-world-agents/blob/main/projects/owa-env-gst/owa/env/gst/pipeline_builder/pipeline.py).
- **Performance tips:** Close unnecessary applications before recording, use SSD storage for better write performance, and record to a different drive than your OS drive.

## FAQ

- **How much disk space do recordings use?** ~100MB per minute for 1080p H265 recording.
- **Will ocap slow down my computer?** Minimal impact with hardware acceleration. Designed for low overhead.
- **What is OWAMcap format?** A specialized format that stores screen video (.mkv) + synchronized events (.mcap) for AI training. Contains keyboard, mouse, window events with nanosecond precision. [Learn more →](https://open-world-agents.github.io/open-world-agents/data/)
- **How do I analyze recordings?** See the [Data Guide](https://open-world-agents.github.io/open-world-agents/data/) for analysis tools and examples.
- **Can I customize what gets recorded?** Yes. Use flags like `--no-record-audio`, `--window-name "App"`, `--fps 30` to control recording behavior.
- **How do I use recorded data for ML?** See the [Data Guide](https://open-world-agents.github.io/open-world-agents/data/) for processing pipelines and training examples.

## When to Use ocap

- **AI Agent Training**: Capture desktop interactions for training multimodal models
- **Workflow Documentation**: Record exact steps with precise timing
- **Performance Testing**: Low-overhead recording during intensive tasks
- **Research & Datasets**: Generate standardized [OWAMcap data](https://open-world-agents.github.io/open-world-agents/data/) for the community ([HuggingFace Hub](https://huggingface.co/datasets?other=OWA))
