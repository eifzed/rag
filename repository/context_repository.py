
from models.context_model import Context
from fastapi import HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from sqlalchemy import delete



class ContextRepository:
    @staticmethod
    def get_by_id_and_owner(db:Session, context_id, owner_id):
        return db.query(Context).filter(
            Context.id == context_id,
            Context.owner_id == owner_id
        ).first()
    
    @staticmethod
    def get_by_owner_and_name(db:Session, name, user_id):
        return db.query(Context).filter(
            Context.name == name,
            Context.owner_id == user_id
        ).first()
    
    @staticmethod
    def create(db:Session, context: Context):
        db.add(context)
        db.commit()
        db.refresh(context)
        return context
    
    @staticmethod
    def get_by_owner(db:Session,  owner_id, name: Optional[str]=None):
        q = db.query(Context)
        if not name:
            q = q.filter(Context.owner_id==owner_id)
        else:
            q = q.filter(Context.owner_id==owner_id, Context.name.ilike(f'%{name}%'))
        
        return q.all()
    
    @staticmethod
    def delete_by_id(db:Session,  id):
        db.execute(delete(Context).where(Context.id == id))


    
