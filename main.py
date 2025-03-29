from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from database import SessionLocal, engine
from models import Base, Usuario

# Crear las tablas
Base.metadata.create_all(bind=engine)

app = FastAPI()

# Dependency para obtener la sesión de la base de datos
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ✔️ Obtener todos los usuarios
@app.get("/usuarios", response_model=list[dict])
def get_usuarios(db: Session = Depends(get_db)):
    usuarios = db.query(Usuario).all()
    return usuarios

# ✔️ Crear un nuevo usuario
@app.post("/usuarios", response_model=dict)
def create_usuario(nombre: str, email: str, lastname: str, db: Session = Depends(get_db)):
    usuario = Usuario(nombre=nombre, email=email, lastname=lastname)
    db.add(usuario)
    db.commit()
    db.refresh(usuario)
    return {"message": "Usuario creado", "id": usuario.id}

# ✔️ Obtener un usuario por ID
@app.get("/usuarios/{usuario_id}", response_model=dict)
def get_usuario(usuario_id: int, db: Session = Depends(get_db)):
    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return usuario

# ✔️ Actualizar un usuario
@app.put("/usuarios/{usuario_id}", response_model=dict)
def update_usuario(usuario_id: int, nombre: str, email: str, lastname: str, db: Session = Depends(get_db)):
    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    usuario.nombre = nombre
    usuario.email = email
    usuario.lastname = lastname
    db.commit()
    return {"message": "Usuario actualizado"}

# ✔️ Eliminar un usuario
@app.delete("/usuarios/{usuario_id}", response_model=dict)
def delete_usuario(usuario_id: int, db: Session = Depends(get_db)):
    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    db.delete(usuario)
    db.commit()
    return {"message": "Usuario eliminado"}
