TEX=Lab2Report.tex
PDF=Lab2Report.pdf

LATEXMK=latexmk
COMMON_FLAGS=-pdf -interaction=nonstopmode -file-line-error

.PHONY: all with-images without-images watch clean

all: with-images

with-images:
	$(LATEXMK) $(COMMON_FLAGS) "$(TEX)"

without-images:
	$(LATEXMK) $(COMMON_FLAGS) -jobname=Lab2Report-noimg -pdflatex='pdflatex %O "\\def\\NOIMAGES{1}\\input{%S}"' "$(TEX)"

watch:
	$(LATEXMK) $(COMMON_FLAGS) -pvc "$(TEX)"

clean:
	$(LATEXMK) -c "$(TEX)"
	rm -f Lab2Report-noimg.pdf Lab2Report-noimg.aux Lab2Report-noimg.log Lab2Report-noimg.out Lab2Report-noimg.fdb_latexmk Lab2Report-noimg.fls
