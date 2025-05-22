#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
models.py

Defines data structures used throughout the PDF processing pipeline.
These include:
- OutputParsed: Metadata returned from the OpenAI-based name generation
- FileDescriptor: Tracks files, including paths and classification info
"""

from pydantic import BaseModel, Field

class OutputParsed(BaseModel):
    """
    Represents the structured output from the document naming AI.

    Attributes:
        docType: The category/type of the document (e.g., 'Research Paper', 'Invoice').
        description: A concise summary of the document's content.
        newFileName: The suggested new file name.
        pathToFile: Relative path indicating the directory to save the renamed file in.
    """
    docType: str = Field(..., description="Type of document")
    description: str = Field(..., description="Concise summary of the document")
    newFileName: str = Field(..., description="Proposed new file name")
    pathToFile: str = Field(..., description="Target relative directory for the file")


class FileDescriptor(BaseModel):
    """
    Represents a record of a processed PDF file.

    Attributes:
        id: SHA256 hash of the original file (used as a unique identifier).
        oldFilePath: Original path to the source PDF file.
        newFilePath: Target path for the renamed and relocated file.
        docType: Type/category of the document.
        docDescription: Short summary of the document's content.
    """
    id: str = Field(..., description="SHA256 file hash used as unique ID")
    oldFilePath: str = Field(..., description="Path to original PDF")
    newFilePath: str = Field(..., description="Path where renamed file will be saved")
    docType: str = Field(..., description="Detected document type")
    docDescription: str = Field(..., description="Generated document summary")
