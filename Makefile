EMACS ?= emacs

.PHONY: validate
validate:
	$(EMACS) --batch -Q --load tools/validate.el --funcall gpt-org-roam-validate
