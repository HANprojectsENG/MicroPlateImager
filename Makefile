#Makefile for doxygen documentation

DOCS_DIR = "./Documentation"

# run program with python3
.PHONY: run
run:
	@echo "--Running software with python3 main.py--\n\n"
	$(shell if [ -f "./main.py" ]; then python3 main.py; else echo "No such file: main.py\n"; fi)

# create Doxygen documentation
.PHONY: docs
docs: clean-docs
	@echo "--Generate documentation by Doxygen--\n"
	$(shell cd $(DOCS_DIR); doxygen > /dev/null 2>&1)
	@echo "--Generated documentation --\n"

# clean up generated doxygen html documentation
.PHONY: clean-docs
clean-docs:
	@echo "--Delete generated html documentation of Doxygen--\n"
	$(shell cd $(DOCS_DIR); if [ -d "html" ]; then rm -r html; fi)
	@echo "--Deleted generated html documentation--\n"

.PHONY: open-docs
open-docs:
	@echo "--Opening Doxygen documentation using chromium-browser--\n"
	$(shell cd $(DOCS_DIR); if [ -d "html" ]; then chromium-browser ./html/index.html; else echo "--Failed opening index.html. No ./Documents/html/ directory found--\n\n"; fi)
