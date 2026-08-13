;;; validate.el --- Validate gpt-org-roam -*- lexical-binding: t; -*-

(require 'cl-lib)
(require 'org)
(require 'org-element)
(require 'subr-x)

(defconst gpt-org-roam--root
  (file-truename
   (expand-file-name ".." (file-name-directory (or load-file-name buffer-file-name)))))

(defun gpt-org-roam--files (regexp)
  "Return repository files whose names match REGEXP."
  (directory-files-recursively gpt-org-roam--root regexp nil nil t))

(defun gpt-org-roam--org-files ()
  "Return all Org files in the repository."
  (gpt-org-roam--files "\\.org\\'"))

(defun gpt-org-roam--relative (file)
  "Return FILE relative to the repository root."
  (file-relative-name file gpt-org-roam--root))

(defun gpt-org-roam--scan-file (file)
  "Scan FILE and return a plist with :ids, :links, and :errors."
  (with-temp-buffer
    (insert-file-contents file)
    (org-mode)
    (let ((ids nil)
          (links nil)
          (errors nil)
          (relative (gpt-org-roam--relative file)))
      (let ((ast
             (condition-case err
                 (org-element-parse-buffer)
               (error
                (push (format "%s: Org parse error: %s"
                              relative
                              (error-message-string err))
                      errors)
                nil))))
        (when ast
          (org-element-map ast 'node-property
            (lambda (property)
              (when (string= (org-element-property :key property) "ID")
                (push (org-element-property :value property) ids))))
          (org-element-map ast 'link
            (lambda (link)
              (when (string= (org-element-property :type link) "id")
                (push (org-element-property :path link) links))))))
      (unless ids
        (push (format "%s: missing persistent :ID:" relative) errors))

      (goto-char (point-min))
      (let ((begins 0)
            (ends 0))
        (while (re-search-forward "^[ \t]*#\\+begin_src\\(?:[ \t].*\\)?$" nil t)
          (cl-incf begins))
        (goto-char (point-min))
        (while (re-search-forward "^[ \t]*#\\+end_src[ \t]*$" nil t)
          (cl-incf ends))
        (unless (= begins ends)
          (push (format "%s: unbalanced source blocks (%d begin, %d end)"
                        relative begins ends)
                errors)))

      (list :file relative
            :ids ids
            :links links
            :errors errors))))

(defun gpt-org-roam-validate ()
  "Validate the repository and exit non-zero on failure."
  (interactive)
  (let ((ids (make-hash-table :test #'equal))
        (links nil)
        (errors nil)
        (org-files (gpt-org-roam--org-files)))
    (dolist (file org-files)
      (let* ((scan (gpt-org-roam--scan-file file))
             (relative (plist-get scan :file)))
        (dolist (id (plist-get scan :ids))
          (puthash id (cons relative (gethash id ids)) ids))
        (dolist (id (plist-get scan :links))
          (push (cons id relative) links))
        (setq errors (nconc (plist-get scan :errors) errors))))

    (maphash
     (lambda (id files)
       (when (> (length files) 1)
         (push (format "duplicate ID %s: %s"
                       id
                       (string-join (reverse files) ", "))
               errors)))
     ids)

    (dolist (link links)
      (unless (gethash (car link) ids)
        (push (format "%s: broken id link -> %s" (cdr link) (car link)) errors)))

    (dolist (file (directory-files-recursively
                   (expand-file-name "tutorials" gpt-org-roam--root)
                   "\\.\\(?:md\\|markdown\\)\\'" nil nil t))
      (push (format "%s: Markdown tutorial is not allowed"
                    (gpt-org-roam--relative file))
            errors))

    (if errors
        (progn
          (princ "gpt-org-roam validation FAILED\n\n")
          (dolist (problem (sort errors #'string<))
            (princ (format "- %s\n" problem)))
          (kill-emacs 1))
      (princ (format "gpt-org-roam validation OK (%d Org files)\n"
                     (length org-files)))
      t)))

(provide 'gpt-org-roam-validate)
;;; validate.el ends here
