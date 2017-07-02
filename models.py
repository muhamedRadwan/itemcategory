from sqlalchemy import create_engine, Column, String, Integer, ForeignKey, DateTime, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
Base = declarative_base()


class User(Base, UserMixin):
    __tablename__ = "user"
    name = Column(String(100), nullable=False)
    id = Column(Integer, primary_key=True)
    picture = Column(String)
    email = Column(String(100), nullable=False,unique=True)
    password_hash = Column(String, nullable=True)

    def hash_password(self, password):
        self.password_hash = generate_password_hash(password, method='sha256')

    def verify_pasword(self, password):
        return check_password_hash(self.password_hash, password)


class Category(Base):
    __tablename__ = "category"
    name = Column(String(100), nullable=False)
    id = Column(Integer, primary_key=True)


class ItemCategory(Base):
    __tablename__ = 'itemCatalog'
    name = Column(String(100), nullable=False)
    id = Column(Integer, primary_key=True)
    description = Column(String, nullable=False)
    created = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    user_id = Column(Integer, ForeignKey('user.id'))
    category_id = Column(Integer, ForeignKey('category.id'))
    user = relationship(User)
    category = relationship(Category)

    @property
    def sirlize(self):
        return {
            'name': self.name,
            'id': self.id,
            'description': self.description,
            'created': self.created,
            'user': self.user.name,
            'title': self.category.name
        }

engine = create_engine('sqlite:///ItemCatalog.db')
Base.metadata.create_all(engine)
