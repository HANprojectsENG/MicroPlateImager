## @brief Makefile for doxygen documentation
## @author Gert van Lagen

DOCS_DIR ="./Documentation"

# create Doxygen documentation
.PHONY: docs
docs: clean-docs
	@echo "--Generate documentation by Doxygen--\n\n"
	$(shell doxygen Documentation/Doxyfile > /dev/null)
	@echo "--Documentation generated--\n\n"

# clean up generated doxygen html documentation
.PHONY: clean-docs
clean-docs:
	@echo "--Delete generated html documentation of Doxygen--\n"
	$(shell cd $(DOCS_DIR); if [ -d "html" ]; then rm -r html; cd ..; fi)
	@echo "--Deleted generated html documentation--\n"

.PHONY: open-docs
open-docs:
	@echo "--Opening Doxygen documentation using chromium-browser--\n"
	$(shell cd $(DOCS_DIR); if [ -d "html" ]; then chromium-browser ./html/index.html; else echo "--Failed opening index.html. No ./Documents/html/ directory found--\n\n"; fi)
