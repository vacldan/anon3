# Build Assets

## Icon File

To build the installer with your custom icon, you need to create `build/icon.ico`.

### Creating the Icon

1. **Download eye icon** from a free icon resource:
   - [Flaticon](https://www.flaticon.com/search?word=eye)
   - [Icons8](https://icons8.com/icons/set/eye)
   - [Iconfinder](https://www.iconfinder.com/search/?q=eye&price=free)

2. **Convert to .ico format** using online tools:
   - [ConvertICO](https://convertico.com/)
   - [ICO Convert](https://icoconvert.com/)
   - [Cloud Convert](https://cloudconvert.com/png-to-ico)

3. **Save as** `build/icon.ico` (this exact path and name)

### Requirements

- Format: `.ico`
- Recommended size: 256x256px
- Must include at least: 16x16, 32x32, 48x48, 256x256 sizes in the .ico file

## Installer Script

The `installer.nsh` file contains custom NSIS installer configuration for modern UI.
