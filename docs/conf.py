# Configuration file for the Sphinx documentation builder.

import os
import sys
import django

sys.path.insert(0, os.path.abspath('..'))
os.environ['DJANGO_SETTINGS_MODULE'] = 'LorenaNewsApp.settings'
django.setup()

# -- Project information -----------------------------------------------------

project = 'LorenaNewsApp'
copyright = '2026, Loredana Draghin'
author = 'Loredana Draghin'
release = '1.0'

# -- General configuration ---------------------------------------------------

extensions = ['sphinx.ext.autodoc']

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

# -- Options for HTML output -------------------------------------------------

html_theme = 'furo'
html_static_path = ['_static']