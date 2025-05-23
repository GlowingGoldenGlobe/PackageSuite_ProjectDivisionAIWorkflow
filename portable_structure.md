# Portable Division Structure for USB Deployment

## USB Stick Directory Layout

```
USB_ROOT/
├── GGG_Division_Installer.exe     # Main installer executable
├── README_PORTABLE.txt            # Quick start guide
├── autorun.inf                    # Auto-launch installer (optional)
│
├── installer/                     # Installer components
│   ├── installer.py              # Python installer script
│   ├── packages_manifest.json    # Package definitions
│   └── icons/                    # Installer icons
│
├── packages/                      # All packages organized by category
│   ├── user_invented/            # User's invented packages
│   │   ├── code_pre_api_compiler/
│   │   ├── error_handler/
│   │   ├── ai_automated_workflow/
│   │   ├── llm_filter/
│   │   ├── model_builder/
│   │   ├── simulation_generator/
│   │   ├── cloud_storage/
│   │   └── llm_memory_cpuo_system/
│   │
│   ├── core_packages/            # Essential project packages
│   │   ├── ai_managers/
│   │   ├── gui/
│   │   ├── utils/
│   │   └── cloud_storage/
│   │
│   └── optional_packages/        # Optional enhancements
│       ├── ros2_integration/
│       ├── open3d_integration/
│       └── blender_bridge/
│
├── dependencies/                  # Pre-downloaded dependencies
│   ├── python_packages/          # Python wheel files
│   │   ├── pyautogen-0.2.26-py3-none-any.whl
│   │   ├── anthropic-0.35.4-py3-none-any.whl
│   │   └── [other wheels...]
│   │
│   └── installers/              # External tool installers
│       ├── blender-4.2.3-windows-x64.msi
│       └── o3de-installer.exe
│
├── templates/                    # Division templates
│   ├── basic_division/          # Minimal setup
│   ├── full_division/           # Complete setup
│   └── custom_division/         # Customizable template
│
├── docs/                        # Documentation
│   ├── INSTALLATION_GUIDE.pdf
│   ├── QUICK_START.pdf
│   └── API_REFERENCE.pdf
│
└── tools/                       # Utility tools
    ├── dependency_checker.py
    ├── division_manager.py
    └── update_checker.py
```

## Setup Process Flow

1. **User inserts USB stick**
2. **Runs GGG_Division_Installer.exe**
3. **Installer shows dependencies window**
4. **User selects packages and configuration**
5. **Installer creates division structure**
6. **Dependencies installed from USB cache**
7. **Desktop shortcuts created**
8. **Division ready to use**

## Portable Features

- Self-contained installer with all dependencies
- Offline installation capability
- Pre-configured templates
- Automatic dependency resolution
- Cross-division compatibility
- Update mechanism included