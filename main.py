from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import os
from datetime import datetime
from fastapi import FastAPI, Depends,WebSocket, WebSocketDisconnect
from sqlalchemy import or_, and_
from sqlalchemy.orm import Session
from database import get_db
from identities import User, UserCreate, Room, RoomCreate, RoomMembers, MessageCreate, Message, UserAuth, GroupMessagePayload


app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

connections = {}

@app.websocket("/ws/{room_id}/{username}")
async def websocket_endpoint(websocket: WebSocket, room_id: int, username: str):
    """
    Gerencia a conexão WebSocket para uma sala de chat específica.
    Aceita conexões, recebe mensagens e as retransmite para todos os clientes conectados na sala.
    
    Parâmetros:
        websocket (WebSocket): conexão WebSocket do cliente.
        room_id (int): ID da sala de chat.
        username (str): nome do usuário conectado.
    """
    await websocket.accept()
    # Adiciona o websocket à lista de conexões da sala
    if room_id not in connections:
        connections[room_id] = []
    connections[room_id].append(websocket)
    try:
        while True:
            data = await websocket.receive_json()
            # Envia a mensagem recebida para todos os clientes conectados na sala
            for conn in connections[room_id]:
                await conn.send_json({"sender": username, "content": data["content"]})
    except WebSocketDisconnect:
        # Remove o websocket da lista ao desconectar
        connections[room_id].remove(websocket)

@app.get("/")
def root():
    """
    Rota principal que retorna a página inicial do chat.
    """
    return FileResponse("static/index.html")

