"""
Application service package.

Services are imported explicitly by the modules that use them.
Avoid eager imports here because some services initialize
heavy dependencies such as PDF/AI libraries.
"""