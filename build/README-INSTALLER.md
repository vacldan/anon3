# Nixminds Document Suite - Modern Installer Setup

## Required Files

Place these files in the `build/` folder:

### 1. icon.ico (Required)
Main application icon - used for:
- Application executable
- Desktop shortcut
- Start menu
- Taskbar
- Installer/Uninstaller

**Requirements:**
- Format: ICO (Windows Icon)
- Recommended sizes included: 256x256, 128x128, 64x64, 48x48, 32x32, 16x16
- Color depth: 32-bit (with transparency)

**How to create from your eye image:**

**Option A - Online (easiest):**
1. Go to https://convertico.com/ or https://icoconvert.com/
2. Upload your eye PNG/JPG image
3. Select all sizes (16, 32, 48, 64, 128, 256)
4. Download and save as `build/icon.ico`

**Option B - Using GIMP (free):**
1. Open GIMP (https://www.gimp.org/)
2. Open your eye image
3. Image > Scale Image > 256x256
4. File > Export As > icon.ico
5. In dialog, select all icon sizes

**Option C - Using ImageMagick (command line):**
```bash
magick convert eye.png -resize 256x256 -define icon:auto-resize=256,128,64,48,32,16 icon.ico
```

### 2. installerSidebar.bmp (Optional - for modern look)
Sidebar image shown on Welcome and Finish pages.

**Requirements:**
- Format: BMP (Windows Bitmap)
- Size: 164x314 pixels
- Color depth: 24-bit

**How to create:**
1. Create a 164x314 pixel image
2. Use your brand colors (suggested: dark blue gradient #1a237e to #3949ab)
3. Add your eye logo in the center
4. Add "Nixminds" text at bottom
5. Save as 24-bit BMP

### 3. installerHeader.bmp (Optional - for modern look)
Header image shown on Directory and other pages.

**Requirements:**
- Format: BMP (Windows Bitmap)
- Size: 150x57 pixels
- Color depth: 24-bit

**How to create:**
1. Create a 150x57 pixel image
2. Use matching brand colors
3. Add small eye logo on the right
4. Save as 24-bit BMP

---

## Quick Modern Look (Without Custom Images)

If you don't want to create custom BMP images, the installer will still look better than default with just the icon.ico file. The MUI2 (Modern UI 2) theme provides:
- Cleaner fonts
- Better spacing
- Professional text
- Proper branding

---

## Color Suggestions for Brand Consistency

Based on typical "eye" themed branding:

| Element | Color | Hex |
|---------|-------|-----|
| Primary | Deep Blue | #1a237e |
| Secondary | Light Blue | #3949ab |
| Accent | Teal | #00897b |
| Background | White | #ffffff |
| Text | Dark Gray | #212121 |

---

## Testing the Installer

After creating the files, rebuild:

```cmd
cd C:\Nixminds\nixminds-anonymizer
rmdir /s /q dist
npm run dist
```

The new installer will be at:
`dist\Nixminds Document Suite-Setup-3.0.0.exe`
