; ============================================
; Nixminds Document Suite - Modern Installer
; ============================================

!include "MUI2.nsh"
!include "FileFunc.nsh"

; ============================================
; Modern UI Configuration
; ============================================

; UI Settings
!define MUI_ABORTWARNING
!define MUI_UNABORTWARNING

; Icons (if present in build folder)
!define MUI_ICON "${BUILD_RESOURCES_DIR}\icon.ico"
!define MUI_UNICON "${BUILD_RESOURCES_DIR}\icon.ico"

; Header image (164x314 pixels recommended for sidebar)
!ifdef BUILD_RESOURCES_DIR
  !define MUI_WELCOMEFINISHPAGE_BITMAP "${BUILD_RESOURCES_DIR}\installerSidebar.bmp"
  !define MUI_UNWELCOMEFINISHPAGE_BITMAP "${BUILD_RESOURCES_DIR}\installerSidebar.bmp"
!endif

; Header image for other pages (150x57 pixels recommended)
!ifdef BUILD_RESOURCES_DIR
  !define MUI_HEADERIMAGE
  !define MUI_HEADERIMAGE_BITMAP "${BUILD_RESOURCES_DIR}\installerHeader.bmp"
  !define MUI_HEADERIMAGE_RIGHT
!endif

; ============================================
; Welcome Page
; ============================================
!define MUI_WELCOMEPAGE_TITLE "Welcome to Nixminds Document Suite"
!define MUI_WELCOMEPAGE_TEXT "This wizard will guide you through the installation of Nixminds Document Suite.$\r$\n$\r$\nNixminds Document Suite is a professional document anonymization tool that helps you protect sensitive information in your documents.$\r$\n$\r$\nFeatures:$\r$\n  - Automatic detection of personal data$\r$\n  - Smart anonymization with Czech name database$\r$\n  - Offline licensing - no internet required$\r$\n$\r$\nClick Next to continue."

; ============================================
; License Page (optional)
; ============================================
!define MUI_LICENSEPAGE_CHECKBOX

; ============================================
; Directory Page
; ============================================
!define MUI_DIRECTORYPAGE_TEXT_TOP "Setup will install Nixminds Document Suite in the following folder.$\r$\n$\r$\nTo install in a different folder, click Browse and select another folder."

; ============================================
; Install Files Page
; ============================================
!define MUI_INSTFILESPAGE_FINISHHEADER_TEXT "Installation Complete"
!define MUI_INSTFILESPAGE_FINISHHEADER_SUBTEXT "Setup has finished installing Nixminds Document Suite on your computer."

; ============================================
; Finish Page
; ============================================
!define MUI_FINISHPAGE_TITLE "Nixminds Document Suite Installed"
!define MUI_FINISHPAGE_TEXT "Nixminds Document Suite has been successfully installed on your computer.$\r$\n$\r$\nIMPORTANT: You will need to activate your license before first use. Contact your administrator for license details.$\r$\n$\r$\nClick Finish to close this wizard and start the application."
!define MUI_FINISHPAGE_RUN "$INSTDIR\${APP_EXECUTABLE_FILENAME}"
!define MUI_FINISHPAGE_RUN_TEXT "Launch Nixminds Document Suite"
!define MUI_FINISHPAGE_SHOWREADME ""
!define MUI_FINISHPAGE_SHOWREADME_NOTCHECKED
!define MUI_FINISHPAGE_SHOWREADME_TEXT "Create Desktop Shortcut"

; ============================================
; Uninstaller Pages
; ============================================
!define MUI_UNCONFIRMPAGE_TEXT_TOP "Nixminds Document Suite will be uninstalled from your computer.$\r$\n$\r$\nYour license and settings will be preserved for future installations."

; ============================================
; Custom Functions
; ============================================

Function .onInit
  ; Set default installation directory
  StrCpy $INSTDIR "$LOCALAPPDATA\Programs\${PRODUCT_NAME}"
FunctionEnd

; Show installation size on directory page
Function .onVerifyInstDir
  ; Allow any directory
FunctionEnd

; Custom finish page checkbox handler
Function CreateDesktopShortcut
  CreateShortcut "$DESKTOP\${PRODUCT_NAME}.lnk" "$INSTDIR\${APP_EXECUTABLE_FILENAME}"
FunctionEnd

; ============================================
; Installer Sections
; ============================================

Section "MainSection" SEC01
  SetOutPath "$INSTDIR"
  SetOverwrite on

  ; Files are automatically added by electron-builder
SectionEnd

Section -Post
  ; Create uninstaller
  WriteUninstaller "$INSTDIR\Uninstall.exe"

  ; Add to Add/Remove Programs
  WriteRegStr SHCTX "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_NAME}" "DisplayName" "${PRODUCT_NAME}"
  WriteRegStr SHCTX "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_NAME}" "UninstallString" "$INSTDIR\Uninstall.exe"
  WriteRegStr SHCTX "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_NAME}" "DisplayIcon" "$INSTDIR\${APP_EXECUTABLE_FILENAME}"
  WriteRegStr SHCTX "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_NAME}" "DisplayVersion" "${VERSION}"
  WriteRegStr SHCTX "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_NAME}" "Publisher" "Nixminds"

  ; Calculate and write install size
  ${GetSize} "$INSTDIR" "/S=0K" $0 $1 $2
  IntFmt $0 "0x%08X" $0
  WriteRegDWORD SHCTX "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_NAME}" "EstimatedSize" "$0"
SectionEnd
