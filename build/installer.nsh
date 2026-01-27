; Modern installer customization
!include "MUI2.nsh"

; Modern UI Settings
!define MUI_ABORTWARNING
!define MUI_ICON "${BUILD_RESOURCES_DIR}\icon.ico"
!define MUI_UNICON "${BUILD_RESOURCES_DIR}\icon.ico"

; Modern colors (blue gradient theme)
!define MUI_BGCOLOR 0xF5F7FA
!define MUI_TEXTCOLOR 0x2C3E50

; Welcome page customization
!define MUI_WELCOMEPAGE_TITLE "Nixminds Document Suite Installer"
!define MUI_WELCOMEPAGE_TEXT "This wizard will guide you through the installation.$\r$\n$\r$\nNixminds Document Suite is a professional document anonymization tool with offline licensing.$\r$\n$\r$\nClick Next to continue."

; Finish page customization
!define MUI_FINISHPAGE_TITLE "Installation Complete"
!define MUI_FINISHPAGE_TEXT "Nixminds Document Suite has been successfully installed.$\r$\n$\r$\nYou will need to activate your license before first use.$\r$\n$\r$\nClick Finish to close this wizard."
!define MUI_FINISHPAGE_RUN "$INSTDIR\${APP_EXECUTABLE_FILENAME}"
!define MUI_FINISHPAGE_RUN_TEXT "Launch Nixminds Document Suite"

; Header customization
!define MUI_HEADERIMAGE
!define MUI_HEADERIMAGE_RIGHT
!define MUI_HEADERIMAGE_BITMAP_NOSTRETCH

; Custom page text
!define MUI_TEXT_WELCOME_INFO_TITLE "Welcome to Nixminds Document Suite Setup"
!define MUI_TEXT_WELCOME_INFO_TEXT "This Setup will guide you through the installation.$\r$\n$\r$\nIt is recommended that you close all other applications before starting Setup. This will make it possible to update relevant system files without having to reboot your computer.$\r$\n$\r$\n$_CLICK"

; Directory page customization
!define MUI_TEXT_DIRECTORY_TITLE "Choose Install Location"
!define MUI_TEXT_DIRECTORY_SUBTITLE "Choose the folder in which to install Nixminds Document Suite."

; Components page (if needed)
!define MUI_COMPONENTSPAGE_SMALLDESC

; Installation progress
!define MUI_INSTFILESPAGE_FINISHHEADER_TEXT "Installation Completed Successfully"
!define MUI_INSTFILESPAGE_FINISHHEADER_SUBTEXT "Setup has finished installing Nixminds Document Suite on your computer."

; Modern progress bar style
!define MUI_INSTFILESPAGE_PROGRESSBAR "smooth"
