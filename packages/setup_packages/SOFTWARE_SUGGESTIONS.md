# Optional Software for GlowingGoldenGlobe Project

## Recommended Software (Not Included in Package Suite)

### 1. **O3DE (Open 3D Engine)**
- **Purpose**: Advanced 3D simulation and game engine
- **Platform**: Recommended on WSL2 Ubuntu (better package/tool availability)
- **Installation**: See O3DE_WSL2_SETUP_GUIDE.md

### 2. **Blender**
- **Purpose**: 3D modeling and animation for micro-robot components
- **Platform**: Windows or Linux
- **Website**: https://www.blender.org/
- **Note**: Project includes Blender Python API integration

### 3. **Open3D**
- **Purpose**: 3D data processing and visualization
- **Platform**: Cross-platform
- **Installation**: Use python310\python.exe for compatibility
- **Note**: Handled by upkgs.py in venv_setup package

### 4. **Visual Studio Code**
- **Purpose**: Primary development environment
- **Features**: 
  - Claude Code AI integration
  - Python debugging
  - Git integration
  - WSL2 remote development
- **Website**: https://code.visualstudio.com/

### 5. **WSL2 (Windows Subsystem for Linux 2)**
- **Purpose**: Linux environment on Windows
- **Recommended for**: O3DE installation and development
- **Distribution**: Ubuntu recommended
- **Benefits**: 
  - Better package availability
  - Native Linux toolchain
  - Seamless Windows integration

## Integration Notes

- The project is designed to work with all these tools
- Each tool enhances different aspects of the micro-robot development
- O3DE and Blender are particularly important for 3D simulation
- VSCode with Claude Code provides AI-assisted development
- WSL2 bridges Windows and Linux environments effectively

## Version Compatibility

- Python: 3.10+ (3.13+ for main environment, 3.10 for Open3D)
- Blender: 3.0+ (for Python API compatibility)
- O3DE: Latest stable release
- VSCode: Latest version with Claude Code extension
- WSL2: Latest Windows update includes WSL2

## Support

For installation help with any of these tools, consult:
- Copilot AI Assistant
- Official documentation for each tool
- Project-specific integration guides in docs/