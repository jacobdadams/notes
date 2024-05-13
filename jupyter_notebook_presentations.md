## Export to html

jupyter nbconvert --to slides presentation_notebook.ipynb

## Export to pdf from html

jupyter nbconvert --to slides --post serve presentation_notebook.ipynb

This launches a local server hosting your slides. Add `?print-pdf` to the end of the file path in the browser (`http://127.0.0.1:8000/presentation.slides.html?print-pdf`). Ctrl-p to print, save as pdf, adjust margins if necessary.
