#!/bin/bash

# Take a screenshot and perform OCR
ocr_text=$(grimblast --freeze save area - | wl-copy | /home/khz/Programas/LatexOCR.sh 2>/dev/null)

