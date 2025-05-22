import os
from typing import Optional

from openai import OpenAI
from models import OutputParsed

class NameChanger:
    """
    Uses OpenAI to analyze PDF content and generate metadata for renaming and classifying documents.
    """

    def __init__(self, api_key: Optional[str] = None, model_name: Optional[str] = None):
        """
        Initializes the NameChanger with an OpenAI client.

        Args:
            api_key: Optional API key. If not provided, attempts to read from the environment variable 'OPEN_API_KEY'.
        """
        self.client = OpenAI(api_key=api_key or os.getenv("OPEN_API_KEY"))
        self.model_name = model_name or os.getenv("MODEL_NAME")

    def process_document(self, text: str) -> OutputParsed:
        """
        Processes the input text and returns structured document metadata.

        Args:
            text: Extracted text content from a PDF file.

        Returns:
            An OutputParsed object containing docType, description, newFileName, and pathToFile.
        """
        instructions = """
        You are an expert librarian AI responsible for accurately classifying and summarizing academic and technical PDF documents based on excerpts from their initial pages.
        Your primary goal is to determine the correct `docType`, generate a concise `description`, and create a new relative file path (`newFileName` and `pathToFile`).

        **Output Field Definitions and Rules:**

        1.  **`docType`**: Classify the document into ONE of the following lowercase categories:
            * `textbook`: A comprehensive instructional book designed for a course of study or self-learning, often covering a subject systematically. Look for explicit mentions like 'book', 'textbook', chapter structures, exercises, or a preface describing its educational purpose.
            * `paper`: Look for terms like 'abstract', 'keywords', 'introduction', 'methodology', 'results', 'conclusion', 'references', author affiliations with research institutions. May also be called a 'research paper', 'academic paper', or 'scholarly article'.
            * `lecture_notes`: Materials prepared for a lecture or course, such as slides, instructor's notes, or detailed handouts. Often less formal than a textbook and may include course-specific information (e.g., 'CS101 Lecture 5').
            * `article`: A piece of writing included with others in a newspaper, magazine, or technical write-up that isn't a formal research paper, or other non-peer-reviewed publication. This is distinct from a scholarly `paper`.
            * `other`: Use this category ONLY if the document clearly does not fit any of the above categories (e.g., a technical manual, a dataset description, a standalone assignment sheet without lecture context, a form, a report not classifiable as a paper).

        2.  **`description`**: Provide a 2-3 sentence concise summary of the document's main topic and purpose based on the provided text.
            * **Crucially, you MUST include the primary author(s) name(s) and the publication year within the description.**
            * If multiple authors, list the primary ones or use 'et al.' if there are many (e.g., 'by Author One, Author Two, et al.').
            * If the year or author is not explicitly stated in the provided text, you MUST indicate this (e.g., 'Author not specified', 'Publication year not found in excerpt'). Do not invent this information.
            * Focus on what the document *is* or *does* (e.g., 'This paper presents...', 'This textbook covers...', 'These lecture notes explain...').

        3.  **`newFileName`**: Generate a concise, descriptive filename in `snake_case`.
            * Prefix the filename with the publication year (YYYY) and primary author's last name if clearly discernible. If not, omit the missing information.
            * The filename should reflect the document's content, often derived from its title or key concepts in the description.
            * For 'paper' type documents, try to include a key author's last name or a very short, unique identifier from the title in the filename if discernible and appropriate, after the year (e.g., '2021_authorname_short_paper_title.pdf').
            * Ensure all characters are ASCII.

        4.  **`pathToFile`**: Generate a relative path based *only* on the `docType`.
            * The path **must** be relative and always begin with './'. Do NOT include any absolute path or library root.
            * The path will be in the format './[docType]/', e.g., './textbook/', './paper/', './lecture_notes/', etc.

        **Decision Process for `docType`:**
        - Prioritize explicit cues in the text. For example, if the text says 'This book aims to...', it is likely a `textbook`.
        - If a document seems like a 'book' but is highly technical and research-focused, it might still be a 'textbook' if structured for learning, or a 'paper' if it's a monograph-length research report. Use your best judgment based on the definitions.
        - Differentiate `paper` (scholarly, research-focused) from `article` (more general, journalistic, or non-peer-reviewed content).
        - Only use `other` as a last resort.

        **Examples:**

        --- Example 1 ---
        Input Text Excerpt: "Grokking Deep Learning teaches you to build deep learning models from scratch. ... by Andrew W. Trask ... Foreword by ... Manning Publications Co. Copyright 2019."
        Output:
        {
        "docType": "textbook",
        "description": "'Grokking Deep Learning' by Andrew W. Trask (2019) is an introductory book that teaches how to build deep learning models from scratch. It is published by Manning Publications Co.",
        "newFileName": "2019_trask_grokking_deep_learning.pdf",
        "pathToFile": "./textbook/"
        }

        --- Example 2 ---
        Input Text Excerpt: "CS336 Assignment 1: Transformer Language Model ... Due: April 15, 2025 ... In this assignment, you will implement core components... Prepared by the CS336 Staff, Stanford University."
        Output:
        {
        "docType": "lecture_notes",
        "description": "This document outlines Assignment 1 for CS336, focusing on implementing a Transformer Language Model. It is prepared by the CS336 Staff at Stanford University for Spring 2025.",
        "newFileName": "cs336_assignment_1_transformer_language_model.pdf",
        "pathToFile": "./lecture_notes/"
        }

        --- Example 3 ---
        Input Text Excerpt: "Revisiting Simple Neural Probabilistic Language Models. ArXiv:2103.XXXXXv1 [cs.CL] 2 Mar 2021. John Doe, Jane Smith. Abstract: We investigate the surprising effectiveness of basic recurrent neural networks..."
        Output:
        {
        "docType": "paper",
        "description": "This research paper by John Doe and Jane Smith (2021), titled 'Revisiting Simple Neural Probabilistic Language Models', investigates the effectiveness of basic recurrent neural networks. It appears to be an ArXiv preprint.",
        "newFileName": "2021_doe_smith_revisiting_simple_nplms.pdf",
        "pathToFile": "./paper/"
        }

        --- Example 4 ---
        Input Text Excerpt: "The Art of Code: A Short Essay on Software Craftsmanship. By Developer Dave. Published on TechBlog.com, June 10, 2024. Today, I want to talk about elegance in code..."
        Output:
        {
        "docType": "article",
        "description": "This article by Developer Dave, published on TechBlog.com (2024), is a short essay discussing software craftsmanship and elegance in code.",
        "newFileName": "2024_dave_art_of_code.pdf",
        "pathToFile": "./article/"
        }
        """

        prompt = f"""
        Based on the instructions provided, please analyze the following text excerpt from the first ~20 pages of a PDF document and generate the `docType`, `description`, `newFileName`, and `pathToFile`.

        Text Excerpt:
        --------------------------------------------------
        {text}
        --------------------------------------------------
        """
        try:
            response = self.client.responses.parse(
                model=self.model_name,
                instructions=instructions,
                input=prompt,
                text_format=OutputParsed
            )
            return response.output_parsed
        except Exception as e:
            print(f"[ERROR] Failed to process document via OpenAI: {e}")
            raise
