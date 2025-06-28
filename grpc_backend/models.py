from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from grpc_backend.db import Base

class File(Base):
    __tablename__ = "files"
    print("📋 Tables:")
    id = Column(Integer, primary_key=True)
    file_name = Column(String, unique=True)
    uploaded_at = Column(DateTime, default=datetime.now)
    size_bytes = Column(Integer, nullable=True)
    uploaded_path = Column(String, nullable=True)
    converted_path = Column(String, nullable=True)

    tags = relationship("DicomTag", back_populates="file", cascade="all, delete")

class DicomTag(Base):
    __tablename__ = "dicom_tags"
    print("📋 Tags:")
    id = Column(Integer, primary_key=True)
    file_id = Column(Integer, ForeignKey("files.id"))
    names = Column(String) #attribute name
    value = Column(Text)
    tag = Column(String) 
    file = relationship("File", back_populates="tags")

