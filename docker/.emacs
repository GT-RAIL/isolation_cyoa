(setq inhibit-splash-screen t)
(setq-default indent-tabs-mode nil)
(setq-default tab-width 4)
(defalias 'yes-or-no-p 'y-or-n-p)
(setq c-default-style "linux"
          c-basic-offset 4)
(setq backup-directory-alist `(("." . "~/.saves")))
(setq backup-by-copying t)
(setq delete-old-versions t
  kept-new-versions 6
  kept-old-versions 2
  version-control t)
(custom-set-variables
 ;; custom-set-variables was added by Custom.
 ;; If you edit it by hand, you could mess it up, so be careful.
 ;; Your init file should contain only one such instance.
 ;; If there is more than one, they won't work right.
 '(nxhtml-autoload-web nil t)
 '(package-selected-packages (quote (markdown-mode))))
(custom-set-faces
 ;; custom-set-faces was added by Custom.
 ;; If you edit it by hand, you could mess it up, so be careful.
 ;; Your init file should contain only one such instance.
 ;; If there is more than one, they won't work right.
 )

;; Add YAML to the load path
;; (add-to-list 'load-path "~/.emacs.d/yaml/")
;; (require 'yaml-mode)
;; (add-to-list 'auto-mode-alist '("\\.yml$" . yaml-mode))
;; (add-to-list 'auto-mode-alist '("\\.yaml$" . yaml-mode))

;; Allow the use of the MELPA repos for downloading packages
(require 'package)
(add-to-list 'package-archives
             '("melpa-stable" . "https://stable.melpa.org/packages/"))
(package-initialize)

;; Fetch el-get in order to install other emacs dependencies
;; (add-to-list 'load-path "~/.emacs.d/el-get/el-get")

;; (unless (require 'el-get nil 'noerror)
;;   (with-current-buffer
;;       (url-retrieve-synchronously
;;        "https://raw.githubusercontent.com/dimitri/el-get/master/el-get-install.el")
;;     (goto-char (point-max))
;;     (eval-print-last-sexp)))
;;
;; (add-to-list 'el-get-recipe-path "~/.emacs.d/el-get-user/recipes")
;; (el-get 'sync)

;; Install Jedi python autocomplete
;; Standard Jedi.el setting
;; (add-hook 'python-mode-hook 'jedi:setup)
;; (setq jedi:complete-on-dot t)
;; (setq jedi:server-command '("/usr/local/lib/python2.7/dist-packages/jediepcserver"))
;; (add-hook 'python-mode-hook 'jedi:setup)
