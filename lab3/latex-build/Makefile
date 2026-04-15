TEX=Lab3Report.tex
PDF=Lab3Report.pdf

LATEXMK=latexmk
COMMON_FLAGS=-pdf -interaction=nonstopmode -file-line-error

.PHONY: all with-images without-images watch clean

all: with-images

with-images:
	$(LATEXMK) $(COMMON_FLAGS) "$(TEX)"

without-images:
	$(LATEXMK) $(COMMON_FLAGS) -jobname=Lab3Report-noimg -pdflatex='pdflatex %O "\\def\\NOIMAGES{1}\\input{%S}"' "$(TEX)"

watch:
	$(LATEXMK) $(COMMON_FLAGS) -pvc "$(TEX)"

clean:
	$(LATEXMK) -c "$(TEX)"
	rm -f Lab3Report-noimg.pdf Lab3Report-noimg.aux Lab3Report-noimg.log Lab3Report-noimg.out Lab3Report-noimg.fdb_latexmk Lab3Report-noimg.fls