#------------------USERS--------------------------------------
@app.post("/users")
def createUser(user:UserCreate ,db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(
            (User.email == user.email) | (User.username == user.username)
        ).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email ou username já cadastrado")
    
    db_user = User(
        name=user.name,
        username=user.username,
        email=user.email,
        password=user.password, # salva senha em hash
        role='user'
    )

    db.add(db_user)
    db.commit()
    return {"message": f"Usuário {db_user.username} criado com sucesso!"}

@app.post("/users/login")
def user_auth(user: UserAuth, db: Session = Depends(get_db)):
    """
    Autentica um usuário pelo email ou username e senha.
    
    Parâmetros:
        user (UserAuth): dados de autenticação (email/username e senha).
        db (Session): sessão do banco de dados.
    
    Retorna:
        dict: mensagem de sucesso e dados do usuário autenticado.
    """
    check_user = db.query(User).filter(
        or_(
            User.username == user.emailUsername,
            User.email == user.emailUsername
        ),
        User.password == user.password
    ).first()
    if not check_user:
        raise HTTPException(status_code=401, detail="Usuário ou senha inválidos")
    return {
        "message": f"Usuário {check_user.username} autenticado com sucesso", 
        "userId": check_user.id,
        "username": check_user.username
    }
      
@app.get("/Allusers")
def get_all_users(db: Session = Depends(get_db)):
    """
    Retorna todos os usuários cadastrados no sistema.
    
    Parâmetros:
        db (Session): sessão do banco de dados.
    
    Retorna:
        list: lista de usuários.
    """
    users = db.query(User).all()
    return users

@app.get("/users/{userId}")
def getUser(userId: int, db: Session = Depends(get_db)):
    """
    Retorna os dados de um usuário específico pelo ID.
    
    Parâmetros:
        userId (int): ID do usuário.
        db (Session): sessão do banco de dados.
    
    Retorna:
        User ou dict: usuário encontrado ou erro.
    """
    user = db.query(User).filter((User.id == userId)).first()
    if not user:
        return {"error": "Usuário não encontrado"}
    return user

@app.get("/users/{userId}/privates")
def getPrivates(userId: int, db: Session = Depends(get_db)):
    """
    Retorna os dados privados de um usuário específico pelo ID.
    (Atualmente retorna o próprio usuário, pode ser expandido para privacidades.)
    
    Parâmetros:
        userId (int): ID do usuário.
        db (Session): sessão do banco de dados.
    
    Retorna:
        User ou dict: usuário encontrado ou erro.
    """
    user = db.query(User).filter((User.id == userId)).first()
    if not user:
        return {"error": "Usuário não encontrado"}
    return user

#------------------ROOMS--------------------------------------
@app.post("/rooms")
def createRoom(room: RoomCreate, db: Session = Depends(get_db)):
    """
    Cria uma nova sala de chat.
    Verifica se já existe uma sala com o mesmo nome.
    
    Parâmetros:
        room (RoomCreate): dados da sala a ser criada.
        db (Session): sessão do banco de dados.
    
    Retorna:
        Room: objeto da sala criada.
    """
    existing_room = db.query(Room).filter(
        (Room.name == room.name)
    ).first()
    if existing_room:
        raise HTTPException(status_code=400, detail="Sala já cadastrada")
    db_room = Room(
        name=room.name,
        description=room.description,
        members=room.members,
        is_private=room.is_private
    )
    db.add(db_room)
    db.commit()
    db.refresh(db_room)  # retorna o objeto atualizado com ID
    return db_room

@app.delete("/rooms/{roomId}")
def func():
    """
    Remove uma sala (apenas pelo dono ou administrador).
    (Função placeholder, implementar lógica de remoção real.)
    """
    output = " Remove uma sala (apenas pelo dono ou administrador)."
    return output

@app.post("/rooms/{roomId}/enter")
def joinRoom(roomId: int, userId: int, db: Session = Depends(get_db)):
    """
    Adiciona um usuário a uma sala de chat.
    Verifica se o usuário e a sala existem e se o usuário já não está na sala.
    
    Parâmetros:
        roomId (int): ID da sala.
        userId (int): ID do usuário.
        db (Session): sessão do banco de dados.
    
    Retorna:
        RoomMembers: objeto de associação criado.
    """
    room = db.query(Room).filter(Room.id == roomId).first()
    user = db.query(User).filter(User.id == userId).first()
    members = db.query(RoomMembers).filter(RoomMembers.room_id == roomId, RoomMembers.user_id == userId).first()
    if not room:
        raise HTTPException(status_code=404, detail="Sala não encontrada")
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    if members:
        raise HTTPException(status_code=400, detail="Usuário já está na sala")
    db_members = RoomMembers(
        user_id=userId,
        room_id=roomId
    )
    db.add(db_members)
    db.commit()
    db.refresh(db_members)  # retorna o objeto atualizado com ID
    return db_members
    

@app.post("/rooms/{roomId}/leave")
def leaveRoom(roomId: int, userId: int, db: Session = Depends(get_db)):
    """
    Remove um usuário de uma sala de chat.
    Verifica se o usuário e a sala existem e se o usuário faz parte da sala.
    
    Parâmetros:
        roomId (int): ID da sala.
        userId (int): ID do usuário.
        db (Session): sessão do banco de dados.
    
    Retorna:
        dict: mensagem de sucesso.
    """
    room = db.query(Room).filter(Room.id == roomId).first()
    user = db.query(User).filter(User.id == userId).first()
    members = db.query(RoomMembers).filter(RoomMembers.room_id == roomId, RoomMembers.user_id == userId).first()
    if not room:
        raise HTTPException(status_code=404, detail="Sala não encontrada")
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    if not members:
        raise HTTPException(status_code=400, detail="Usuário não faz parte desta sala")
    db.delete(members)
    db.commit()
    return {"message": f"Usuário {userId} saiu da sala {roomId}"}


# Adm está se removendo aqui. Precisa implementar a validação JWT/OAuth antes dessa parte
@app.delete("/rooms/{roomId}/users/{userId}")
def adminRemove(roomId: int, userId: int, db: Session = Depends(get_db)):
    """
    Remove um usuário de uma sala, apenas se o solicitante for administrador.
    Verifica se o usuário é admin, se a sala existe e se o usuário faz parte da sala.
    
    Parâmetros:
        roomId (int): ID da sala.
        userId (int): ID do usuário a ser removido.
        db (Session): sessão do banco de dados.
    
    Retorna:
        dict: mensagem de sucesso.
    """
    user = db.query(User).filter(User.id == userId, User.role == 'admin').first()
    room = db.query(Room).filter(Room.id == roomId).first()
    members = db.query(RoomMembers).filter(RoomMembers.room_id == roomId, RoomMembers.user_id == userId).first()
    if not user:
        raise HTTPException(status_code=404, detail='Você não pode executar esta ação pois não é administrador')
    if not room:
        raise HTTPException(status_code=404, detail="Sala não encontrada")
    if not members:
        raise HTTPException(status_code=400, detail="Usuário não faz parte desta sala")
    db.delete(members)
    db.commit()
    return {"message": f"Usuário {userId} foi removido da sala {roomId}"}

@app.get("/rooms/{userId}")
def get_rooms(userId: int, db:Session = Depends(get_db) ):
    rooms = db.query(Room).join(RoomMembers, Room.id == RoomMembers.room_id).filter(RoomMembers.user_id == userId).all()
    return rooms

#----------------MESSAGES-----------------------------------
@app.post("/messages/direct/{receiverId}")
def direct(senderId: int, receiverId: int, content: str, db: Session = Depends(get_db)):
    """
    Envia uma mensagem direta entre dois usuários, desde que compartilhem uma sala privada.
    
    Parâmetros:
        senderId (int): ID do remetente.
        receiverId (int): ID do destinatário.
        content (str): conteúdo da mensagem.
        db (Session): sessão do banco de dados.
    
    Retorna:
        dict: mensagem de sucesso e ID da sala privada.
    """
    # Verifica se o destinatário existe
    receiver = db.query(User).filter(User.id == receiverId).first()
    if not receiver:
        raise HTTPException(status_code=404, detail="Usuário destinatário não encontrado")
    # Busca salas em que o remetente participa
    sender_rooms = db.query(RoomMembers.room_id).filter(RoomMembers.user_id == senderId).all()
    # Busca salas em que o destinatário participa
    receiver_rooms = db.query(RoomMembers.room_id).filter(RoomMembers.user_id == receiverId).all()
    # Extrai apenas os IDs das salas
    s_rooms = [s.room_id for s in sender_rooms]
    r_rooms = [r.room_id for r in receiver_rooms]
    # Interseção — salas em comum
    comum = list(set(s_rooms) & set(r_rooms))
    if not comum:
        raise HTTPException(status_code=400, detail="Usuários não compartilham nenhuma sala")
    # Agora verifica se há pelo menos uma sala privada entre eles
    private_room = db.query(Room).filter(
        Room.id.in_(comum),
        Room.is_private == True
    ).first()
    if not private_room:
        raise HTTPException(status_code=403, detail="Nenhuma sala privada encontrada entre os usuários")
    # Cria a mensagem
    now = datetime.now()
    message = Message(
        room_id=private_room.id,
        sender_id=senderId,
        receiver_id=receiverId,
        content=content,
        created_at=now
    )
    db.add(message)
    db.commit()
    return {
        "message": f"Mensagem '{content}' enviada de {senderId} para {receiverId}",
        "room_id": private_room.id
    }

@app.post("/rooms/{roomId}/messages")
def groupMessage(roomId: int, payload: GroupMessagePayload, db: Session = Depends(get_db)):
    """
    Envia uma mensagem para todos os membros de uma sala de chat.
    Verifica se o usuário faz parte da sala antes de enviar.
    
    Parâmetros:
        roomId (int): ID da sala (do caminho da URL).
        payload (GroupMessagePayload): Dados da mensagem (do corpo da requisição).
        db (Session): sessão do banco de dados.
    
    Retorna:
        dict: mensagem de sucesso e ID da mensagem criada.
    """
    room = db.query(Room).filter(Room.id == roomId).first()
    if not room:
        raise HTTPException(status_code=404, detail="Sala não encontrada")

    # Os dados agora são extraídos do objeto payload
    membership = db.query(RoomMembers).filter(
        RoomMembers.room_id == roomId,
        RoomMembers.user_id == payload.senderId
    ).first()
    if not membership:
        raise HTTPException(status_code=403, detail="Usuário não faz parte desta sala")
    
    # Criar mensagem
    message = Message(
        room_id=roomId,
        sender_id=payload.senderId,
        receiver_id=None,
        content=payload.content,
        created_at=datetime.now()
    )
    db.add(message)
    db.commit()
    db.refresh(message)
    return {"message": f"Mensagem enviada para sala {roomId}", "message_id": message.id}

    
@app.get("/rooms/{roomId}/messages")
def getMessages(roomId: int, db: Session = Depends(get_db)):
    """
    Retorna todas as mensagens de uma sala específica.
    
    Parâmetros:
        roomId (int): ID da sala.
        db (Session): sessão do banco de dados.
    
    Retorna:
        list: lista de mensagens da sala.
    """
    messages = db.query(Message).filter(Message.room_id == roomId).all()
    return messages




