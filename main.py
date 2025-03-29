from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import Column, Integer, String
from database import SessionLocal, engine
from models import Base, Usuario
from pydantic import BaseModel
from passlib.context import CryptContext
from datetime import datetime, timedelta
import jwt
from fastapi.middleware.cors import CORSMiddleware


# Secret key for JWT
SECRET_KEY = "mysecretkey"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Crear las tablas en la base de datos
Base.metadata.create_all(bind=engine)

app = FastAPI()

# Allow all origins (you can limit this to specific domains for more security)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://main.d287jeeuebb05f.amplifyapp.com"],  # Or specify your frontend URL, e.g., ["https://main.d287jeeuebb05f.amplifyapp.com"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# Dependencia para obtener la sesión de la base de datos
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Definición del modelo para la respuesta de la API
class UsuarioResponse(BaseModel):
    id: int
    nombre: str
    email: str
    lastname: str

    class Config:
        orm_mode = True

# Pydantic model para la creación de un nuevo usuario
class UsuarioCreate(BaseModel):
    nombre: str
    email: str
    lastname: str
    password: str

# Pydantic model para la autenticación
class UsuarioLogin(BaseModel):
    email: str
    password: str

# Definición del modelo para el token
class Token(BaseModel):
    access_token: str
    token_type: str

# Crear una instancia del contexto de la contraseña
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Función para verificar la contraseña
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

# Función para hashear la contraseña
def get_password_hash(password):
    return pwd_context.hash(password)

# Función para crear el JWT
def create_access_token(data: dict, expires_delta: timedelta = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)):
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# ✔️ Obtener todos los usuarios
@app.get("/usuarios", response_model=list[UsuarioResponse])
def get_usuarios(db: Session = Depends(get_db)):
    usuarios = db.query(Usuario).all()
    return usuarios

# ✔️ Crear un nuevo usuario
@app.post("/usuarios", response_model=UsuarioResponse)
def create_usuario(usuario: UsuarioCreate, db: Session = Depends(get_db)):
    # Verificar si el usuario ya existe
    db_usuario = db.query(Usuario).filter(Usuario.email == usuario.email).first()
    if db_usuario:
        raise HTTPException(status_code=400, detail="El usuario ya existe")
    
    # Crear el nuevo usuario
    hashed_password = get_password_hash(usuario.password)
    db_usuario = Usuario(nombre=usuario.nombre, email=usuario.email, lastname=usuario.lastname, password=hashed_password)
    
    db.add(db_usuario)
    db.commit()
    db.refresh(db_usuario)
    return db_usuario

# ✔️ Login de usuario y generar token JWT
@app.post("/login", response_model=Token)
def login(usuario: UsuarioLogin, db: Session = Depends(get_db)):
    db_usuario = db.query(Usuario).filter(Usuario.email == usuario.email).first()
    if not db_usuario or not verify_password(usuario.password, db_usuario.password):
        raise HTTPException(status_code=401, detail="Credenciales inválidas")
    
    # Crear el token
    access_token = create_access_token(data={"sub": db_usuario.email})
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
def update_usuario(usuario_id: int, usuario: UsuarioCreate, db: Session = Depends(get_db)):
    db_usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if not db_usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    db_usuario.nombre = usuario.nombre
    db_usuario.email = usuario.email
    db_usuario.lastname = usuario.lastname
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
