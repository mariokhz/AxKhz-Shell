#!/bin/bash


image="$HOME/.config/Ax-Shell/assets/notify-icons/ocr.png"

 
# Take a screenshot and perform OCR
ocr_text=$(grimblast --freeze save area - | tesseract -l spa - - 2>/dev/null)

# Check if OCR was successful
if [[ -n "$ocr_text" ]]; then
    echo -n "$ocr_text" | wl-copy
    notify-send -a "Ax-Shell" "OCR Success" "Text Copied to Clipboard" -i $image
else
    notify-send -a "Ax-Shell" "OCR Failed" "No text recognized or operation failed"
fi
