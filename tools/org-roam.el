;;; org-roam.el --- Repository-local gpt-org-roam helper -*- lexical-binding: t; -*-

(require 'subr-x)

(defun gpt-org-roam--root ()
  "Return the repository root containing this helper."
  (file-truename
   (expand-file-name ".." (file-name-directory (or load-file-name buffer-file-name)))))

;;;###autoload
(defun gpt-org-roam-use-repository ()
  "Point Org-roam at this repository and synchronize its database."
  (interactive)
  (require 'org-roam)
  (setq org-roam-directory (gpt-org-roam--root))
  (org-roam-db-sync)
  (message "org-roam-directory -> %s" org-roam-directory))

(provide 'gpt-org-roam-helper)
;;; org-roam.el ends here
