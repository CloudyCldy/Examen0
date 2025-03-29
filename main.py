from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import Column, Integer, String
from database import SessionLocal, engine
from models import Base, Usuario
from pydantic import BaseModel
from datetime import datetime, timedelta
import jwt

# Secret key for JWT
SECRET_KEY = "kuromi"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Crear las tablas en la base de datos
Base.metadata.create_all(bind=engine)

app = FastAPI()

# ✅ Agregar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permite todas las solicitudes (ajusta esto en producción)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# Dependencia para obtener la sesión de la base de datos
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Modelos Pydantic actualizados
class UsuarioResponse(BaseModel):
    id: int
    nombre: str
    email: str
    apellido: str

    class Config:
        orm_mode = True

class UsuarioCreate(BaseModel):
    nombre: str
    email: str
    apellido: str  # Ahora usamos apellido como credencial

class UsuarioUpdate(BaseModel):
    nombre: str
    email: str
    apellido: str

    class Config:
        orm_mode = True

class UsuarioLogin(BaseModel):
    email: str
    apellido: str  # Validamos con apellido en lugar de password

class Token(BaseModel):
    access_token: str
    token_type: str

# Función para crear el JWT
def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# ✔️ Obtener todos los usuarios
@app.get("/usuarios", response_model=list[UsuarioResponse])
def get_usuarios(db: Session = Depends(get_db)):
    usuarios = db.query(Usuario).all()
    return usuarios

# ✔️ Crear un nuevo usuario (sin contraseña, usando apellido)
@app.post("/usuarios", response_model=UsuarioResponse)
def create_usuario(usuario: UsuarioCreate, db: Session = Depends(get_db)):
    # Verificar si el usuario ya existe
    db_usuario = db.query(Usuario).filter(Usuario.email == usuario.email).first()
    if db_usuario:
        raise HTTPException(status_code=400, detail="El usuario ya existe")
    
    # Crear el nuevo usuario con apellido como credencial
    db_usuario = Usuario(
        nombre=usuario.nombre,
        email=usuario.email,
        apellido=usuario.apellido  # No usamos password
    )
    
    db.add(db_usuario)
    db.commit()
    db.refresh(db_usuario)
    return db_usuario

# ✔️ Login de usuario validando con apellido
@app.post("/login", response_model=Token)
def login(usuario: UsuarioLogin, db: Session = Depends(get_db)):
    db_usuario = db.query(Usuario).filter(Usuario.email == usuario.email).first()
    
    # Validar que el usuario existe y el apellido coincide
    if not db_usuario or db_usuario.apellido != usuario.apellido:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales inválidas",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Crear el token JWT
    access_token = create_access_token(
        data={"sub": db_usuario.email},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

# ✔️ Obtener un usuario por ID
@app.get("/usuarios/{usuario_id}", response_model=UsuarioResponse)
def get_usuario(usuario_id: int, db: Session = Depends(get_db)):
    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return usuario

# ✔️ Actualizar un usuario
@app.put("/usuarios/{usuario_id}", response_model=UsuarioResponse)
def update_usuario(usuario_id: int, usuario: UsuarioUpdate, db: Session = Depends(get_db)):
    db_usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if not db_usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    db_usuario.nombre = usuario.nombre
    db_usuario.email = usuario.email
    db_usuario.apellido = usuario.apellido

    db.commit()
    db.refresh(db_usuario)
    return db_usuario

# ✔️ Eliminar un usuario
@app.delete("/usuarios/{usuario_id}", response_model=dict)
def delete_usuario(usuario_id: int, db: Session = Depends(get_db)):
    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    db.delete(usuario)
    db.commit()
    return {"message": "Usuario eliminado"}
