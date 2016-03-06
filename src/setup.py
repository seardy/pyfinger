#!/usr/bin/env python
# -*- coding: utf-8 -*-

from distutils.core import setup

setup(
    name            = 'PyFingerprint',
    version         = '1.3', ## Never forget to change module version as well!
    description     = 'Python written library for using the ZFM-20 fingerprint sensor.',
    author          = 'Bastian Raschke',
    author_email    = 'bastian.raschke@posteo.de',
    url             = 'https://sicherheitskritisch.de',
    license         = 'D-FSL',
    package_dir     = {'': 'files'},
    packages        = ['pyfingerprint'],
)
