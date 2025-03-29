# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

import os
import sys

# Add the parent directory to the Python path so that Sphinx can find and import
# the modules in our package for autodoc generation. This allows the documentation
# to include API references generated directly from the source code.
sys.path.insert(0, os.path.abspath('..'))

project = 'langchain-couchbase'
copyright = '2025, Nithish Raghunandanan'
author = 'Nithish Raghunandanan'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = ["sphinx.ext.todo", "sphinx.ext.viewcode", "sphinx.ext.autodoc", 'sphinx.ext.intersphinx']

# Intersphinx configuration
intersphinx_mapping = {
    'python': ('https://docs.python.org/3', None),
    'couchbase': ('https://docs.couchbase.com/python-sdk/current/', None),
}
intersphinx_missing_references = "warn" # Ensure warnings are still shown for missing refs

# Suppress specific nitpicky warnings
nitpick_ignore = [
    ('py:class', 'couchbase.cluster.Cluster'),  # Ignore missing Cluster type from couchbase lib
    ('py:class', 'Cluster'),  # Also ignore if referenced without full path
]

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']



# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']
