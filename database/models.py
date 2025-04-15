"""
Database models for Book Knowledge AI application.
Provides data models for database tables.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Union
from datetime import datetime

@dataclass
class Book:
    """Model representing a book in the database."""
    
    title: str
    author: str
    categories: List[str] = field(default_factory=list)
    file_path: Optional[str] = None
    content_length: Optional[int] = None
    date_added: datetime = field(default_factory=datetime.now)
    last_modified: datetime = field(default_factory=datetime.now)
    id: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the book model to a dictionary."""
        return {
            'id': self.id,
            'title': self.title,
            'author': self.author,
            'categories': self.categories,
            'file_path': self.file_path,
            'content_length': self.content_length,
            'date_added': self.date_added.isoformat() if self.date_added else None,
            'last_modified': self.last_modified.isoformat() if self.last_modified else None,
            'metadata': self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Book':
        """Create a Book instance from a dictionary."""
        # Convert date strings to datetime objects
        date_added = data.get('date_added')
        if isinstance(date_added, str):
            date_added = datetime.fromisoformat(date_added)
        
        last_modified = data.get('last_modified')
        if isinstance(last_modified, str):
            last_modified = datetime.fromisoformat(last_modified)
        
        return cls(
            id=data.get('id'),
            title=data.get('title', ''),
            author=data.get('author', ''),
            categories=data.get('categories', []),
            file_path=data.get('file_path'),
            content_length=data.get('content_length'),
            date_added=date_added or datetime.now(),
            last_modified=last_modified or datetime.now(),
            metadata=data.get('metadata', {})
        )

@dataclass
class BookContent:
    """Model representing a book's content in the database."""
    
    book_id: int
    content: str
    format: str = "text"
    extracted_at: datetime = field(default_factory=datetime.now)
    id: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the book content model to a dictionary."""
        return {
            'id': self.id,
            'book_id': self.book_id,
            'content': self.content,
            'format': self.format,
            'extracted_at': self.extracted_at.isoformat() if self.extracted_at else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BookContent':
        """Create a BookContent instance from a dictionary."""
        # Convert date strings to datetime objects
        extracted_at = data.get('extracted_at')
        if isinstance(extracted_at, str):
            extracted_at = datetime.fromisoformat(extracted_at)
        
        return cls(
            id=data.get('id'),
            book_id=data.get('book_id'),
            content=data.get('content', ''),
            format=data.get('format', 'text'),
            extracted_at=extracted_at or datetime.now()
        )

@dataclass
class Category:
    """Model representing a category in the database."""
    
    name: str
    description: Optional[str] = None
    parent_id: Optional[int] = None
    id: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the category model to a dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'parent_id': self.parent_id
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Category':
        """Create a Category instance from a dictionary."""
        return cls(
            id=data.get('id'),
            name=data.get('name', ''),
            description=data.get('description'),
            parent_id=data.get('parent_id')
        )

@dataclass
class KnowledgeBaseEntry:
    """Model representing a knowledge base entry in the database."""
    
    book_id: int
    added_at: datetime = field(default_factory=datetime.now)
    is_indexed: bool = False
    last_indexed: Optional[datetime] = None
    chunk_count: int = 0
    id: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the knowledge base entry model to a dictionary."""
        return {
            'id': self.id,
            'book_id': self.book_id,
            'added_at': self.added_at.isoformat() if self.added_at else None,
            'is_indexed': self.is_indexed,
            'last_indexed': self.last_indexed.isoformat() if self.last_indexed else None,
            'chunk_count': self.chunk_count
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'KnowledgeBaseEntry':
        """Create a KnowledgeBaseEntry instance from a dictionary."""
        # Convert date strings to datetime objects
        added_at = data.get('added_at')
        if isinstance(added_at, str):
            added_at = datetime.fromisoformat(added_at)
        
        last_indexed = data.get('last_indexed')
        if isinstance(last_indexed, str):
            last_indexed = datetime.fromisoformat(last_indexed)
        
        return cls(
            id=data.get('id'),
            book_id=data.get('book_id'),
            added_at=added_at or datetime.now(),
            is_indexed=data.get('is_indexed', False),
            last_indexed=last_indexed,
            chunk_count=data.get('chunk_count', 0)
        )