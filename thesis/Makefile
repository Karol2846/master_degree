LATEXMK ?= latexmk

.PHONY: pdf watch clean

pdf:            ## zbuduj build/main.pdf
	$(LATEXMK)

watch:          ## przebudowuj po każdym zapisie pliku
	$(LATEXMK) -pvc -view=none

clean:          ## usuń katalog build/
	rm -rf build
