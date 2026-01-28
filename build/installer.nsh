; ============================================
; Nixminds Document Suite - Simple Installer
; ============================================
; NOTE: Keep this file SIMPLE to avoid memory errors!

!include "MUI2.nsh"

; Basic UI Settings
!define MUI_ABORTWARNING

; Welcome page text
!define MUI_WELCOMEPAGE_TITLE "Nixminds Document Suite"
!define MUI_WELCOMEPAGE_TEXT "Vitejte v instalaci Nixminds Document Suite.$\r$\n$\r$\nTento program anonymizuje citlive udaje v dokumentech.$\r$\n$\r$\nKliknete Dalsi pro pokracovani."

; Finish page text
!define MUI_FINISHPAGE_TITLE "Instalace dokoncena"
!define MUI_FINISHPAGE_TEXT "Nixminds Document Suite byl uspesne nainstalovan.$\r$\n$\r$\nPRO AKTIVACI: Umistete soubor license.lic do slozky s aplikaci."
