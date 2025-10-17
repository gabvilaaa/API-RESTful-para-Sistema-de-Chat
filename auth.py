# auth.py

from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext

# 1. Configuração de Segurança
# Para gerar uma chave secreta forte, você pode executar no seu terminal:
# openssl rand -hex 32
SECRET_KEY = "sua_chave_secreta_super_forte_de_32_bytes_aqui"  # SUBSTITUA PELA SUA CHAVE
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Contexto do Passlib para hashing de senhas
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# 2. Funções para Senha
def verify_password(plain_password: str, hashed_password ) -> bool:
    """Verifica se a senha fornecida corresponde ao hash armazenado."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Gera o hash de uma senha."""
    return pwd_context.hash(password)


# 3. Função para Criar o Token JWT
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """
    Cria um novo token de acesso JWT.
    
    Args:
        data (dict): Os dados a serem incluídos no payload do token (o "corpo").
        expires_delta (Optional[timedelta]): Duração de validade do token.
    
    Returns:
        str: O token JWT codificado.
    """
    to_encode = data.copy()
    
    # Define o tempo de expiração
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        # Padrão de 30 minutos se não for fornecido
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
    to_encode.update({"exp": expire})
    
    # Gera o token JWT
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt