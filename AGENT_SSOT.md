# 🤖 PIXELPILOT: AI AGENT OPERATING INSTRUCTIONS

> **SYSTEM OVERRIDE DIRECTIVE:** You are a Senior Qt/C++ Software Architect. You are working in a multi-model environment where other AIs will touch this code after you. You MUST read and obey this document.

## 1. 🏷️ THE AI SEMANTIC TAGGING PROTOCOL
When reading or writing code in this repository, you must obey and utilize these tags in comments:
* `@AI-LOCKED`: **[RESTRICTIVE]** Do not modify this logic. It exists for a specific OS-level reason (e.g., KDE Wayland quirks). Ask the user before modifying.
* `@AI-CONTRACT`: **[CAUTION]** This is a rigid interface or architectural rule. If you change this, you MUST update all connected systems.
* `@AI-FREE`: **[FREEDOM]** Internal implementation logic. You are free to optimize and refactor this (e.g., optimizing an OpenCV matrix transformation).

## 2. 🏛️ CURRENT `@AI-CONTRACT` BOUNDARIES (Do Not Break)
* **UI Framework:** Qt Quick (QML) ONLY. NEVER suggest or use `QWidget` or `.ui` files.
* **Wayland Capture:** NEVER use `QScreen::grabWindow` or `QPixmap::grabWindow` (they fail on Wayland). You MUST route all screen capture through the `WaylandGrabber` class (PipeWire/XDG).
* **Threading (OpenCV):** NEVER run OpenCV image processing on the Main/GUI Thread. You MUST push frames to a worker thread or use `QtConcurrent`.
* **The Node Graph:** Connections (Wires) between nodes represent purely BOOLEAN (true/false) signals. Green = True, Red = False. Signal propagation must be immediate.
* **State Management:** All global variables and states are stored in the C++ `GlobalVarManager`. NEVER store business logic or global state in QML/JavaScript.
* **Signal Syntax:** You MUST use Qt 6 function-pointer syntax: `connect(sender, &Class::signal, receiver, &Class::slot);`. NO old macros.
* **Build Structure:** ALL build artifacts MUST live in the `build/` directory. Use subfolders for different environments: `build/dev`, `build/test`, `build/pkg`.
* **Binary Distribution:** Compiled binaries and `.deb` packages MUST NOT be committed to the repository. They are strictly for GitHub Releases. Final versions are staged in `build/pkg/`.

## 3. 🛑 PRE-FLIGHT CHECKLIST (MANDATORY)
Before you write or modify ANY code, you MUST output a brief plan formatted exactly like this:
1. **Goal:** (What are you trying to do?)
2. **Blast Radius:** (Which `@AI-CONTRACT` boundaries am I touching? Am I affecting the Wayland compositor or the QML render loop?)
3. **Execution Plan:** (Brief step-by-step).

## 4. 🗺️ ARCHITECTURE MAP & STANDARDS
* **Language:** C++20. Default to smart pointers (`std::unique_ptr`, `std::shared_ptr`).
* **Pattern (MVVM):** QML handles ONLY presentation. C++ handles heavy logic, OpenCV, and OS interaction. Glue them using `Q_PROPERTY`, `Q_INVOKABLE`, and `signals`.
* **Event-Driven Core:** The system is NOT a busy loop. It reacts to `frameReady()` signals. NO `QThread::msleep()` in the main thread.
* **Naming:** Classes = `PascalCase` (`WaylandGrabber`). Vars/Funcs/QML IDs = `camelCase` (`startCapture()`, `startBtn`).

## 5. 📖 CHANGELOG / AI MEMORY
* *[Memory]*: Established multi-OS Docker build pipeline to resolve Arch Linux bleeding-edge `glibc` mismatch.
* *[Memory]*: Implemented headless Wayland DBus session bypass for AI compilation testing.
* *[Memory]*: Injected initial @AI-CONTRACT and @AI-LOCKED tags across the C++ and QML codebase.
* *[Memory]*: Standardized and verified semantic tagging framework deployment across Wayland grabber and NodeGraph components.
* *[Memory]*: Refactored build system to use a centralized `build/` folder and established a "No Binaries in Repo" policy for GitHub Releases.

## 6. 🎯 CURRENT TASK


## 7. 🚀 BUILD & RUN (Testing your changes)
To verify that your C++ code compiles, your QML syntax is correct, and the Docker image builds successfully, you MUST run the automated validation script. This script runs synchronously in an `offscreen` headless Qt mode and will safely exit without blocking your terminal.

**Run this command to test your changes:**
`./ai-build-test.sh`

## 8. 🧹 AI CLEANUP PROTOCOL (MANDATORY)
When you have successfully completed the Current Task:
1. **Update Memory:** Add a 1-sentence bullet point to Section 5 summarizing what you built.
2. **Clear the Task:** Delete the contents of Section 6 and leave it blank for the next agent.

